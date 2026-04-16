import unittest
from io import StringIO
import tempfile
from types import SimpleNamespace
from unittest import mock

import arithmetic_captcha_solver
from arithmetic_captcha_solver import SolveResult, solve_from_ocr_text


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

    def test_solve_image_bytes_without_ddddocr(self):
        real_import = __import__

        def fake_import(name, *args, **kwargs):
            if name == "ddddocr":
                raise ImportError("missing")
            return real_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=fake_import):
            with self.assertRaises(RuntimeError):
                arithmetic_captcha_solver.solve_image_bytes(b"img")

    def test_solve_image_bytes_with_scored_candidates(self):
        class FakeOcr:
            def __init__(self, show_ad=False):
                self.show_ad = show_ad

            def classification(self, sample):
                if sample == b"v1":
                    return "bad"
                if sample == b"v2":
                    return "42-2"
                return ""

        fake_ddddocr = SimpleNamespace(DdddOcr=FakeOcr)
        with mock.patch.dict("sys.modules", {"ddddocr": fake_ddddocr}):
            with mock.patch.object(
                arithmetic_captcha_solver, "_maybe_preprocess_variants", return_value=[b"v1", b"v2"]
            ):
                result = arithmetic_captcha_solver.solve_image_bytes(b"img")
        self.assertTrue(result.ok)
        self.assertEqual(result.fixed_expression, "4-2")
        self.assertEqual(result.answer, 2)

    def test_solve_image_path_reads_file(self):
        with tempfile.NamedTemporaryFile(delete=True) as tf:
            tf.write(b"bytes")
            tf.flush()
            with mock.patch.object(
                arithmetic_captcha_solver, "solve_image_bytes", return_value=SolveResult(True, "x", "1+1", "1+1", 2, None)
            ) as mocked:
                result = arithmetic_captcha_solver.solve_image_path(tf.name)
        mocked.assert_called_once_with(b"bytes")
        self.assertTrue(result.ok)

    def test_main_success_output(self):
        fake = SolveResult(True, "42-2", "42-2", "4-2", 2, None)
        out = StringIO()
        with mock.patch.object(arithmetic_captcha_solver, "solve_image_path", return_value=fake):
            with mock.patch("sys.stdout", out):
                code = arithmetic_captcha_solver.main(["/tmp/fake.png"])
        text = out.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("raw OCR text: 42-2", text)
        self.assertIn("fixed expression: 4-2", text)
        self.assertIn("computed answer: 2", text)


if __name__ == "__main__":
    unittest.main()
