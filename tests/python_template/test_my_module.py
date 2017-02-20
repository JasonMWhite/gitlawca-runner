import pytest
from python_template import my_module


@pytest.fixture
def my_object() -> my_module.MyClass:
    return my_module.MyClass()


def test_adds_one(my_object: my_module.MyClass):
    assert my_object.add_one(7) == 8
