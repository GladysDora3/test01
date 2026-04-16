import unittest

from captcha_math_solver import CaptchaMathSolver, extract_expression, normalize_text, safe_evaluate


class TestCaptchaMathSolver(unittest.TestCase):
    def setUp(self) -> None:
        self.solver = CaptchaMathSolver()

    def test_merged_operand_repair_for_reported_42_minus_2(self) -> None:
        result = self.solver.solve_text("42-2")
        self.assertTrue(result.ok)
        self.assertEqual(result.parsed_expr, "4-2")
        self.assertEqual(result.answer, 2)

    def test_reported_case_1o_minus_7_minus_2_extracts_10_minus_7(self) -> None:
        result = self.solver.solve_text("1o-7-2")
        self.assertTrue(result.ok)
        self.assertEqual(result.normalized_text, "10-7-2")
        self.assertEqual(result.parsed_expr, "10-7")
        self.assertEqual(result.answer, 3)

    def test_valid_two_digit_expression_is_not_broken(self) -> None:
        result = self.solver.solve_text("10-7=?")
        self.assertTrue(result.ok)
        self.assertEqual(result.parsed_expr, "10-7")
        self.assertEqual(result.answer, 3)

    def test_valid_two_digit_expression_like_12_minus_2_is_not_repaired(self) -> None:
        result = self.solver.solve_text("12-2=?")
        self.assertTrue(result.ok)
        self.assertEqual(result.parsed_expr, "12-2")
        self.assertEqual(result.answer, 10)

    def test_suffix_cleanup_and_mapping(self) -> None:
        self.assertEqual(normalize_text("1O+2=？"), "10+2")
        self.assertEqual(extract_expression("10+2"), "10+2")

    def test_normal_arithmetic(self) -> None:
        self.assertEqual(safe_evaluate("9+8")[0], 17)
        self.assertEqual(safe_evaluate("9-8")[0], 1)
        self.assertEqual(safe_evaluate("9*8")[0], 72)
        self.assertEqual(safe_evaluate("9/2")[0], 4.5)


if __name__ == "__main__":
    unittest.main()
