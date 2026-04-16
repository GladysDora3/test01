"""Local arithmetic captcha solver example using ddddocr.

Usage:
    python arithmetic_captcha_solver.py <image_path>
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple


_OPERATOR_MAP = {
    "x": "*",
    "X": "*",
    "×": "*",
    "✕": "*",
    "*": "*",
    "÷": "/",
    "／": "/",
    "?": "",
    "？": "",
    "=": "",
}


@dataclass
class SolveResult:
    ok: bool
    raw_text: str
    normalized_expression: str
    fixed_expression: str
    answer: Optional[float]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "raw_text": self.raw_text,
            "normalized_expression": self.normalized_expression,
            "fixed_expression": self.fixed_expression,
            "answer": self.answer,
            "error": self.error,
        }


def _maybe_preprocess_variants(image_bytes: bytes) -> List[bytes]:
    """Return OCR input variants (original + optional OpenCV variants)."""
    variants = [image_bytes]
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except Exception:
        return variants

    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return variants

    # Light denoise + adaptive threshold variants for symbol retention.
    blur = cv2.GaussianBlur(img, (3, 3), 0)
    _, th_bin = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    _, th_inv = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    for item in (th_bin, th_inv):
        ok, encoded = cv2.imencode(".png", item)
        if ok:
            variants.append(encoded.tobytes())

    return variants


def normalize_ocr_text(text: str) -> str:
    text = text.strip().replace(" ", "")
    for src, dst in _OPERATOR_MAP.items():
        text = text.replace(src, dst)
    text = text.replace("－", "-").replace("–", "-").replace("—", "-")
    text = text.replace("＋", "+")
    # Keep only digits and basic operators.
    text = re.sub(r"[^0-9+\-*/]", "", text)
    return text


def _is_basic_expr(expr: str) -> bool:
    return bool(re.fullmatch(r"\d+[+\-*/]\d+", expr))


def repair_likely_merged_operator(expr: str) -> str:
    r"""Repair likely operator-loss OCR output, e.g. `42-2` -> `4-2`.

    Heuristic:
    - If expression already parseable as one-digit left operand form, keep as-is.
    - If left side is 2+ digits and right side is 1 digit (`\d{2,}[op]\d`),
      prefer taking the first left digit as true left operand.
    """
    if _is_basic_expr(expr):
        # Keep normally parsed expression; only adjust suspicious merged-left case below.
        pass

    m = re.fullmatch(r"(\d{2})([+\-*/])(\d)", expr)
    if not m:
        return expr

    left, op, right = m.groups()
    # Common OCR merge: "4-2" -> "42-2" (missing operator between first 2 chars).
    return f"{left[0]}{op}{right}"


def parse_expression(expr: str) -> Optional[Tuple[int, str, int]]:
    m = re.fullmatch(r"(\d+)([+\-*/])(\d+)", expr)
    if not m:
        return None
    left, op, right = m.groups()
    return int(left), op, int(right)


def compute_expression(expr: str) -> Optional[float]:
    parsed = parse_expression(expr)
    if not parsed:
        return None

    left, op, right = parsed
    if op == "+":
        return float(left + right)
    if op == "-":
        return float(left - right)
    if op == "*":
        return float(left * right)
    if op == "/":
        if right == 0:
            return None
        return float(left / right)
    return None


def solve_from_ocr_text(raw_text: str) -> SolveResult:
    normalized = normalize_ocr_text(raw_text)
    fixed = repair_likely_merged_operator(normalized)
    answer = compute_expression(fixed)
    if answer is None:
        return SolveResult(
            ok=False,
            raw_text=raw_text,
            normalized_expression=normalized,
            fixed_expression=fixed,
            answer=None,
            error="unable to parse/compute arithmetic expression",
        )
    return SolveResult(
        ok=True,
        raw_text=raw_text,
        normalized_expression=normalized,
        fixed_expression=fixed,
        answer=int(answer) if answer.is_integer() else answer,
        error=None,
    )


def _candidate_score(raw_text: str) -> int:
    normalized = normalize_ocr_text(raw_text)
    fixed = repair_likely_merged_operator(normalized)
    score = 0
    if re.search(r"[+\-*/]", normalized):
        score += 2
    if parse_expression(fixed):
        score += 3
    if compute_expression(fixed) is not None:
        score += 5
    return score


def solve_image_bytes(image_bytes: bytes) -> SolveResult:
    try:
        import ddddocr  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "ddddocr is required for image OCR. Install dependencies first."
        ) from exc

    ocr = ddddocr.DdddOcr(show_ad=False)
    candidates: List[str] = []
    for sample in _maybe_preprocess_variants(image_bytes):
        try:
            txt = ocr.classification(sample)
        except Exception:
            continue
        if txt:
            candidates.append(txt)

    if not candidates:
        return SolveResult(
            ok=False,
            raw_text="",
            normalized_expression="",
            fixed_expression="",
            answer=None,
            error="ocr returned no text",
        )

    best_raw = max(candidates, key=_candidate_score)
    return solve_from_ocr_text(best_raw)


def solve_image_path(image_path: str) -> SolveResult:
    with open(image_path, "rb") as f:
        data = f.read()
    return solve_image_bytes(data)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Solve local arithmetic captcha image")
    parser.add_argument("image_path", help="Local captcha image path")
    args = parser.parse_args(list(argv) if argv is not None else None)

    result = solve_image_path(args.image_path)
    print(f"raw OCR text: {result.raw_text}")
    print(f"normalized expression: {result.normalized_expression}")
    print(f"fixed expression: {result.fixed_expression}")
    if result.ok:
        print(f"computed answer: {result.answer}")
        return 0
    print(f"error: {result.error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
