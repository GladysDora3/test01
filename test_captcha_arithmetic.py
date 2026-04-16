import unittest

from captcha_arithmetic import (
    normalize_ocr_text,
    parse_arithmetic_expression,
    solve_arithmetic_captcha_text,
)


class CaptchaArithmeticTests(unittest.TestCase):
    def test_normal_cases(self):
        self.assertEqual(solve_arithmetic_captcha_text("4-2=?"), 2)
        self.assertEqual(solve_arithmetic_captcha_text("7+8=?"), 15)
        self.assertEqual(solve_arithmetic_captcha_text("9×3=?"), 27)
        self.assertEqual(solve_arithmetic_captcha_text("8/2=?"), 4)

    def test_merged_token_case(self):
        self.assertEqual(parse_arithmetic_expression("42-2"), (4, "-", 2))
        self.assertEqual(solve_arithmetic_captcha_text("42-2"), 2)

    def test_symbol_normalization(self):
        self.assertEqual(normalize_ocr_text("9X3=？"), "9*3")
        self.assertEqual(normalize_ocr_text("8÷2=?"), "8/2")

    def test_invalid_or_noisy_strings(self):
        self.assertIsNone(solve_arithmetic_captcha_text("abc??"))
        self.assertIsNone(solve_arithmetic_captcha_text("1++2"))
        self.assertIsNone(solve_arithmetic_captcha_text("8/0=?"))


if __name__ == "__main__":
    unittest.main()
