import sys

class ERROR:
    def __init__(self):
        self.stack = []

    def dump(self, exit_code: int = 1):
        for error in self.stack:
            print(error)
        sys.exit(exit_code)

    def preprocessing_error(self, message: str = "", file: str = "", line: int = 1):
        self.stack.append(f"[{file}:{line}] Preprocessing Error: {message}")

    def lexing_error(self, message: str = "", file: str = "", line: int = 1):
        self.stack.append(f"[{file}:{line}] Lexical Error: {message}")

    def parsing_error(self, message: str = "", file: str = "", line: int = 1):
        self.stack.append(f"[{file}:{line}] Parsing Error: {message}")

    def semantic_error(self, message: str = "", file: str = "", line: int = 1):
        self.stack.append(f"[{file}:{line}] Semantic Error: {message}")

    def compiler_error(self, message: str = "", file: str = "", line: int = 1):
        self.stack.append(f"[{file}:{line}] Compiler Error: {message}")
