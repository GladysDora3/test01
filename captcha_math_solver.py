import re
from dataclasses import dataclass
from typing import Optional


OPS = {"+", "-", "*", "/"}
ZERO_CONFUSIONS = {"o", "O", "〇", "零"}
ONE_CONFUSIONS = {"l", "I"}


@dataclass
class SolveResult:
    ok: bool
    raw_text: str
    normalized: str
    fixed_expr: str
    answer: Optional[float]
    reason: str = ""


class ArithmeticCaptchaSolver:
    def solve_text(self, raw_text: str) -> SolveResult:
        normalized = self._normalize_expr(raw_text)
        fixed_expr = self._fix_merged_operator_cases(normalized)
        answer, reason = self._safe_eval_two_operand(fixed_expr)
        if answer is None:
            return SolveResult(
                ok=False,
                raw_text=raw_text,
                normalized=normalized,
                fixed_expr=fixed_expr,
                answer=None,
                reason=reason,
            )
        return SolveResult(
            ok=True,
            raw_text=raw_text,
            normalized=normalized,
            fixed_expr=fixed_expr,
            answer=answer,
        )

    def _normalize_expr(self, text: str) -> str:
        s = text.strip()
        s = (
            s.replace("？", "?")
            .replace("=", "")
            .replace("?", "")
            .replace("x", "*")
            .replace("X", "*")
            .replace("×", "*")
            .replace("÷", "/")
            .replace("—", "-")
            .replace("–", "-")
            .replace("_", "-")
        )

        chars = list(s)
        out = []
        for i, ch in enumerate(chars):
            prev_ch = chars[i - 1] if i > 0 else ""
            next_ch = chars[i + 1] if i + 1 < len(chars) else ""

            if ch in ZERO_CONFUSIONS and (prev_ch.isdigit() or next_ch.isdigit()):
                out.append("0")
                continue

            if ch in ONE_CONFUSIONS and (prev_ch.isdigit() or next_ch.isdigit()):
                out.append("1")
                continue

            out.append(ch)

        return re.sub(r"[^0-9+\-*/]", "", "".join(out))

    def _fix_merged_operator_cases(self, expr: str) -> str:
        """
        Conservative fix for OCR merged-operator errors.
        Keep valid two-digit values containing 0 (e.g. 10+2) unchanged.
        """
        m = re.fullmatch(r"(\d{2})([+\-*/])(\d{1,2})", expr)
        if m:
            left, op, right = m.groups()
            if "0" in left:
                return expr
            return f"{left[0]}{op}{right}"

        m = re.fullmatch(r"(\d{1,2})([+\-*/])(\d{2})", expr)
        if m:
            left, op, right = m.groups()
            if "0" in right:
                return expr
            return f"{left}{op}{right[0]}"

        return expr

    def _safe_eval_two_operand(self, expr: str):
        m = re.fullmatch(r"(\d{1,2})([+\-*/])(\d{1,2})", expr)
        if not m:
            return None, f"invalid expression: {expr}"

        a_s, op, b_s = m.groups()
        a, b = int(a_s), int(b_s)
        if op == "+":
            return a + b, ""
        if op == "-":
            return a - b, ""
        if op == "*":
            return a * b, ""
        if op == "/":
            if b == 0:
                return None, "division by zero"
            if a % b == 0:
                return a // b, ""
            return a / b, ""
        return None, f"unsupported operator: {op}"
