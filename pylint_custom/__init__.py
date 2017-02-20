from pylint import lint

from pylint_custom import multiple_import_checker


def register(linter: lint.PyLinter):
    multiple_import_checker.register_checkers(linter)
