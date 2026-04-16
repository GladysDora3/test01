import unittest

from captcha_math_solver import ArithmeticCaptchaSolver


class ArithmeticCaptchaSolverTests(unittest.TestCase):
    def setUp(self):
        self.solver = ArithmeticCaptchaSolver()

    def test_ocr_confused_zero_is_normalized(self):
        result = self.solver.solve_text("1o+2=？")
        self.assertTrue(result.ok)
        self.assertEqual(result.normalized, "10+2")
        self.assertEqual(result.fixed_expr, "10+2")
        self.assertEqual(result.answer, 12)

    def test_two_digit_input_stays_two_digit(self):
        result = self.solver.solve_text("10+2=?")
        self.assertTrue(result.ok)
        self.assertEqual(result.fixed_expr, "10+2")
        self.assertEqual(result.answer, 12)

    def test_single_digit_case_still_works(self):
        result = self.solver.solve_text("4-2=?")
        self.assertTrue(result.ok)
        self.assertEqual(result.answer, 2)

    def test_merged_case_fix_still_applies(self):
        result = self.solver.solve_text("42-2")
        self.assertTrue(result.ok)
        self.assertEqual(result.fixed_expr, "4-2")
        self.assertEqual(result.answer, 2)

    def test_non_zero_two_digit_operand_is_preserved(self):
        result = self.solver.solve_text("15+3=?")
        self.assertTrue(result.ok)
        self.assertEqual(result.fixed_expr, "15+3")
        self.assertEqual(result.answer, 18)


if __name__ == "__main__":
    unittest.main()
