class MyClass:

    def __init__(self, value: int) -> None:
        self._value = value

    def add_constant(self, constant: int) -> int:
        return self._value + constant

    def print_value(self) -> None:
        print("The value is: {}".format(self._value))


class MySubClass(MyClass):
    def __init__(self, first_value: int, second_value: int) -> None:
        self._other_value = second_value
        super(MySubClass, self).__init__(first_value)

    def add_both_values(self) -> int:
        return self._value + self._other_value
