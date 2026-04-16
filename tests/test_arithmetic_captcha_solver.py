import unittest

from arithmetic_captcha_solver import solve_arithmetic_captcha


class TestArithmeticCaptchaSolver(unittest.TestCase):
    def test_repairs_merged_first_operand(self):
        self.assertEqual(2, solve_arithmetic_captcha("42-2"))

    def test_extracts_first_valid_expression_with_trailing_noise(self):
        self.assertEqual(3, solve_arithmetic_captcha("1o-7-2"))

    def test_prefers_first_valid_expression_when_more_ops_follow(self):
        self.assertEqual(3, solve_arithmetic_captcha("10-7-3=?"))

    def test_supports_suffix_variants(self):
        self.assertEqual(8, solve_arithmetic_captcha("10-2=?"))
        self.assertEqual(8, solve_arithmetic_captcha("10-2=？"))

    def test_keeps_valid_two_digit_operand(self):
        self.assertEqual(3, solve_arithmetic_captcha("10-7=?"))

    def test_invalid_strings_fail_gracefully(self):
        self.assertIsNone(solve_arithmetic_captcha("abc"))
        self.assertIsNone(solve_arithmetic_captcha("10/0=?"))

if __name__ == "__main__":
    unittest.main()
