import re
from typing import Optional, Tuple


def _strip_noise(value: str) -> str:
    return value.replace("=", "").strip()


def percent_float(value: str) -> Optional[float]:
    cleaned = _strip_noise(value).replace("%", "")
    if cleaned in {"", "-", "--"}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def ratio_float(value: str) -> Optional[float]:
    if "%" in value:
        return percent_float(value)
    return float_value(value)


def money_float(value: str) -> Optional[float]:
    cleaned = _strip_noise(value).replace("$", "").replace(",", "")
    if cleaned in {"", "-", "--"}:
        return None
    multiplier = 1.0
    suffix = cleaned[-1].upper()
    if suffix in {"K", "M", "B", "T"}:
        cleaned = cleaned[:-1]
        multiplier = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}[suffix]
    try:
        return float(cleaned) * multiplier
    except ValueError:
        return None


def int_value(value: str) -> Optional[int]:
    cleaned = _strip_noise(value).replace(",", "")
    if cleaned in {"", "-", "--"}:
        return None
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def float_value(value: str) -> Optional[float]:
    cleaned = _strip_noise(value).replace(",", "")
    if cleaned in {"", "-", "--"}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_key(value: str) -> str:
    if not value:
        return ""
    cleaned = value.lower()
    cleaned = cleaned.replace("$", " $")
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.replace("-", " ")
    cleaned = cleaned.replace("$ ", "$")
    cleaned = cleaned.replace(" $", "$")
    cleaned = cleaned.replace("contigent", "contingent")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def normalize_header_text(value: str) -> str:
    return normalize_key(value)


def match_header_alias(
    header_alias_map: dict, raw_key: str
) -> Tuple[Optional[str], Optional[str]]:
    normalized = normalize_key(raw_key)
    for k, v in header_alias_map.items():
        if normalize_key(k) == normalized:
            return v, normalized
    return None, normalized
