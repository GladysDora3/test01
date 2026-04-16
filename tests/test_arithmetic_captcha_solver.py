import unittest

from arithmetic_captcha_solver import solve_from_ocr_text


class ArithmeticCaptchaSolverTests(unittest.TestCase):
    def test_standard_minus(self):
        result = solve_from_ocr_text("4-2=?")
        self.assertTrue(result.ok)
        self.assertEqual(result.fixed_expression, "4-2")
        self.assertEqual(result.answer, 2)

    def test_standard_plus(self):
        result = solve_from_ocr_text("7+8=?")
        self.assertTrue(result.ok)
        self.assertEqual(result.fixed_expression, "7+8")
        self.assertEqual(result.answer, 15)

    def test_standard_multiply_symbol(self):
        result = solve_from_ocr_text("9×3=?")
        self.assertTrue(result.ok)
        self.assertEqual(result.fixed_expression, "9*3")
        self.assertEqual(result.answer, 27)

    def test_standard_division(self):
        result = solve_from_ocr_text("8/2=?")
        self.assertTrue(result.ok)
        self.assertEqual(result.fixed_expression, "8/2")
        self.assertEqual(result.answer, 4)

    def test_merged_operator_loss_case(self):
        result = solve_from_ocr_text("42-2")
        self.assertTrue(result.ok)
        self.assertEqual(result.fixed_expression, "4-2")
        self.assertEqual(result.answer, 2)

    def test_invalid_or_noisy_string(self):
        result = solve_from_ocr_text("abc??")
        self.assertFalse(result.ok)
        self.assertIsNone(result.answer)


if __name__ == "__main__":
    unittest.main()
