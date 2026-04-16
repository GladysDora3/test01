import logging
import re
import unicodedata
from io import BytesIO
from typing import Callable, Optional, Tuple

LOGGER = logging.getLogger(__name__)

_OPERATOR_NORMALIZATION = {
    "x": "*",
    "X": "*",
    "×": "*",
    "＊": "*",
    "÷": "/",
    "／": "/",
    "＋": "+",
    "﹢": "+",
    "－": "-",
    "﹣": "-",
    "–": "-",
    "—": "-",
}

_ALLOWED_CHARS = set("0123456789+-*/=?")
_MERGED_PATTERN = re.compile(r"^(\d+)(\d)([+\-*/])\2$")
_SIMPLE_EXPR_PATTERN = re.compile(r"^(\d+)([+\-*/])(\d+)$")


def preprocess_arithmetic_captcha(image_bytes: bytes) -> bytes:
    """Apply lightweight denoise/binarization before OCR.

    Falls back to the original bytes when image tooling is unavailable.
    """
    try:
        from PIL import Image, ImageFilter

        image = Image.open(BytesIO(image_bytes)).convert("L")
        image = image.filter(ImageFilter.MedianFilter(size=3))
        image = image.point(lambda p: 255 if p > 170 else 0, mode="1").convert("L")
        image = image.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))

        output = BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()
    except Exception as exc:  # pragma: no cover - fallback behavior only
        LOGGER.warning("Captcha preprocessing failed, using original image: %s", exc)
        return image_bytes


def normalize_ocr_text(raw_text: str) -> str:
    normalized = unicodedata.normalize("NFKC", raw_text or "")
    normalized = "".join(_OPERATOR_NORMALIZATION.get(ch, ch) for ch in normalized)
    normalized = "".join(ch for ch in normalized if ch in _ALLOWED_CHARS)

    normalized = normalized.rstrip("?？")
    if "=" in normalized:
        normalized = normalized.split("=", 1)[0]

    return normalized.strip()


def parse_arithmetic_expression(raw_text: str) -> Optional[Tuple[int, str, int]]:
    text = normalize_ocr_text(raw_text)
    if not text:
        LOGGER.info("OCR text is empty after normalization: %r", raw_text)
        return None

    merged_match = _MERGED_PATTERN.match(text)
    if merged_match:
        left, right, operator = merged_match.groups()
        LOGGER.info("Detected likely merged OCR token %r, repaired to %s%s%s", text, left, operator, right)
        return int(left), operator, int(right)

    simple_match = _SIMPLE_EXPR_PATTERN.match(text)
    if simple_match:
        left, operator, right = simple_match.groups()
        return int(left), operator, int(right)

    LOGGER.info("Unable to parse arithmetic captcha OCR text: %r -> %r", raw_text, text)
    return None


def evaluate_two_operand_expression(left: int, operator: str, right: int) -> Optional[int]:
    if operator == "+":
        return left + right
    if operator == "-":
        return left - right
    if operator == "*":
        return left * right
    if operator == "/":
        if right == 0:
            LOGGER.warning("Division by zero in captcha expression: %s/%s", left, right)
            return None
        if left % right != 0:
            LOGGER.warning("Non-integer division in captcha expression: %s/%s", left, right)
            return None
        return left // right

    LOGGER.warning("Unsupported operator in captcha expression: %r", operator)
    return None


def solve_arithmetic_captcha_text(raw_text: str) -> Optional[int]:
    parsed = parse_arithmetic_expression(raw_text)
    if not parsed:
        return None

    left, operator, right = parsed
    return evaluate_two_operand_expression(left, operator, right)


def _default_ddddocr_classifier(image_bytes: bytes) -> str:
    import ddddocr

    ocr = ddddocr.DdddOcr(show_ad=False)
    return ocr.classification(image_bytes)


def recognize_arithmetic_captcha(
    image_bytes: bytes,
    classifier: Optional[Callable[[bytes], str]] = None,
) -> Optional[int]:
    processed_image = preprocess_arithmetic_captcha(image_bytes)
    ocr_classifier = classifier or _default_ddddocr_classifier

    try:
        ocr_text = ocr_classifier(processed_image)
    except Exception as exc:
        LOGGER.error("Arithmetic captcha OCR failed: %s", exc)
        return None

    return solve_arithmetic_captcha_text(ocr_text)
