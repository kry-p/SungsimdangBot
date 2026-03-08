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

    @pytest.mark.xfail(reason="^ treated as left-associative", strict=True)
    def test_power_right_associative(self, calc):
        assert calc.operation(" 2 ^ 3 ^ 2") == 512

    def test_left_associative_division(self, calc):
        assert calc.operation(" 6 / 2 * 3") == 9.0

    def test_left_associative_subtraction(self, calc):
        assert calc.operation(" 10 - 3 - 2") == 5

    def test_deeply_nested_parentheses(self, calc):
        assert calc.operation(" (((2 + 3)))") == 5

    @pytest.mark.xfail(reason="implicit multiplication not supported", strict=True)
    def test_adjacent_parentheses_implicit_mul(self, calc):
        assert calc.operation(" (2 + 3)(4 + 1)") == 25


class TestNegativeNumbers:
    def test_negative_result(self, calc):
        assert calc.operation(" 3 - 5") == -2

    def test_leading_negative(self, calc):
        assert calc.operation(" -3 + 5") == 2

    @pytest.mark.xfail(reason="negative after operator not handled", strict=True)
    def test_negative_after_operator(self, calc):
        assert calc.operation(" 5 * -3") == -15

    def test_negative_in_parentheses(self, calc):
        assert calc.operation(" (-3) + 5") == 2


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


class TestStringToNumber:
    def test_integer(self, calc):
        assert calc.string_to_number("42") == 42
        assert isinstance(calc.string_to_number("42"), int)

    def test_float(self, calc):
        assert calc.string_to_number("3.14") == 3.14
        assert isinstance(calc.string_to_number("3.14"), float)

    def test_constant_pi(self, calc):
        assert calc.string_to_number("pi") == math.pi

    def test_constant_e(self, calc):
        assert calc.string_to_number("e") == math.e

    def test_non_numeric_string(self, calc):
        assert calc.string_to_number("+") == "+"
        assert calc.string_to_number("sqrt") == "sqrt"


class TestWrongSyntaxChecker:
    def test_valid_expression(self, calc):
        assert calc.wrong_syntax_checker("2 + 3 * 4") is None

    def test_valid_with_constants(self, calc):
        assert calc.wrong_syntax_checker("pi + e") is None

    def test_valid_with_functions(self, calc):
        assert calc.wrong_syntax_checker("sqrt(4)") is None

    def test_invalid_characters(self, calc):
        assert calc.wrong_syntax_checker("2 + abc") == "syntax error"

    def test_invalid_single_letter(self, calc):
        assert calc.wrong_syntax_checker("x") == "syntax error"


class TestPriority:
    def test_function_priority(self, calc):
        assert calc.priority("sqrt") == 0
        assert calc.priority("sin") == 0

    def test_power_priority(self, calc):
        assert calc.priority("^") == 1

    def test_mul_div_priority(self, calc):
        assert calc.priority("*") == 2
        assert calc.priority("/") == 2

    def test_add_sub_priority(self, calc):
        assert calc.priority("+") == 3
        assert calc.priority("-") == 3

    def test_parentheses_priority(self, calc):
        assert calc.priority("(") == 4
        assert calc.priority(")") == 4

    def test_power_higher_than_mul_div(self, calc):
        assert calc.priority("^") < calc.priority("*")

    def test_unknown_priority(self, calc):
        assert calc.priority("xyz") == 5


class TestOperationEdgeCases:
    def test_decimal_arithmetic(self, calc):
        assert calc.operation(" 0.1 + 0.2") == round(0.1 + 0.2, 4)

    def test_constants_combination(self, calc):
        assert calc.operation(" pi + e") == round(math.pi + math.e, 4)

    def test_power_precedence(self, calc):
        assert calc.operation(" 2 ^ 3 * 2") == 16

    @pytest.mark.xfail(reason="consecutive negative operands not supported", strict=True)
    def test_negative_times_negative(self, calc):
        assert calc.operation(" -2 * -3") == 6

    def test_large_number(self, calc):
        assert calc.operation(" 999999 * 999999") == 999998000001

    def test_only_whitespace(self, calc):
        assert calc.operation("   ") == "syntax error"


class TestFunctionCalls:
    @pytest.mark.xfail(reason="str.insert() bug in tokenize() line 80", strict=True)
    def test_sqrt(self, calc):
        assert calc.operation(" sqrt(4)") == 2.0

    @pytest.mark.xfail(reason="str.insert() bug in tokenize() line 80", strict=True)
    def test_sin_zero(self, calc):
        assert calc.operation(" sin(0)") == 0.0

    @pytest.mark.xfail(reason="str.insert() bug in tokenize() line 80", strict=True)
    def test_cos_zero(self, calc):
        assert calc.operation(" cos(0)") == 1.0

    @pytest.mark.xfail(reason="str.insert() bug in tokenize() line 80", strict=True)
    def test_log_ten(self, calc):
        assert calc.operation(" log(10)") == 1.0

    @pytest.mark.xfail(reason="str.insert() bug in tokenize() line 80", strict=True)
    def test_function_in_expression(self, calc):
        assert calc.operation(" 1 + sqrt(9)") == 4.0
