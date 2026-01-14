from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from app.services.cleaning import normalize_header_text


@dataclass
class Token:
    text: str
    left: int
    top: int
    width: int
    height: int
    conf: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def x_center(self) -> float:
        return self.left + self.width / 2


@dataclass
class ParsedTable:
    ok: bool
    parser: str
    columns: List[str]
    rows: List[dict]
    cell_conf: List[List[int]]
    warnings: List[str]


class BaseParser:
    name = "generic"
    expected_headers: Sequence[str] = []
    column_order: Sequence[str] = []
    column_types: Dict[str, str] = {}
    header_alias_map: Dict[str, str] = {}

    def detect(self, header_text: str) -> bool:
        return False

    def normalize_header(self, text: str) -> str:
        return normalize_header_text(text)

    def match_header_bbox(self, tokens: List[Token], label: str) -> Optional[tuple]:
        label_words = self.normalize_header(label).split()
        if not label_words:
            return None
        rows = group_tokens_by_row(tokens)
        for row in rows:
            words = [self.normalize_header(token.text) for token in row]
            for idx in range(len(words)):
                if words[idx : idx + len(label_words)] == label_words:
                    matched = row[idx : idx + len(label_words)]
                    left = min(t.left for t in matched)
                    right = max(t.right for t in matched)
                    return (left, right)
        return None



def group_tokens_by_row(tokens: List[Token]) -> List[List[Token]]:
    if not tokens:
        return []
    tokens_sorted = sorted(tokens, key=lambda t: t.top)
    heights = [t.height for t in tokens_sorted]
    median_height = sorted(heights)[len(heights) // 2]
    row_tol = median_height * 0.8
    rows: List[List[Token]] = []
    current_row: List[Token] = []
    current_y = tokens_sorted[0].top
    for token in tokens_sorted:
        if abs(token.top - current_y) <= row_tol:
            current_row.append(token)
        else:
            rows.append(sorted(current_row, key=lambda t: t.left))
            current_row = [token]
            current_y = token.top
    if current_row:
        rows.append(sorted(current_row, key=lambda t: t.left))
    return rows
