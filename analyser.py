import ast
import re
import os
import sys


class StaticCodeAnalyzerError(Exception):
    pass


class TooLongLineError(StaticCodeAnalyzerError):
    pass


class IndentError(StaticCodeAnalyzerError):
    pass


class UnnecessarySemicolonError(StaticCodeAnalyzerError):
    pass


class NotEnoughSpacesError(StaticCodeAnalyzerError):
    pass


class TODOFoundError(StaticCodeAnalyzerError):
    pass


class TooManyBlankLinesError(StaticCodeAnalyzerError):
    pass


class TooManySpacesError(StaticCodeAnalyzerError):
    pass


class NameCaseError(StaticCodeAnalyzerError):
    pass


class StaticCodeAnalyzer:

    def __init__(self, path_file: str):
        self.path_file = path_file
        self.__check_funcs = [
            self.__check_long,
            self.__check_indentation,
            self.__check_semicolon,
            self.__check_spaces,
            self.__check_todo_existing,
            self.__check_blank_lines,
            self.__check_class_declaration_spaces,
            self.__check_function_declaration_spaces
        ]
        self.__count_blank_lines_in_row = 0

    def run(self):
        with open(self.path_file, 'r') as f:
            tree = ast.parse(f.read())
            f.seek(0, 0)
            for number_line, line in enumerate(f, start=1):
                self.__check_errors(number_line, line)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self.__check_class_name(node)
            if isinstance(node, ast.FunctionDef):
                self.__check_function_name(node)
                self.__check_arguments(node)
                self.__check_function_variables(node)

    def __check_errors(self, number_line, line):
        for func in self.__check_funcs:
            try:
                func(line)
            except StaticCodeAnalyzerError as err:
                self.__print_error(self.path_file, number_line, err.args[0], err.args[1])

    @staticmethod
    def __print_error(file, number_line, code, error):
        print(f"{file}: Line {number_line}: {code} {error}")

    @staticmethod
    def __check_long(line: str):
        long = 79
        if len(line) > long:
            raise TooLongLineError("S001", "Too long")

    @staticmethod
    def __check_indentation(line: str):
        if line != "\n" and (len(line) - len(line.lstrip())) % 4:
            raise IndentError("S002", "Indentation is not a multiple of four")

    @staticmethod
    def __check_semicolon(line: str):
        parts_line = line.split("#")
        if parts_line[0].rstrip("\n").rstrip(" ").endswith(";"):
            raise UnnecessarySemicolonError("S003", "Unnecessary semicolon")

    @staticmethod
    def __check_spaces(line: str):
        if re.match(r"[^#]*[^ ]( ?#)", line):
            raise NotEnoughSpacesError("S004", "At least two spaces required before inline")

    @staticmethod
    def __check_todo_existing(line: str):
        if re.search(r"(?i)# *todo", line):
            raise TODOFoundError("S005", "TODO found")

    def __check_blank_lines(self, line: str):
        if line.strip() == "":
            self.__count_blank_lines_in_row += 1
        else:
            if self.__count_blank_lines_in_row > 2:
                self.__count_blank_lines_in_row = 0
                raise TooManyBlankLinesError("S006", "More than two blank lines preceding a code line")
            self.__count_blank_lines_in_row = 0

    @staticmethod
    def __check_class_declaration_spaces(line: str):
        match = re.match(r"class[ ]{2,}", line)
        if match:
            raise TooManySpacesError("S007", "Too many spaces after 'class'")

    @staticmethod
    def __check_function_declaration_spaces(line: str):
        if re.match(r"\s*def[ ]{2,}", line):
            raise TooManySpacesError("S007", "Too many spaces after 'def'")

    def __check_class_name(self, node: ast.ClassDef):
        if re.match(r"[^A-Z].*", node.name):
            self.__print_error(self.path_file, node.lineno, "S008", f"Class name '{node.name}' should use CamelCase")

    def __check_function_name(self, node: ast.FunctionDef):
        if re.match(r"[_]{,2}[^a-z_].*", node.name):
            self.__print_error(self.path_file, node.lineno, "S009", f"Function name '{node.name}' should use snake_case")

    def __check_arguments(self, node: ast.FunctionDef):
        names = [a.arg for a in node.args.args]
        for name in names:
            if re.match(r"[^a-z_].*", name):
                self.__print_error(self.path_file, node.lineno, "S010", f"Argument name '{name}' should be snake_case")
        for default in node.args.defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.__print_error(self.path_file, node.lineno, "S012", "The default argument value is mutable")

    def __check_function_variables(self, node: ast.FunctionDef):
        assignments = [a for a in node.body if isinstance(a, ast.Assign)]
        for child in assignments:
            variables = [a for a in child.targets if isinstance(a, ast.Name)]
            for var in variables:
                if re.match(r"^[a-z][a-z0-9]+(_[a-z0-9]+)*$", var.id) is None:
                    self.__print_error(self.path_file, var.lineno, "S011", f"Variable '{var.id}' in function should be snake_case")


if __name__ == "__main__":
    args = sys.argv
    input_path = args[1]

    def call_analyzer_error(path: str):
        error_checking = StaticCodeAnalyzer(path)
        error_checking.run()
        return None

    if os.path.isdir(input_path):
        for root, dirs, files in os.walk(input_path):
            for file_name in sorted(files):
                if file_name.endswith(".py") is False:
                    continue
                file_path = os.path.join(root, file_name)
                call_analyzer_error(file_path)
    else:
        call_analyzer_error(input_path)
