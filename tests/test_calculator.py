import math

import pytest

from modules.calculator import Calculator


@pytest.fixture
def calc():
    return Calculator()


class TestBasicArithmetic:
    def test_addition(self, calc):
        assert calc.operation(" 2 + 3") == 5

    def test_subtraction(self, calc):
        assert calc.operation(" 10 - 4") == 6

    def test_multiplication(self, calc):
        assert calc.operation(" 3 * 7") == 21

    def test_division(self, calc):
        assert calc.operation(" 15 / 3") == 5

    def test_division_float(self, calc):
        assert calc.operation(" 7 / 2") == 3.5

    def test_power(self, calc):
        assert calc.operation(" 2 ^ 10") == 1024


class TestPrecedence:
    def test_mul_before_add(self, calc):
        assert calc.operation(" 2 + 3 * 4") == 14

    def test_parentheses(self, calc):
        assert calc.operation(" (2 + 3) * 4") == 20

    @pytest.mark.xfail(reason="nested parentheses not fully supported", strict=True)
    def test_nested_parentheses(self, calc):
        assert calc.operation(" ((1 + 2) * (3 + 4))") == 21


class TestNegativeNumbers:
    def test_negative_result(self, calc):
        assert calc.operation(" 3 - 5") == -2

    def test_leading_negative(self, calc):
        assert calc.operation(" -3 + 5") == 2


class TestConstants:
    def test_pi(self, calc):
        assert calc.operation(" pi") == round(math.pi, 4)

    def test_e(self, calc):
        assert calc.operation(" e") == round(math.e, 4)


class TestErrors:
    def test_division_by_zero(self, calc):
        assert calc.operation(" 1 / 0") == "division by zero error"

    def test_syntax_error_letters(self, calc):
        assert calc.operation(" abc") == "syntax error"

    def test_empty_expression(self, calc):
        assert calc.operation("") == "syntax error"


class TestFunctionCalls:
    @pytest.mark.xfail(reason="str.insert() bug in tokenize() line 80", strict=True)
    def test_sqrt(self, calc):
        assert calc.operation(" sqrt(4)") == 2.0

    @pytest.mark.xfail(reason="str.insert() bug in tokenize() line 80", strict=True)
    def test_sin_zero(self, calc):
        assert calc.operation(" sin(0)") == 0.0
