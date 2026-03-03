from error import *
import sys
import struct
import os

class PREPROCESSOR:
    def __init__(self, source: str, file: str = ""):
        self.file = file
        self.source = source
        self.characters = list(source)
        self.processed = self.source
        self.macros = {}
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
            self.characters = list(self.processed)
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
                    else:
                        self.processed += else_body

                if instruction == "defmacro":
                    identifier = ""
                    
                    while len(self.characters) > 0 and (self.at().isalnum() or self.at() == "_"):
                        identifier += self.characters.pop(0)

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
                    self.processed += self.macros[identifier]
                    self.swaps = True
                else:
                    self.processed += identifier
            else:
                self.eat()