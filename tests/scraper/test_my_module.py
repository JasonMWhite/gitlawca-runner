import pytest
from scraper import my_module


class TestMyClass:

    @pytest.fixture
    def my_object(self) -> my_module.MyClass:
        return my_module.MyClass(10)

    def test_adds_constant(self, my_object: my_module.MyClass):
        assert my_object.add_constant(7) == 17

class TestMySubClass:

    @pytest.fixture
    def my_other_object(self) -> my_module.MySubClass:
        return my_module.MySubClass(10, 5)

    def test_adds_both_values(self, my_other_object: my_module.MySubClass):
        assert my_other_object.add_both_values() == 15

    def test_adds_constant(self, my_other_object: my_module.MySubClass):
        assert my_other_object.add_constant(2) == 12
