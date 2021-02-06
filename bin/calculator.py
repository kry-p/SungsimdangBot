class Calculator:
    def __init__(self, ):
        self.operator = ['+', '-', '*', '/', '(', ')']
        self.tokenized_notation = list()
        self.postfix_notation = list()

    # 계산 작업
    def operation(self, notation):
        self.tokenize(notation)
        self.infix_to_postfix()
        return self.calculate_postfix()

    # 후위 연산 우선순위
    @staticmethod
    def priority(operator):
        if operator == '*' or operator == '/':
            return 0
        elif operator == '+' or operator == '-':
            return 1
        elif operator == '(' or operator == ')':
            return 2
        else:
            return 3

    # 입력받은 수식을 토큰화
    def tokenize(self, notation):
        # 잘못 처리된 공백까지 올바르게 전처리하기 위해 모든 공백을 삭제
        index = -1
        temp = notation.replace(" ", "")

        # 모든 연산자에 대해 공백 재삽입
        for i in self.operator:
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
            return string

    # 중위 표현식을 후위 표현식으로 변환
    def infix_to_postfix(self):
        stack = list()
        result = list()

        for i in self.tokenized_notation:

            # 숫자는 그대로 내보냄
            if type(i) is int or type(i) is float:
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

        for i in self.postfix_notation:

            if type(i) is int or type(i) is float:
                stack.append(i)

            # 스택에서 차례로 pop 한 뒤 연산
            # 0이면 error 를 반환하고 종료
            else:
                num1 = stack.pop()
                num2 = stack.pop()

                if i == '+':
                    temp = num2 + num1
                elif i == '-':
                    temp = num2 - num1
                elif i == '*':
                    temp = num2 * num1
                elif i == '/':
                    try:
                        temp = num2 / num1
                    except ZeroDivisionError:
                        return 'error : divided by zero'
                stack.append(temp)

        return stack[-1]

