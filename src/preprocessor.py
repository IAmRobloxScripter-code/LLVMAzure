from error import *

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
                while len(self.characters) > 0 and self.at().isalnum():
                    instruction += self.characters.pop(0)
                self.skip_whitespace()
                if instruction == "defmacro":
                    identifier = ""
                    while len(self.characters) > 0 and self.at().isalnum():
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
                    if self.at() != ")":
                        self.error_class.preprocessing_error("Expected ')' at the end of macro defenition!", self.file, self.line)
                        self.error_class.dump()
                    else:
                        self.characters.pop(0)

                    self.macros[identifier] = body
                self.skip_whitespace()
            elif char.isalpha():
                identifier = ""
                while len(self.characters) > 0 and self.at().isalnum():
                    identifier += self.characters.pop(0)
                
                if identifier in self.macros:
                    self.processed += self.macros[identifier]
                    self.swaps = True
                else:
                    self.processed += identifier
            else:
                self.eat()
        