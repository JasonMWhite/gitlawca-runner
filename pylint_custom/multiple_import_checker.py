import astroid
from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker
from pylint import lint


def register_checkers(linter: lint.PyLinter):
    """Register checkers."""
    linter.register_checker(MultipleImportChecker(linter))


class MultipleImportChecker(BaseChecker):
    __implements__ = (IAstroidChecker,)

    name = 'multiple-import-checker'

    msgs = {
        'C9900': ('%s imports multiple items in one import statement',
                  'multiple-import-items',
                  'Separate imports into one item per line.')
    }

    def visit_importfrom(self, node: astroid.ImportFrom):
        if len(node.names) > 1:
            self.add_message('multiple-import-items', args=node, node=node)
