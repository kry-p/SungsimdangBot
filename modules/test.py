import math
import re


class NewCalculator:
    def __init__(self):
        self.library = {
            "operator": ['+', '-', '*', '/', '^', '(', ')'],
            "function": ['exp', 'log', 'ln', 'sqrt',
                         'sin', 'cos', 'tan',
                         'asin', 'acos', 'atan'],
            "constant":['pi', 'e']
        }
        self.result = None

    def operation(self, expression):
        self.expression = expression
        self.string_convert()
        self.infix_change()
        return self.result

    def string_convert(self, string):
        # 공백제거 겸 문자열의 리스트화
        string = string.replace(" ", "")
        pre_trig = 0
        counter = 0
        stack_c = 0
        raw_notation = list()

        # 문자열의 공백 제거 후 원소 분리
        while len(string) > counter:
            for i in string:
                post_trig = 2
                if i in self.library["operator"]:
                    post_trig = 1
                elif post_trig != 1 and i.isnumeric():
                    post_trig = 0

                if counter == 0:
                    if i == '-':
                        raw_notation.append(string[0:1])
                        counter += 2
                        pre_trig = 0
                        continue
                    elif i in self.library["operator"]:
                        # 에러 반환하기(수식의 맨앞이 연산자)
                        return 'syntax error'
                    raw_notation.append(i)
                    pre_trig = post_trig
                    counter += 1
                    continue
                elif pre_trig == post_trig:
                    raw_notation[stack_c] = raw_notation[stack_c] + i
                else:
                    stack_c += 1
                    raw_notation.append(i)
                    pre_trig = post_trig
                counter += 1

        # 문자열로 남아있는 숫자의 실수형 변환
        for i in range(len(raw_notation)):
            if raw_notation[i].isnumeric():
                raw_notation[i] = float(raw_notation[i])

        self.temp_log = [counter, stack_c, post_trig, raw_notation]

        # 예외문자 혹은 연산자 확인
        for i in raw_notation:
            checksum = 0
            for key, value in self.library.items():
                if i in value or self.is_number(i):
                    checksum = 1
                    continue
            if not checksum:
                self.result = 'syntax error'
                break



        self.tokenized_notation = raw_notation
        return self.tokenized_notation


    def infix_change(self):
        if not self.result:
            return



    @staticmethod
    def is_number(string):
        try:
            float(string)
            return True
        except ValueError:
            return False

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


if __name__ == '__main__':
    # calcex = NewCalculator()
    # print(calcex.string_convert('cex+3'))
    # print(calcex.temp_log)

    x = None
    print(not x)