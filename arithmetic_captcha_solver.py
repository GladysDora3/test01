import re
from typing import Optional, Tuple, Union

Number = Union[int, float]

_OCR_TRANSLATION = str.maketrans({
    "o": "0",
    "O": "0",
    "〇": "0",
    "×": "*",
    "x": "*",
    "X": "*",
    "÷": "/",
    "？": "?",
    "＝": "=",
    "—": "-",
    "–": "-",
    "_": "-",
})

_EXPR_PATTERN = re.compile(r"(\d{1,2})([+\-*/])(\d{1,2})")


def normalize_ocr_text(raw_text: str) -> str:
    text = (raw_text or "").translate(_OCR_TRANSLATION)
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[^0-9+\-*/=?]", "", text)
    return text


def _strip_trailing_suffix(text: str) -> str:
    return re.sub(r"(?:=\?|\?)$", "", text)


def _repair_merged_first_operand(expression: str) -> str:
    match = re.fullmatch(r"(\d{2})([+\-*/])(\d)", expression)
    if not match:
        return expression

    first, op, second = match.groups()
    if first[1] == second[0]:
        return f"{first[0]}{op}{second}"

    return expression


def extract_expression(raw_text: str) -> Optional[Tuple[int, str, int]]:
    normalized = normalize_ocr_text(raw_text)
    candidate_source = _strip_trailing_suffix(normalized)

    match = _EXPR_PATTERN.search(candidate_source)
    if not match:
        return None

    expression = _repair_merged_first_operand(match.group(0))
    repaired = re.fullmatch(r"(\d{1,2})([+\-*/])(\d{1,2})", expression)
    if not repaired:
        return None

    a, op, b = repaired.groups()
    return int(a), op, int(b)


def solve_arithmetic_captcha(raw_text: str) -> Optional[Number]:
    parsed = extract_expression(raw_text)
    if not parsed:
        return None

    a, op, b = parsed
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        if b == 0:
            return None
        if a % b == 0:
            return a // b
        return a / b
    return None
