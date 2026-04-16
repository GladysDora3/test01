# test01

## Arithmetic captcha solver (ddddocr)

Local runnable example is in:

- `/home/runner/work/test01/test01/arithmetic_captcha_solver.py`

Install dependencies:

```bash
pip install ddddocr opencv-python Pillow numpy
```

Run with a local image path:

```bash
python arithmetic_captcha_solver.py /path/to/captcha.png
```

Output includes:

- raw OCR text
- normalized expression
- fixed expression (includes merged-operator repair like `42-2` -> `4-2`)
- computed answer

Run unit tests:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```
