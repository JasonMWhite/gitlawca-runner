import astroid.test_utils
import pylint.testutils

from pylint_custom import multiple_import_checker


class TestMultipleImportChecker(pylint.testutils.CheckerTestCase):

    CHECKER_CLASS = multiple_import_checker.MultipleImportChecker

    def test_multiple_imports_raises_linter_error(self):
        root = astroid.builder.parse("""
        import sys
        from package.module import ClassName, function_name
        from other_package.other_module import SomethingElse
        """)
        class_name_node = root['ClassName']

        message = pylint.testutils.Message('multiple-import-items',
                                           node=class_name_node, args=class_name_node)

        with self.assertAddsMessages(message):
            self.walk(root)

    def test_no_multiple_imports_doesnt_raise_linter_error(self):
        root = astroid.builder.parse("""
        import sys
        from package.module import ClassName
        from other_package.other_module import SomethingElse
        """)

        with self.assertNoMessages():
            self.walk(root)
