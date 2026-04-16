#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None

try:
    import ddddocr  # type: ignore
except Exception:  # pragma: no cover
    ddddocr = None


@dataclass
class SolveResult:
    ok: bool
    raw_ocr: str
    normalized_text: str
    parsed_expr: Optional[str]
    answer: Optional[float]
    reason: str


class CaptchaMathSolver:
    _EXPR_PATTERN = re.compile(r"(\d{1,2})([+\-*/])(\d{1,2})")

    def __init__(self) -> None:
        self._ocr = None

    def solve_image(self, image_path: str) -> SolveResult:
        if cv2 is None:
            return SolveResult(False, "", "", None, None, "opencv-python is not installed")
        if ddddocr is None:
            return SolveResult(False, "", "", None, None, "ddddocr is not installed")

        image = cv2.imread(image_path)
        if image is None:
            return SolveResult(False, "", "", None, None, f"cannot read image: {image_path}")

        if self._ocr is None:
            self._ocr = ddddocr.DdddOcr(show_ad=False)

        candidates = []
        for variant in self._preprocess_variants(image):
            ok, buffer = cv2.imencode(".png", variant)
            if not ok:
                continue
            raw = (self._ocr.classification(buffer.tobytes()) or "").strip()
            if not raw:
                continue
            parsed = self.solve_text(raw)
            score = self._score_candidate(raw, parsed)
            candidates.append((score, parsed))

        if not candidates:
            return SolveResult(False, "", "", None, None, "OCR produced no text")

        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    def solve_text(self, raw_text: str) -> SolveResult:
        normalized = normalize_text(raw_text)
        parsed_expr = extract_expression(normalized, original_text=raw_text)
        if parsed_expr is None:
            return SolveResult(False, raw_text, normalized, None, None, "no valid expression found")
        answer, reason = safe_evaluate(parsed_expr)
        if reason:
            return SolveResult(False, raw_text, normalized, parsed_expr, None, reason)
        return SolveResult(True, raw_text, normalized, parsed_expr, answer, "")

    @staticmethod
    def _preprocess_variants(image) -> List:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        variants = [gray]

        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants.append(otsu)

        _, otsu_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        variants.append(otsu_inv)

        adaptive = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2,
        )
        variants.append(adaptive)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        opened = cv2.morphologyEx(otsu, cv2.MORPH_OPEN, kernel)
        variants.append(opened)

        dilated = cv2.dilate(otsu, kernel, iterations=1)
        variants.append(dilated)
        return variants

    @staticmethod
    def _score_candidate(raw_text: str, result: SolveResult) -> int:
        score = 0
        if result.parsed_expr:
            score += 100
        if result.ok:
            score += 50
        if "=" in raw_text or "?" in raw_text or "？" in raw_text:
            score += 5
        score -= max(0, len(result.normalized_text) - 6)
        return score


def normalize_text(raw_text: str) -> str:
    translated = []
    translation = {
        "o": "0",
        "O": "0",
        "〇": "0",
        "零": "0",
        "x": "*",
        "X": "*",
        "×": "*",
        "÷": "/",
        "—": "-",
        "–": "-",
        "_": "-",
        "？": "?",
        "＝": "=",
    }
    for ch in raw_text.strip():
        translated.append(translation.get(ch, ch))
    text = "".join(translated).replace(" ", "")

    text = re.sub(r"(?:=\?|\?)$", "", text)
    text = re.sub(r"[^0-9+\-*/]", "", text)
    return text


def _repair_merged_left_operand(expr: str, original_text: str = "") -> str:
    match = re.fullmatch(r"(\d)(\d)([+\-*/])(\d)", expr)
    if not match:
        return expr
    first_digit, second_digit, op, right_digit = match.groups()
    has_explicit_suffix = bool(re.search(r"(=\?)|[?？]", original_text))
    if second_digit == right_digit and first_digit not in {"0", "1"} and not has_explicit_suffix:
        return f"{first_digit}{op}{right_digit}"
    return expr


def extract_expression(normalized_text: str, original_text: str = "") -> Optional[str]:
    for match in CaptchaMathSolver._EXPR_PATTERN.finditer(normalized_text):
        a, op, b = match.groups()
        expr = f"{a}{op}{b}"
        expr = _repair_merged_left_operand(expr, original_text=original_text)
        return expr
    return None


def safe_evaluate(expr: str) -> Tuple[Optional[float], str]:
    match = re.fullmatch(r"(\d{1,2})([+\-*/])(\d{1,2})", expr)
    if not match:
        return None, f"invalid expression: {expr}"
    left_operand, op, right_operand = match.groups()
    left = int(left_operand)
    right = int(right_operand)

    if op == "+":
        return left + right, ""
    if op == "-":
        return left - right, ""
    if op == "*":
        return left * right, ""
    if op == "/":
        if right == 0:
            return None, "division by zero"
        if left % right == 0:
            return left // right, ""
        return left / right, ""
    return None, f"unsupported operator: {op}"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python captcha_math_solver.py <image_path>")
        return 1

    image_path = sys.argv[1]
    solver = CaptchaMathSolver()
    result = solver.solve_image(image_path)

    print(f"raw OCR: {result.raw_ocr}")
    print(f"normalized text: {result.normalized_text}")
    print(f"parsed expr: {result.parsed_expr}")
    print(f"answer: {result.answer}")
    print(f"reason: {result.reason or 'OK'}")
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
