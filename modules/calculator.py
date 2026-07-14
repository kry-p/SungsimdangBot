import math
import re


class CalculationLimitError(Exception):
    pass


class Calculator:
    CALC_LIMIT_ERROR = "calculation limit error"
    MAX_EXPRESSION_LENGTH = 2000
    MAX_NUMBER_DIGITS = 1000
    MAX_RESULT_DIGITS = 1000
    MAX_TOKENS = 200

    def __init__(
        self,
        max_expression_length=MAX_EXPRESSION_LENGTH,
        max_number_digits=MAX_NUMBER_DIGITS,
        max_result_digits=MAX_RESULT_DIGITS,
        max_tokens=MAX_TOKENS,
    ):
        self.max_expression_length = max_expression_length
        self.max_number_digits = max_number_digits
        self.max_result_digits = max_result_digits
        self.max_tokens = max_tokens
        self.library = {
            "operator": ["+", "-", "*", "/", "^", "(", ")"],
            "constant": ["pi", "e"],
            "function": ["exp", "log", "ln", "sqrt", "sin", "cos", "tan", "asin", "acos", "atan"],
        }
        self.function = {
            "exp": math.exp,
            "log": math.log10,
            "ln": math.log,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "asin": math.asin,
            "acos": math.acos,
            "atan": math.atan,
        }

    # 계산 작업
    def operation(self, expression):
        try:
            if len(expression) > self.max_expression_length:
                raise CalculationLimitError
            check = self.wrong_syntax_checker(expression)
            if check == "syntax error":
                return "syntax error"
            tokens = self.tokenize(expression)
            postfix = self.infix_to_postfix(tokens)

            result = self.calculate_postfix(postfix)

            if isinstance(result, int):
                return result
            else:
                return round(result, 4)
        except CalculationLimitError:
            return self.CALC_LIMIT_ERROR
        except (TypeError, UnboundLocalError, IndexError, SyntaxError, ValueError, OverflowError):
            return "syntax error"
        except ZeroDivisionError:
            return "division by zero error"

    # 정해진 연산자나 함수 이외의 텍스트가 있는지 체크
    def wrong_syntax_checker(self, expression):
        for i in sorted(self.library["function"], key=len, reverse=True):
            expression = re.sub(i, "", expression)

        for i in self.library["constant"]:
            expression = re.sub(i, "", expression)

        rule = re.compile(r"[0-9\.\+\-\*\/\^\(\)\s]")
        expression = re.sub(rule, "", expression)

        if expression != "":
            return "syntax error"

    # 후위 연산 우선순위
    def priority(self, operator):
        if operator in self.library["function"]:
            return 0
        elif operator == "^":
            return 1
        elif operator == "*" or operator == "/":
            return 2
        elif operator == "+" or operator == "-":
            return 3
        elif operator == "(" or operator == ")":
            return 4
        else:
            return 5

    # 입력받은 수식을 토큰화
    def tokenize(self, notation):
        text = notation.replace(" ", "")
        if not text:
            raise SyntaxError

        # 정규식으로 토큰 추출 (함수명은 길이 역순으로 매칭)
        func_pattern = "|".join(sorted(self.library["function"], key=len, reverse=True))
        const_pattern = "|".join(sorted(self.library["constant"], key=len, reverse=True))
        pattern = rf"({func_pattern}|{const_pattern}|\d+\.?\d*|[+\-*/^()])"
        tokens = re.findall(pattern, text)

        if "".join(tokens) != text:
            raise SyntaxError
        if len(tokens) > self.max_tokens:
            raise CalculationLimitError
        for tok in tokens:
            if re.fullmatch(r"\d+\.?\d*", tok) and self._numeric_token_digits(tok) > self.max_number_digits:
                raise CalculationLimitError

        # 값 토큰: 숫자, 상수, 닫는 괄호
        def is_value(tok):
            return tok == ")" or tok in self.library["constant"] or re.fullmatch(r"\d+\.?\d*", tok)

        # 암시적 곱셈 삽입 및 단항 마이너스 처리
        result = []
        for tok in tokens:
            # 암시적 곱셈: 값 토큰 뒤에 (, 함수, 상수, 숫자가 오면 * 삽입
            if (
                result
                and is_value(result[-1])
                and (
                    tok == "("
                    or tok in self.library["function"]
                    or tok in self.library["constant"]
                    or re.fullmatch(r"\d+\.?\d*", tok)
                )
            ):
                result.append("*")

            # 단항 마이너스: 이전 토큰이 없거나 ( 또는 연산자이면 -1 * 로 변환
            if tok == "-" and (not result or result[-1] == "(" or result[-1] in "+-*/^"):
                result.extend(["-1", "*"])
            else:
                result.append(tok)
        if len(result) > self.max_tokens:
            raise CalculationLimitError

        # 괄호 균형 검증
        depth = 0
        for tok in result:
            if tok == "(":
                depth += 1
            elif tok == ")":
                depth -= 1
            if depth < 0:
                raise SyntaxError
        if depth != 0:
            raise SyntaxError

        return list(map(self.string_to_number, result))

    @staticmethod
    def _numeric_token_digits(token):
        digits = token.replace(".", "").lstrip("0")
        return max(len(digits), 1)

    # String 형태의 숫자를 정수와 실수로 변환
    @staticmethod
    def string_to_number(string):
        try:
            result = float(string)

            if string.isdigit():
                return int(string)
            else:
                return result

        except ValueError:
            if string == "e":
                return math.e
            elif string == "pi":
                return math.pi
            else:
                return string

    # 중위 표현식을 후위 표현식으로 변환
    def infix_to_postfix(self, tokenized_notation):
        stack = []
        result = []

        for i in tokenized_notation:
            # 숫자는 그대로 내보냄
            if isinstance(i, (int, float)) or i in self.library["constant"]:
                result.append(i)

            # 연산자 처리하기
            else:
                # '(' 이면 반드시 스택에 push
                if i == "(":
                    stack.append(i)
                # ')' 이면 '(' 가 나올 때까지 모두 pop
                # stack 은 연산 우선순위의 역순으로 정렬되어 pop 시 우선 순위대로 나오게 됨
                elif i == ")":
                    while stack:
                        if stack[-1] == "(":
                            stack.pop()
                            break
                        result.append(stack.pop())
                else:
                    while (
                        stack
                        and stack[-1] != "("
                        and (
                            self.priority(stack[-1]) < self.priority(i)
                            or (self.priority(stack[-1]) == self.priority(i) and i != "^")
                        )
                    ):
                        result.append(stack.pop())
                    stack.append(i)

        while stack:
            result.append(stack.pop())

        return result

    # 후위 표현식을 계산
    def calculate_postfix(self, postfix_notation):
        stack = []
        temp = None

        for i in postfix_notation:
            if isinstance(i, (int, float)) or i in self.library["constant"]:
                stack.append(self._validate_number(i))

            # 스택에서 차례로 pop 한 뒤 연산
            # 0이면 error 를 반환하고 종료
            # function 형태가 나오면 하나만 pop 하여 연산하면 됨
            else:
                # 일반 연산자
                if i in self.library["operator"]:
                    num1 = stack.pop()
                    num2 = stack.pop()

                    if i == "+":
                        temp = num2 + num1
                    elif i == "-":
                        temp = num2 - num1
                    elif i == "*":
                        temp = num2 * num1
                    elif i == "/":
                        temp = num2 / num1
                    elif i == "^":
                        self._validate_power_operands(num2, num1)
                        temp = pow(num2, num1)
                # 함수
                elif i in self.library["function"]:
                    num = stack.pop()
                    temp = self.function[i](num)

                stack.append(self._validate_number(temp))

        return stack[-1]

    def _validate_number(self, value):
        if isinstance(value, int):
            if self._int_digit_count(value) > self.max_result_digits:
                raise CalculationLimitError
            return value
        if isinstance(value, float):
            if not math.isfinite(value):
                raise CalculationLimitError
            if self._float_digit_count(value) > self.max_result_digits:
                raise CalculationLimitError
            return value
        raise ValueError

    @staticmethod
    def _int_digit_count(value):
        return len(str(abs(value)))

    @staticmethod
    def _float_digit_count(value):
        if value == 0:
            return 1
        return max(int(math.floor(math.log10(abs(value)))) + 1, 1)

    def _validate_power_operands(self, base, exponent):
        if base < 0 and not self._is_integer_value(exponent):
            raise ValueError
        if base == 0 or abs(base) == 1 or exponent == 0:
            return

        log10_base = math.log10(abs(base))
        if log10_base > 0 and exponent >= self.max_result_digits / log10_base:
            raise CalculationLimitError
        if log10_base < 0 and exponent <= self.max_result_digits / log10_base:
            raise CalculationLimitError

    @staticmethod
    def _is_integer_value(value):
        return isinstance(value, int) or (isinstance(value, float) and value.is_integer())
