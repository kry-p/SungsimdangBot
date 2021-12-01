import math
import re


class NewCalculator:
    def __init__(self):
        self.library = {
            "operator": ['+', '-', '*', '/', '^', '(', ')'],
            "function": ['exp', 'log', 'ln', 'sqrt',
                         'sin', 'cos', 'tan',
                         'asin', 'acos', 'atan']
        }

    def operation(self, expression):
        notation = string_convert(expression)
        result = infix_change(notation)
        return result

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

        # 문자열로 남아있는 숫자의 숫자형 변환
        self.tokenized_notation = list(map(self.string_to_number,
                                           raw_notation.replace("  ", " ").split()))

    def infix_change(self):
        pass

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


if __name__ == '__main__':
    library = {
        "operator": ['+', '-', '*', '/', '^', '(', ')'],
        "function": ['exp', 'log', 'ln', 'sqrt',
                     'sin', 'cos', 'tan',
                     'asin', 'acos', 'atan']
    }
    string = "1+   2-12 * 3  -1 *4pi -3e"
    string = string.replace(" ", "")
    pre_trig = 0
    counter = 0
    stack_c = 0
    raw_notation = list()
    print(len(string))
    while len(string) > counter:
        for i in string:
            post_trig = 2
            if i in library["operator"]:
                post_trig = 1
            elif post_trig != 1 and i.isnumeric():
                post_trig = 0

            if counter == 0:
                if i == '-':
                    raw_notation.append(string[0:1])
                    counter += 2
                    pre_trig = 0
                    continue
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
    print(raw_notation)
