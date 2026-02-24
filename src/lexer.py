from error import *
from globals import *
import re

NUMBER_REGEX = re.compile(
    r"""
    ^
    (
        0[xX][0-9a-fA-F]+ |
        0[bB][01]+ |
        0[oO][0-7]+ |
        (?:        
            \d+(\.\d+)?      
            ([eE][+-]?\d+)?
        )
    )
    $
    """,
    re.VERBOSE,
)


def is_valid_number(number: str) -> bool:
    return bool(NUMBER_REGEX.match(number))


class LEXER:
    def __init__(self, source: str, file: str):
        self.tokens = []
        self.line = 1
        self.source = source
        self.characters = list(source)
        self.file = file
        self.error_class = ERROR()
        self.begin()
        if len(self.error_class.stack) > 0:
            self.error_class.dump()

    def make_token(self, value, kind="character"):
        return {"value": value, "kind": kind, "line": self.line}

    def at(self):
        return self.characters[0]

    def peek(self, count: int = 1):
        return self.characters[count]

    def eat(self):
        return self.characters.pop(0)

    def skip_whitespace(self):
        char = self.at()
        if char in (" ", "\t", "\r", "\n"):
            self.eat()
        if char in ("\n", "\r"):
            self.line += 1

    def push_token(self, token):
        self.tokens.append(token)

    def begin(self):
        while len(self.characters) > 0:
            char = self.at()
            self.skip_whitespace()
            if char in (" ", "\t", "\r", "\n"):
                continue
            if char == "(":
                self.push_token(self.make_token(self.eat()))
            elif char == ")":
                self.push_token(self.make_token(self.eat()))
            elif char == "[":
                self.push_token(self.make_token(self.eat()))
            elif char == "]":
                self.push_token(self.make_token(self.eat()))
            elif char == "{":
                self.push_token(self.make_token(self.eat()))
            elif char == "}":
                self.push_token(self.make_token(self.eat()))
            elif char == "+":
                self.push_token(self.make_token(self.eat()))
            elif char == ":":
                self.push_token(self.make_token(self.eat()))
            elif char == "-":
                if self.peek() == ">":
                    self.eat()
                    self.eat()
                    self.push_token(self.make_token("->"))
                    continue
                self.push_token(self.make_token(self.eat()))
            elif char == "*":
                self.push_token(self.make_token(self.eat()))
            elif char == "/":
                self.push_token(self.make_token(self.eat()))
            elif char == "&":
                self.push_token(self.make_token(self.eat()))
            elif char == "." and self.peek(1) == "." and self.peek(2) == ".":
                self.eat()
                self.eat()
                self.eat()
                self.push_token(self.make_token("...", "varadic"))
            elif char == ".":
                self.push_token(self.make_token(self.eat()))
            elif char == "#":
                self.eat()

                while len(self.characters) > 0 and self.at() not in ("\n", "\r"):
                    self.eat()
            elif char == "=":
                if self.peek() == "=":
                    self.eat()
                    self.eat()
                    self.push_token(self.make_token("=="))
                else:
                    self.push_token(self.make_token(self.eat()))
            elif char == ">":
                if self.peek() == "=":
                    self.eat()
                    self.eat()
                    self.push_token(self.make_token(">="))
                else:
                    self.push_token(self.make_token(self.eat()))
            elif char == "<":
                if self.peek() == "=":
                    self.eat()
                    self.eat()
                    self.push_token(self.make_token("<="))
                else:
                    self.push_token(self.make_token(self.eat()))
            elif char == "!":
                if self.peek() == "=":
                    self.eat()
                    self.eat()
                    self.push_token(self.make_token("!="))
                else:
                    self.push_token(self.make_token(self.eat()))
            elif char.isdigit():
                number = ""

                while len(self.characters) > 0 and (
                    self.at().isalnum() or self.at() == "."
                ):
                    number += self.eat()

                if not is_valid_number(number):
                    self.error_class.lexing_error(
                        "Invalid number!", self.file, self.line
                    )

                self.push_token(self.make_token(number, "number"))
            elif char in ('"', "`"):
                string = self.eat()
                while len(self.characters) > 0 and self.at() != char:
                    c = ""
                    if self.at() == "\\":
                        if self.peek(1) == "n":
                            self.eat()
                            self.eat()
                            c = "\n"
                        elif self.peek(1) == "t":
                            self.eat()
                            self.eat()
                            c = "\t"
                        elif self.peek(1) == "r":
                            self.eat()
                            self.eat()
                            c = "\r"
                        elif self.peek(1) == "0":
                            self.eat()
                            self.eat()
                            c = "\0"
                        else:
                            self.eat()
                            c = self.eat()
                    else:
                        c = self.eat()
                    string += c
                string += self.eat()
                self.push_token(self.make_token(string, "string"))
            elif char == "'":
                self.eat()
                c = ""
                if self.at() == "\\":
                    if self.peek(1) == "n":
                        self.eat()
                        self.eat()
                        c = "\n"
                    elif self.peek(1) == "t":
                        self.eat()
                        self.eat()
                        c = "\t"
                    elif self.peek(1) == "r":
                        self.eat()
                        self.eat()
                        c = "\r"
                    elif self.peek(1) == "0":
                        self.eat()
                        self.eat()
                        c = "\0"
                    else:
                        self.eat()
                        c = self.eat()
                else:
                    c = self.eat()
                self.push_token(self.make_token(c, "char"))
                if self.at() != "'":
                    self.error_class.lexing_error(
                        "Char literal must be 1 character long!", self.file, self.line
                    )
                    self.error_class.dump()
                self.eat()
            elif char.isalpha():
                identifier = ""
                while len(self.characters) > 0 and self.at().isalnum():
                    identifier += self.eat()
                if identifier in NATIVE_KEYWORDS:
                    self.push_token(self.make_token(identifier, "keyword"))
                elif identifier in NATIVE_TYPES:
                    self.push_token(self.make_token(identifier, "type"))
                else:
                    self.push_token(self.make_token(identifier, "identifier"))
            else:
                self.error_class.lexing_error(
                    f'Invalid character - "{self.at()}"', self.file, self.line
                )
                self.eat()
        self.push_token(self.make_token("EOF", "EOF"))
