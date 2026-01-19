import statistics
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import pytesseract
from pytesseract import TesseractNotFoundError

from app.services.cleaning import (
    float_value,
    int_value,
    money_float,
    normalize_header_text,
    normalize_key,
    percent_float,
    ratio_float,
)
from app.services.parsers.base import ParsedTable, Token, group_tokens_by_row
from app.services.parsers.generic import GenericParser
from app.services.parsers.marketchameleon_notional import MarketChameleonNotionalParser
from app.services.parsers.marketchameleon_volume import MarketChameleonVolumeParser
from app.services.parsers.marketchameleon_volatility import MarketChameleonVolatilityParser

HEADER_ALIAS_MAP = {
    "Relative Volume to 90-Day Avg": "RelVolTo90D",
    "Call Volume": "CallVolume",
    "Put Volume": "PutVolume",
    "Put %": "PutPct",
    "% Single-Leg": "SingleLegPct",
    "% Multi Leg": "MultiLegPct",
    "% Contingent": "ContingentPct",
    "Relative Notional to 90-Day Avg": "RelNotionalTo90D",
    "Call $ Notional": "CallNotional",
    "Put $ Notional": "PutNotional",
    "Symbol": "symbol",
    "Volatility % Chg": "IV30ChgPct",
    "Current IV30": "IV30",
    "20-Day Historical Vol": "HV20",
    "1-Year Historical Vol": "HV1Y",
    "IV30 % Rank": "IVR",
    "IV30 52-Week Position": "IV_52W_P",
    "Current Option Volume": "Volume",
    "Open Interest % Rank": "OI_PctRank",
    "Earnings": "Earnings",
    "% Chg": "PriceChgPct",
}

FIELD_TYPES = {
    "price": "float",
    "stock_price": "float",
    "market_cap": "money",
    "PriceChgPct": "percent",
    "trade_count": "int",
    "total_notional": "money",
    "avg90_notional": "money",
    "RelNotionalTo90D": "ratio",
    "CallNotional": "money",
    "PutNotional": "money",
    "SingleLegPct": "percent",
    "MultiLegPct": "percent",
    "ContingentPct": "percent",
    "total_volume": "int",
    "avg90_volume": "int",
    "RelVolTo90D": "ratio",
    "CallVolume": "int",
    "PutVolume": "int",
    "PutPct": "percent",
    "IV30": "float",
    "IV30ChgPct": "percent",
    "HV20": "float",
    "HV1Y": "float",
    "IVR": "percent",
    "IV_52W_P": "percent",
    "Volume": "int",
    "OI_PctRank": "percent",
}


class ParserRegistry:
    def __init__(self) -> None:
        self.parsers = {
            "generic": GenericParser(),
            "mc_notional": MarketChameleonNotionalParser(),
            "mc_volume": MarketChameleonVolumeParser(),
            "mc_volatility": MarketChameleonVolatilityParser(),
        }

    def detect(self, header_text: str) -> str:
        normalized = normalize_header_text(header_text)
        keywords = {
            "mc_notional": [
                "total $ notional",
                "call $ notional",
                "put $ notional",
                "90 day avg $ notional",
                "relative notional to 90 day avg",
            ],
            "mc_volume": [
                "total volume",
                "call volume",
                "put volume",
                "90 day avg volume",
                "relative volume to 90 day avg",
                "put %",
            ],
            "mc_volatility": [
                "current iv30",
                "20 day historical vol",
                "1 year historical vol",
                "iv30 % rank",
                "iv30 52 week position",
                "open interest % rank",
                "current option volume",
            ],
        }
        for parser_name, phrases in keywords.items():
            hits = sum(1 for phrase in phrases if phrase in normalized)
            if hits >= 2:
                return parser_name
        return "generic"

    def get(self, name: str):
        return self.parsers.get(name, self.parsers["generic"])


registry = ParserRegistry()


def preprocess_image(image: np.ndarray) -> np.ndarray:
    resized = cv2.resize(image, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    equalized = clahe.apply(gray)
    denoised = cv2.fastNlMeansDenoising(equalized, None, 10, 7, 21)
    thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2
    )
    return thresh


def tokens_from_image(image: np.ndarray) -> List[Token]:
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    tokens: List[Token] = []
    for idx, text in enumerate(data["text"]):
        conf = int(float(data["conf"][idx])) if data["conf"][idx] != "-1" else -1
        cleaned = text.strip()
        if not cleaned:
            continue
        if len(cleaned) == 1 and cleaned in {"i", "•", "|", "▲", "▼"} and conf < 60:
            continue
        tokens.append(
            Token(
                text=cleaned,
                left=int(data["left"][idx]),
                top=int(data["top"][idx]),
                width=int(data["width"][idx]),
                height=int(data["height"][idx]),
                conf=conf,
            )
        )
    return tokens


def split_header_body(tokens: List[Token], image_height: int) -> Tuple[List[Token], List[Token]]:
    header_limit = image_height * 0.35
    header_tokens = [token for token in tokens if token.top <= header_limit]
    body_tokens = [token for token in tokens if token.top > header_limit]
    return header_tokens, body_tokens


def merge_header_text(tokens: List[Token]) -> str:
    return " ".join(token.text for token in sorted(tokens, key=lambda t: t.left))


def build_column_boundaries(
    header_tokens: List[Token], expected_headers: List[str]
) -> Tuple[List[str], List[float], List[str]]:
    warnings: List[str] = []
    matched = []
    for label in expected_headers:
        bbox = match_header_bbox(header_tokens, label)
        if bbox:
            matched.append((label, bbox))
        else:
            warnings.append(f"Header column not found: {label}")
    matched_sorted = sorted(matched, key=lambda item: item[1][0])
    if not matched_sorted:
        return [], [], warnings
    boundaries = [-10**9]
    columns = [label for label, _ in matched_sorted]
    for idx in range(1, len(matched_sorted)):
        prev_right = matched_sorted[idx - 1][1][1]
        next_left = matched_sorted[idx][1][0]
        boundaries.append((prev_right + next_left) / 2)
    boundaries.append(10**9)
    return columns, boundaries, warnings


def match_header_bbox(tokens: List[Token], label: str) -> Optional[Tuple[int, int]]:
    label_words = normalize_key(label).split()
    if not label_words:
        return None
    rows = group_tokens_by_row(tokens)
    for row in rows:
        words = [normalize_key(token.text) for token in row]
        for idx in range(len(words)):
            if words[idx : idx + len(label_words)] == label_words:
                matched = row[idx : idx + len(label_words)]
                left = min(t.left for t in matched)
                right = max(t.right for t in matched)
                return (left, right)
    return None


def resolve_alias(label: str) -> str:
    normalized_label = normalize_key(label)
    for raw, mapped in HEADER_ALIAS_MAP.items():
        if normalize_key(raw) == normalized_label:
            return mapped
    return label


def clean_value(column: str, value: str):
    field_type = FIELD_TYPES.get(column)
    if field_type == "percent":
        return percent_float(value)
    if field_type == "money":
        return money_float(value)
    if field_type == "int":
        return int_value(value)
    if field_type == "float":
        return float_value(value)
    if field_type == "ratio":
        return ratio_float(value)
    return value


def parse_market_chameleon(
    parser_name: str,
    header_tokens: List[Token],
    body_tokens: List[Token],
) -> ParsedTable:
    parser = registry.get(parser_name)
    warnings: List[str] = []
    columns_labels, boundaries, header_warnings = build_column_boundaries(
        header_tokens, list(parser.expected_headers)
    )
    warnings.extend(header_warnings)
    if len(columns_labels) < max(1, int(0.6 * len(parser.expected_headers))):
        return ParsedTable(
            ok=False,
            parser=parser_name,
            columns=list(parser.column_order),
            rows=[],
            cell_conf=[],
            warnings=[
                "Unable to match enough header columns. Try cropping the table region or switching parser."
            ],
        )
    column_map = {}
    for label in columns_labels:
        column_map[label] = resolve_alias(label)
    rows_grouped = group_tokens_by_row(body_tokens)
    parsed_rows = []
    cell_conf = []
    for row in rows_grouped:
        row_cells = {col: None for col in parser.column_order}
        row_conf = [-1 for _ in parser.column_order]
        for idx, label in enumerate(columns_labels):
            col_name = column_map.get(label, label)
            if col_name not in row_cells:
                continue
            tokens_in_col = [
                token
                for token in row
                if boundaries[idx] <= token.x_center < boundaries[idx + 1]
            ]
            if tokens_in_col:
                tokens_in_col = sorted(tokens_in_col, key=lambda t: t.left)
                raw_text = " ".join(t.text for t in tokens_in_col)
                cleaned = clean_value(col_name, raw_text)
                row_cells[col_name] = cleaned
                row_conf[parser.column_order.index(col_name)] = int(
                    sum(t.conf for t in tokens_in_col) / len(tokens_in_col)
                )
        valid_cells = sum(1 for value in row_cells.values() if value not in (None, ""))
        if valid_cells < max(1, int(0.7 * len(columns_labels))):
            warnings.append("Skipped a row with too few populated cells.")
            continue
        parsed_rows.append(row_cells)
        cell_conf.append(row_conf)
    return ParsedTable(
        ok=True,
        parser=parser_name,
        columns=list(parser.column_order),
        rows=parsed_rows,
        cell_conf=cell_conf,
        warnings=warnings,
    )


def parse_image(file_bytes: bytes, parser_choice: str) -> ParsedTable:
    try:
        image_array = np.frombuffer(file_bytes, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if image is None:
            return ParsedTable(
                ok=False,
                parser=parser_choice,
                columns=[],
                rows=[],
                cell_conf=[],
                warnings=["Unable to decode image file."],
            )
        processed = preprocess_image(image)
        tokens = tokens_from_image(processed)
        header_tokens, body_tokens = split_header_body(tokens, processed.shape[0])
        header_text = merge_header_text(header_tokens)
        parser_name = parser_choice
        if parser_choice == "auto":
            parser_name = registry.detect(header_text)
        if parser_name in {"mc_notional", "mc_volume", "mc_volatility"}:
            return parse_market_chameleon(parser_name, header_tokens, body_tokens)
        parser = registry.get(parser_name)
        return parser.parse(header_tokens, body_tokens)
    except TesseractNotFoundError:
        return ParsedTable(
            ok=False,
            parser=parser_choice,
            columns=[],
            rows=[],
            cell_conf=[],
            warnings=[
                "Tesseract OCR not found. Please install Tesseract (see README) and restart the backend."
            ],
        )
    except Exception as exc:  # pragma: no cover - safety
        return ParsedTable(
            ok=False,
            parser=parser_choice,
            columns=[],
            rows=[],
            cell_conf=[],
            warnings=[f"Unexpected error during OCR: {exc}"],
        )


def create_parse_response(file_bytes: bytes, parser_choice: str) -> Dict:
    parsed = parse_image(file_bytes, parser_choice)
    parse_id = str(uuid.uuid4())
    return {
        "ok": parsed.ok,
        "parser": parsed.parser,
        "columns": parsed.columns,
        "rows": parsed.rows,
        "cell_conf": parsed.cell_conf,
        "warnings": parsed.warnings,
        "parse_id": parse_id,
        "created_at": datetime.utcnow().isoformat(),
    }
