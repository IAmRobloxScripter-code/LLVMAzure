from error import *
import sys
import struct
import os
import re
from pathlib import Path

class PREPROCESSOR:
    def __init__(self, source: str, file: str = ""):
        self.file = file
        self.source = source
        self.characters = list(source)
        self.processed = self.source
        self.macros = {}
        self.macro_params = {}
        self.error_class = ERROR()
        self.line = 1
        self.swaps = False

        is_windows = sys.platform.startswith("win")

        if is_windows:
            is_64bit = struct.calcsize("P") * 8 == 64
            
            if is_64bit:
                self.macros["win32"] = "1"
                self.macros["win64"] = "1"
            else:
                self.macros["win32"] = "1"
        else:
            if os.name == "posix":
                self.macros["unix"] = "1"
            self.macros[sys.platform] = "1"

        while True:
            self.source = self.processed
            self.characters = list(self.source)
            self.processed = ""
            self.line = 1
            self.swaps = False
            self.begin()
            if self.swaps == False:
                break

    def at(self):
        return self.characters[0]

    def peek(self, count: int = 1):
        return self.characters[count]

    def eat(self):
        char = self.characters.pop(0)
        self.processed += char
        return char

    def skip_whitespace(self):
        while len(self.characters) > 0 and self.at() in (" ", "\t", "\r", "\n"):
            if self.at() in ("\r" "\n"):
                self.line += 1
            self.characters.pop(0)

    def begin(self):
        while len(self.characters) > 0:
            char = self.at()
            if char in ("\n", "\r"):
                self.line += 1
                self.eat()
                continue

            if char == "(" and self.peek() == "@":
                instruction = ""
                self.characters.pop(0)
                self.characters.pop(0)
                while len(self.characters) > 0 and (self.at().isalnum() or self.at() == "_"):
                    instruction += self.characters.pop(0)
                self.skip_whitespace()
                if instruction == "isdef":
                    self.skip_whitespace()
                    identifier = ""
                    while len(self.characters) > 0 and (self.at().isalnum() or self.at() == "_"):
                        identifier += self.characters.pop(0)
                    body = ""
                    depth = 1
                    while len(self.characters) > 0 and depth > 0:
                        if self.at() == "(":
                            depth += 1
                        elif self.at() == ")":
                            depth -= 1
                        if depth <= 0:
                            break
                        if self.at() in ("\n", "\r"):
                            self.line += 1
                        body += self.characters.pop(0)

                    self.skip_whitespace()
                    if len(self.characters) <= 0 or self.at() != ")":
                        self.error_class.preprocessing_error(
                            "Expected ')' at the end of is defined statement!",
                            self.file,
                            self.line,
                        )
                        self.error_class.dump()
                    else:
                        self.characters.pop(0)

                    self.skip_whitespace()
                    if len(self.characters) > 0 and self.at() == "(" and self.peek() == "@":
                        potential_else = ""
                        self.characters.pop(0)
                        self.characters.pop(0)
                        while (
                            len(self.characters) > 0
                            and self.at().isalnum()
                        ):
                            potential_else += self.characters.pop(0)

                        if potential_else == "iselse":
                            else_body = ""
                            else_depth = 1
                            while len(self.characters) > 0 and else_depth > 0:
                                if self.at() == "(":
                                    else_depth += 1
                                elif self.at() == ")":
                                    else_depth -= 1
                                if else_depth <= 0:
                                    break
                                if self.at() in ("\n", "\r"):
                                    self.line += 1
                                else_body += self.characters.pop(0)
                        else:
                            self.processed += f"@({potential_else}"

                        self.skip_whitespace()
                        if len(self.characters) <= 0 or self.at() != ")":
                            self.error_class.preprocessing_error(
                                f"Expected ')' at the end of {"else defenition" if potential_else == "else" else "preprocessing expression"}!",
                                self.file,
                                self.line,
                            )
                            self.error_class.dump()
                        else:
                            self.characters.pop(0)

                    if identifier in self.macros:
                        self.processed += body
                        self.swaps = True
                    else:
                        self.processed += else_body
                        self.swaps = True

                if instruction == "insert":
                    self.skip_whitespace()
                    path = ""
                    string_terminator = ""
                    if len(self.characters) <= 0 or self.at() not in ("\"", "'", "`"):
                        self.error_class.preprocessing_error(
                            f"Expected a string start at the start of insert path!",
                            self.file,
                            self.line,
                        )
                        self.error_class.dump()
                    else:
                        string_terminator = self.characters.pop(0)

                    while len(self.characters) > 0 and self.at() != string_terminator:
                        if self.at() in ("\n", "\r"):
                            self.line += 1
                        path += self.characters.pop(0)

                    if len(self.characters) <= 0 or self.at() != string_terminator:
                        self.error_class.preprocessing_error(
                            f"Expected a string terminator at the end of insert path!",
                            self.file,
                            self.line,
                        )
                        self.error_class.dump()
                    else:
                        self.characters.pop(0)
                    self.skip_whitespace()
                    if len(self.characters) <= 0 or self.at() != ")":
                        self.error_class.preprocessing_error(
                            f"Expected ')' at the end of insert!",
                            self.file,
                            self.line,
                        )
                        self.error_class.dump()
                    else:
                        self.characters.pop(0)
                    if not path.endswith(".az"):
                        path += ".az"
                    path_class = Path(path)
                    if path_class.exists() and path_class.is_file():
                        with open(path_class, "r") as inserted_file:
                            self.processed += f"{inserted_file.read()}"
                            inserted_file.close()
                        self.swaps = True
                    else:
                        self.error_class.preprocessing_error(
                            f"Invalid insert -> `{path}` does not exist or is not a valid file!",
                            self.file,
                            self.line,
                        )
                        self.error_class.dump()

                if instruction == "defmacro":
                    identifier = ""
                    
                    while len(self.characters) > 0 and (self.at().isalnum() or self.at() == "_"):
                        identifier += self.characters.pop(0)

                    if self.at() == "(":
                        symbols = []
                        self.characters.pop(0)
                        self.skip_whitespace()
                        while len(self.characters) > 0 and self.at() != ")":
                            param = ""
                            while len(self.characters) > 0 and (self.at().isalnum() or self.at() == "_"):
                                param += self.characters.pop(0)
                            symbols.append(param)
                            self.skip_whitespace()
                        if len(self.characters) <= 0 or self.at() != ")":
                            self.error_class.preprocessing_error(
                                f"Expected ')' at the end of macro parameter defenition!",
                                self.file,
                                self.line,
                            )
                            self.error_class.dump()
                        else:
                            self.characters.pop(0)
                        self.macro_params[identifier] = symbols

                    self.skip_whitespace()
                    body = ""
                    depth = 1
                    while len(self.characters) > 0 and depth > 0:
                        if self.at() == "(":
                            depth += 1
                        elif self.at() == ")":
                            depth -= 1
                        if depth <= 0:
                            break
                        if self.at() in ("\n", "\r"):
                            self.line += 1
                        body += self.characters.pop(0)

                    self.skip_whitespace()
                    if len(self.characters) <= 0 or self.at() != ")":
                        self.error_class.preprocessing_error(
                            "Expected ')' at the end of macro defenition!",
                            self.file,
                            self.line,
                        )
                        self.error_class.dump()
                    else:
                        self.characters.pop(0)

                    self.macros[identifier] = body
                self.skip_whitespace()
            elif char.isalpha() or char == "_":
                identifier = ""
                while len(self.characters) > 0 and (self.at().isalnum() or self.at() == "_"):
                    identifier += self.characters.pop(0)

                if identifier in self.macros:
                    macro = self.macros[identifier]
                    if self.at() == "(":
                        params = []
                        self.characters.pop(0)
                        while len(self.characters) > 0 and self.at() != ")":
                            self.skip_whitespace()
                            if len(self.characters) <= 0 or self.at() != "(":
                                self.error_class.preprocessing_error(
                                    "Expected '(' at the start of macro argument!",
                                    self.file,
                                    self.line,
                                )
                                self.error_class.dump()
                            else:
                                self.characters.pop(0)
                            param = ""
                            while len(self.characters) > 0 and self.at() != ")":
                                if self.at() in ("\n", "\r"):
                                    self.line += 1
                                param += self.characters.pop(0)
                            params.append(param)
                            if len(self.characters) <= 0 or self.at() != ")":
                                self.error_class.preprocessing_error(
                                    "Expected ')' at the end of macro argument!",
                                    self.file,
                                    self.line,
                                )
                                self.error_class.dump()
                            else:
                                self.characters.pop(0)
                        if len(self.characters) <= 0 or self.at() != ")":
                            self.error_class.preprocessing_error(
                                "Expected ')' at the end of macro arguments!",
                                self.file,
                                self.line,
                            )
                            self.error_class.dump()
                        else:
                            self.characters.pop(0)

                        if len(self.macro_params[identifier]) < len(params):
                            self.error_class.preprocessing_error(
                                "Too many arguments for macro arguments!",
                                self.file,
                                self.line,
                            )
                            self.error_class.dump()
                        elif len(self.macro_params[identifier]) > len(params):
                            self.error_class.preprocessing_error(
                                "Too few arguments for macro arguments!",
                                self.file,
                                self.line,
                            )
                            self.error_class.dump()
                        for index, param in enumerate(self.macro_params[identifier]):
                            pattern = rf"\b{re.escape(param)}\b"
                            macro = re.sub(pattern, params[index], macro)

                    self.processed += macro
                    self.swaps = True
                else:
                    self.processed += identifier
            else:
                self.eat()