import math
import re


class Calculator:
    def __init__(self):
        self.library = {
            "operator": ['+', '-', '*', '/', '^', '(', ')'],
            "constant": ['pi', 'e'],
            "function": ['exp', 'log', 'ln', 'sqrt',
                         'sin', 'cos', 'tan',
                         'asin', 'acos', 'atan']
        }
        self.function = {
            "exp": math.exp, "log": math.log10, "ln": math.log,
            "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
            "tan": math.tan, "asin": math.asin, "acos": math.acos, "atan": math.atan
        }
        self.tokenized_notation = list()
        self.postfix_notation = list()

    # 계산 작업
    def operation(self, expression):
        try:
            self.tokenize(expression)
            self.infix_to_postfix()

            result = self.calculate_postfix()

            if type(result) is int:
                return result
            else:
                return round(result, 4)
        except (TypeError, UnboundLocalError, IndexError, SyntaxError):
            return 'syntax error'
        except ZeroDivisionError:
            return 'division by zero error'

    # 정해진 연산자나 함수 이외의 텍스트가 있는지 체크
    def wrong_syntax_checker(self, expression):
        for i in self.library["function"]:
            expression = re.sub(i, '', expression)

        for i in self.library["constant"]:
            expression = re.sub(i, '', expression)

        rule = re.compile(r'[0-9\.\+\-\*\/\^\(\)\s]')
        expression = re.sub(rule, '', expression)

        if expression != '':
            return 'syntax error'

    # 후위 연산 우선순위
    def priority(self, operator):
        if operator in self.library["function"]:
            return 0
        elif operator == '*' or operator == '/' or operator == '^':
            return 1
        elif operator == '+' or operator == '-':
            return 2
        elif operator == '(' or operator == ')':
            return 3
        else:
            return 4

    # 입력받은 수식을 토큰화
    def tokenize(self, notation):
        # 잘못 처리된 공백까지 올바르게 전처리하기 위해 모든 공백을 삭제
        index = -1
        temp = notation.replace(" ", "")

        # 모든 연산자에 대해 공백 재삽입
        for i in self.library["operator"]:
            while True:
                index = temp.find(i, index + 1)

                if index == -1:
                    break
                else:
                    if index == 0:
                        temp = i + ' ' + temp[index + 1:]
                    else:
                        temp = temp[:index] + ' ' + i + ' ' + temp[index + 1:]
                    index += 2

        for i in self.library["function"]:
            while True:
                index = temp.find(i, index + 1)

                if index == -1:
                    break
                else:
                    if index == 0:
                        temp = i + ' ' + temp[index + len(i):]
                    else:
                        temp = temp[:index] + ' ' + i + ' ' + temp[index + len(i):]
                    index += 2

        # 입력받은 값을 바로 리스트로 변환하여 숫자는 여전히 String 임
        # 이를 연산에 바로 사용할 수 있도록 숫자로(int, float) 변환

        self.tokenized_notation = list(map(self.string_to_number,
                                           temp.replace("  ", " ").split()))

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
            if string == 'e':
                return math.e
            elif string == 'pi':
                return math.pi
            else:
                return string

    # 중위 표현식을 후위 표현식으로 변환
    def infix_to_postfix(self):
        stack = list()
        result = list()

        for i in self.tokenized_notation:

            # 숫자는 그대로 내보냄
            if type(i) is int or type(i) is float \
                    or i in self.library["constant"]:
                result.append(i)

            # 연산자 처리하기
            else:
                # '(' 이면 반드시 스택에 push
                if i == '(':
                    stack.append(i)
                # ')' 이면 '(' 가 나올 때까지 모두 pop
                # stack 은 연산 우선순위의 역순으로 정렬되어 pop 시 우선 순위대로 나오게 됨
                elif i == ')':
                    for j in range(len(stack)):
                        if stack[-1] == '(':
                            stack.pop()
                            break
                        else:
                            result.append(stack.pop())
                else:
                    # 괄호를 제외한 일반 연산자 처리
                    # 스택이 비었으면 추가
                    if not stack:
                        stack.append(i)
                    else:
                        # 현재 연산자가 스택의 연산자보다 우선순위가 높으면 스택에 추가
                        # 그렇지 않으면 스택에서 pop 하고 현재 연산자를 스택에 추가
                        if self.priority(i) < self.priority(stack[-1]):
                            stack.append(i)
                        else:
                            result.append(stack.pop())
                            stack.append(i)

        for i in range(len(stack)):
            result.append(stack.pop())

        self.postfix_notation = result

    # 후위 표현식을 계산
    def calculate_postfix(self):
        stack = list()
        temp = None

        for i in self.postfix_notation:

            if type(i) is int or type(i) is float \
                    or i in self.library["constant"]:
                stack.append(i)

            # 스택에서 차례로 pop 한 뒤 연산
            # 0이면 error 를 반환하고 종료
            # function 형태가 나오면 하나만 pop 하여 연산하면 됨
            else:
                # 일반 연산자
                if i in self.library["operator"]:
                    num1 = stack.pop()
                    num2 = stack.pop()

                    if i == '+':
                        temp = num2 + num1
                    elif i == '-':
                        temp = num2 - num1
                    elif i == '*':
                        temp = num2 * num1
                    elif i == '/':
                        temp = num2 / num1
                    elif i == '^':
                        temp = pow(num2, num1)
                # 함수
                elif i in self.library["function"]:
                    num = stack.pop()
                    temp = self.function[i](num)

                stack.append(temp)

        return stack[-1]
