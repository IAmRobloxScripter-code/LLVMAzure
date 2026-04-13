from error import *


class PARSER:
    def __init__(self, tokens: list, file: str = ""):
        self.file = file
        self.tokens = tokens
        self.error_class = ERROR()
        self.ast = []
        self.types = []
        self.defined_types = {}
        self.structs = {}
        while len(self.tokens) > 0 and self.at()["kind"] != "EOF":
            stmt = self.parse_stmt()
            if stmt:
                self.ast.append(stmt)

        if len(self.error_class.stack) > 0:
            self.error_class.dump()

    def get_number_kind(self, number: str = "0"):
        if number.lower().startswith("0x"):
            return "hex"
        elif number.lower().startswith("0o"):
            return "octal"
        elif number.lower().startswith("0b"):
            return "binary"
        else:
            return "decimal"

    def at(self):
        return self.tokens[0]

    def eat(self):
        return self.tokens.pop(0)

    def expect(self, value=None, kind=None):
        if value and kind:
            if self.at()["value"] == value and self.at()["kind"] == kind:
                return self.eat()
            else:
                self.error_class.parsing_error(
                    f"Expected [{value}, {kind}], got [{self.at()["value"], self.at()["kind"]}]!",
                    self.file,
                    self.at()["line"],
                )
                self.error_class.dump()
                return {}
        elif value and not kind:
            if self.at()["value"] == value:
                return self.eat()
            else:
                self.error_class.parsing_error(
                    f"Expected '{value}', got '{self.at()["value"]}'!",
                    self.file,
                    self.at()["line"],
                )
                self.error_class.dump()
                return {}
        elif not value and kind:
            if self.at()["kind"] == kind:
                return self.eat()
            else:
                self.error_class.parsing_error(
                    f"Expected '{kind}', got '{self.at()["kind"]}'!",
                    self.file,
                    self.at()["line"],
                )
                self.error_class.dump()
                return {}
        else:
            sys.exit(1)
            return {}

    def parse_expr(self):
        match self.at()["value"]:
            case _:
                return self.parse_primary()

    def parse_stmt_or_expr(self):
        if self.at()["value"] == "(":
            return self.parse_stmt()
        else:
            return self.parse_expr()

    def parse_keyword(self):
        keyword = self.at()["value"]
        match keyword:
            case "template":
                return self.parse_template()
            case "let":
                return self.parse_variable()
            case "struct":
                return self.parse_struct()
            case "is":
                return self.parse_is()
            case "loop":
                return self.parse_loop()
            case "fn":
                return self.parse_fn()
            case "ret":
                return self.parse_ret()
            case "declare":
                return self.parse_declare()
            case "stop" | "continue":
                token = self.eat()
                return {
                    "kind": "JumpStatement",
                    "value": token["value"],
                    "line": token["line"],
                }
            case "enum":
                return self.parse_enum()
            case "impl":
                return self.parse_impl()

    def parse_stmt(self):
        self.expect("(")
        node = None
        if self.at()["kind"] == "keyword":
            node = self.parse_keyword()
        elif self.at()["kind"] == "type":
            node = self.parse_explicit_type()
        else:
            match self.at()["value"]:
                case (
                    "+" | "-" | "*" | "/" | "==" | ">=" | "!=" | "<=" | "<" | ">" | "&"
                ):
                    node = self.parse_operation()
                case "{":
                    node = self.parse_struct_literal()
                case "[":
                    node = self.parse_array()
                case "(":
                    node = self.parse_call()
                case ".":
                    node = self.parse_index()
                case "=":
                    node = self.parse_assignment()
                case "->":
                    node = self.parse_struct_index()
                case ":":
                    node = self.parse_enum_index()
        self.expect(")")
        return node

    def parse_explicit_type(self):
        line = self.at()["line"]
        type = self.parse_type()
        value = self.parse_stmt_or_expr()
        return {
            "kind": "ExplicitConversionExpression",
            "type": type,
            "value": value,
            "line": line,
        }

    def parse_type(self):
        token = self.at()
        node = None
        if (
            token["kind"] == "type"
            or token["kind"] == "identifier"
            or token["value"] in self.types
        ):
            if token["value"] in self.structs:
                self.eat()
                node = {
                    "kind": "StructType",
                    "members": [],
                    "name": token["value"],
                    "line": token["line"],
                }

                for member in self.structs[token["value"]]:
                    node["members"].append(member["type"])
            elif token["value"] == "function":
                self.eat()
                self.expect("(")
                return_type = self.parse_type()
                params = []
                self.expect("(")
                while (
                    len(self.tokens) > 0
                    and self.at()["kind"] != "EOF"
                    and self.at()["value"] != ")"
                ):
                    if self.at()["kind"] == "varadic":
                        params.append(
                            {
                                "kind": "BaseType",
                                "type": "varadic",
                                "line": self.eat()["line"],
                            }
                        )
                    else:
                        params.append(self.parse_type())
                self.expect(")")
                self.expect(")")
                node = {
                    "kind": "FunctionType",
                    "return": return_type,
                    "params": params,
                    "line": token["line"],
                }
            elif token["value"] in self.types and token["value"] in self.defined_types:
                return self.defined_types[self.eat()["value"]]
            else:
                node = {
                    "kind": "BaseType",
                    "type": self.eat()["value"],
                    "line": token["line"],
                }
        elif token["value"] == "[":
            self.eat()
            size = None
            if self.at()["kind"] == "number":
                size_number = self.eat()
                number_kind = self.get_number_kind(size_number["value"])
                if number_kind == "decimal":
                    if len(size_number["value"]) > 1 and size_number["value"][1] == ".":
                        self.error_class.parsing_error(
                            f"Cannot use float as array size!",
                            self.file,
                            size_number["line"],
                        )
                        self.error_class.dump()
                    else:
                        size = int(size_number["value"], 10)
                elif number_kind == "hex":
                    size = int(size_number["value"], 16)
                elif number_kind == "binary":
                    size = int(size_number["value"], 2)
                elif number_kind == "octal":
                    size = int(size_number["value"], 8)
                else:
                    self.error_class.parsing_error(
                        f"Invalid number -> {size_number["value"]}",
                        self.file,
                        size_number["line"],
                    )
                    self.error_class.dump()
            self.expect("]")
            node = {
                "kind": "ArrayType",
                "of": self.parse_type(),
                "size": size,
                "line": token["line"],
            }
        elif token["value"] == "*":
            self.eat()
            node = {
                "kind": "PointerType",
                "to": self.parse_type(),
                "line": token["line"],
            }
        elif token["value"] == "(":
            self.eat()
            node = self.parse_type()
            self.expect(")")
        elif token["value"] == "<":
            line = self.eat()["line"]
            generics = []
            while (
                len(self.tokens) > 0
                and self.at()["kind"] != "EOF"
                and self.at()["value"] != ">"
            ):
                generics.append(self.parse_type())
            self.expect(">")
            node = {
                "kind": "GenericType",
                "types": generics,
                "of": self.parse_type(),
                "line": line,
            }
        else:
            self.error_class.parsing_error(
                f"Invalid type -> {self.at()["value"]}!", self.file, self.at()["line"]
            )
            self.error_class.dump()
        return node

    def parse_is(self):
        line = self.eat()["line"]
        condition = self.parse_stmt_or_expr()
        body = []
        while (
            len(self.tokens) > 0
            and self.at()["kind"] != "EOF"
            and self.at()["value"] != ")"
        ):
            body.append(self.parse_stmt())
        else_body = None

        if self.tokens[1]["value"] == "(" and self.tokens[2]["value"] == "else":
            else_body = []
            self.expect(")")
            self.eat()
            self.eat()
            while (
                len(self.tokens) > 0
                and self.at()["kind"] != "EOF"
                and self.at()["value"] != ")"
            ):
                else_body.append(self.parse_stmt())
        return {
            "kind": "IsStatement",
            "condition": condition,
            "body": body,
            "else_body": else_body,
            "line": line,
        }

    def parse_loop(self):
        line = self.eat()["line"]
        body = []
        while (
            len(self.tokens) > 0
            and self.at()["kind"] != "EOF"
            and self.at()["value"] != ")"
        ):
            body.append(self.parse_stmt())
        return {
            "kind": "LoopStatement",
            "body": body,
            "line": line,
        }

    def parse_variable(self):
        self.eat()
        identifier = self.expect(kind="identifier")
        type = self.parse_type()
        value = self.parse_stmt_or_expr()
        return {
            "kind": "VariableDeclaration",
            "name": identifier["value"],
            "type": type,
            "value": value,
            "line": identifier["line"],
        }

    def parse_fn(self):
        line = self.eat()["line"]
        identifier = self.expect(kind="identifier")["value"]
        return_type = self.parse_type()

        self.expect("(")
        params = []
        while (
            len(self.tokens) > 0
            and self.at()["kind"] != "EOF"
            and self.at()["value"] != ")"
        ):
            if self.at()["kind"] != "varadic":
                params_name = self.expect(kind="identifier")
                params_type = self.parse_type()
                param = {
                    "kind": "ParameterDeclaration",
                    "name": params_name["value"],
                    "type": params_type,
                    "line": params_name["line"],
                }
                params.append(param)
            else:
                line = self.eat()["line"]
                param = {
                    "kind": "ParameterDeclaration",
                    "name": "...",
                    "type": "varadic",
                    "line": line,
                }
                params.append(param)
        self.expect(")")
        body = []
        while (
            len(self.tokens) > 0
            and self.at()["kind"] != "EOF"
            and self.at()["value"] != ")"
        ):
            body.append(self.parse_stmt())
        return {
            "kind": "FunctionDeclaration",
            "name": identifier,
            "return_type": return_type,
            "params": params,
            "body": body,
            "line": line,
        }

    def parse_ret(self):
        line = self.eat()["line"]
        if self.at()["value"] == ")":
            return {"kind": "ReturnStatement", "value": None, "line": line}
        value = self.parse_stmt_or_expr()
        return {"kind": "ReturnStatement", "value": value, "line": line}

    def parse_operation(self):
        operator = self.eat()
        left = self.parse_stmt_or_expr()
        if self.at()["value"] == ")":
            return {
                "kind": "UnaryExpression",
                "operator": operator["value"],
                "value": left,
                "line": operator["line"],
            }
        right = self.parse_stmt_or_expr()
        return {
            "kind": "BinaryExpression",
            "operator": operator["value"],
            "left": left,
            "right": right,
            "line": operator["line"],
        }

    def parse_array(self):
        line = self.eat()["line"]
        if self.at()["value"] == "]":
            self.eat()
            elements = []
            while (
                len(self.tokens) > 0
                and self.at()["kind"] != "EOF"
                and self.at()["value"] != ")"
            ):
                elements.append(self.parse_stmt_or_expr())
            return {"kind": "ArrayLiteral", "elements": elements, "line": line}
        else:
            value = self.parse_stmt_or_expr()
            self.expect("]")
            return {"kind": "DereferenceExpression", "value": value, "line": line}

    def parse_struct_literal(self):
        line = self.eat()["line"]
        self.expect("}")
        elements = []
        while (
            len(self.tokens) > 0
            and self.at()["kind"] != "EOF"
            and self.at()["value"] != ")"
        ):
            elements.append(self.parse_stmt_or_expr())
        return {"kind": "StructLiteral", "elements": elements, "line": line}

    def parse_call(self):
        line = self.eat()["line"]
        self.expect(")")
        identifier = self.parse_stmt_or_expr()
        args = []
        while (
            len(self.tokens) > 0
            and self.at()["kind"] != "EOF"
            and self.at()["value"] != ")"
        ):
            args.append(self.parse_stmt_or_expr())
        return {
            "kind": "CallExpression",
            "function": identifier,
            "args": args,
            "line": line,
        }

    def parse_struct(self):
        line = self.eat()["line"]
        identifier = self.expect(kind="identifier")["value"]
        members = []
        while (
            len(self.tokens) > 0
            and self.at()["kind"] != "EOF"
            and self.at()["value"] != ")"
        ):
            member_line = self.expect("(")["line"]
            member_identifier = self.expect(kind="identifier")["value"]
            member_type = self.parse_type()
            self.expect(")")
            members.append(
                {
                    "kind": "MemberDeclaration",
                    "identifier": member_identifier,
                    "type": member_type,
                    "line": member_line,
                }
            )
        self.types.append(identifier)
        self.structs[identifier] = members
        return {
            "kind": "StructDeclaration",
            "identifier": identifier,
            "members": members,
            "line": line,
        }

    def parse_template(self):
        self.eat()
        position = len(self.types)
        count = 0
        types = []
        while (
            len(self.tokens) > 0
            and self.at()["kind"] != "EOF"
            and self.at()["kind"] == "identifier"
        ):
            type_identifier = self.expect(kind="identifier")["value"]
            types.append(type_identifier)
            self.types.append(type_identifier)
            count += 1

        self.expect("(")
        blueprints = []
        while (
            len(self.tokens) > 0
            and self.at()["kind"] != "EOF"
            and self.at()["value"] != ")"
        ):
            blueprints.append(self.parse_type())
        self.expect(")")

        # combinations = list(product(blueprints, repeat=len(types)))
        # for combo in combinations:
        #     mapping = dict(zip(types, combo))
        #     for blueprint, blueprint_type in mapping.items():
        #         self.defined_types[blueprint] = blueprint_type
        #     self.ast.append(self.parse_stmt())
        #     for blueprint in mapping.keys():
        #         del self.defined_types[blueprint]
        stmt = self.parse_stmt()
        for _ in range(count):
            self.types.pop(position)
        return {
            "kind": "TemplateDeclaration",
            "identifiers": types,
            "blueprints": blueprints,
            "stmt": stmt,
        }

    def parse_index(self):
        line = self.eat()["line"]
        parent = self.parse_stmt_or_expr()
        child_chain = []
        while (
            len(self.tokens) > 0
            and self.at()["kind"] != "EOF"
            and self.at()["value"] != ")"
        ):
            child_chain.append(self.parse_stmt_or_expr())
        return {
            "kind": "IndexExpression",
            "parent": parent,
            "child": child_chain,
            "line": line,
        }

    def parse_struct_index(self):
        line = self.eat()["line"]
        parent = self.parse_stmt_or_expr()
        child_chain = []
        while (
            len(self.tokens) > 0
            and self.at()["kind"] != "EOF"
            and self.at()["value"] != ")"
        ):
            child_chain.append(self.parse_stmt_or_expr())
        return {
            "kind": "MemberExpression",
            "parent": parent,
            "child": child_chain,
            "line": line,
        }

    def parse_declare(self):
        line = self.eat()["line"]
        stmt = self.parse_stmt()
        return {"kind": "DeclareForeignStatement", "stmt": stmt, "line": line}

    def parse_assignment(self):
        line = self.eat()["line"]
        left = self.parse_stmt_or_expr()
        right = self.parse_stmt_or_expr()
        return {
            "kind": "AssignmentExpression",
            "left": left,
            "right": right,
            "line": line,
        }

    def parse_enum(self):
        line = self.eat()["line"]
        identifier = self.expect(kind="identifier")["value"]
        enums = []
        while (
            len(self.tokens) > 0
            and self.at()["kind"] != "EOF"
            and self.at()["value"] != ")"
        ):
            enum_line = self.expect("(")["line"]
            enum_identifier = self.expect(kind="identifier")["value"]
            enum_types = []
            while (
                len(self.tokens) > 0
                and self.at()["kind"] != "EOF"
                and self.at()["value"] != ")"
            ):
                enum_types.append(self.parse_type())
            self.expect(")")
            enums.append(
                {
                    "kind": "EnumMemberDeclaration",
                    "identifier": enum_identifier,
                    "type": enum_types,
                    "line": enum_line,
                }
            )
        self.types.append(identifier)
        return {
            "kind": "EnumDeclaration",
            "identifier": identifier,
            "enums": enums,
            "line": line,
        }

    def parse_enum_index(self):
        line = self.eat()["line"]
        parent = self.expect(kind="identifier")["value"]
        child = self.expect(kind="identifier")["value"]
        constructor_values = []
        while (
            len(self.tokens) > 0
            and self.at()["kind"] != "EOF"
            and self.at()["value"] != ")"
        ):
            constructor_values.append(self.parse_stmt_or_expr())
        return {
            "kind": "EnumIndexExpression",
            "parent": parent,
            "child": child,
            "args": constructor_values,
            "line": line,
        }

    def parse_impl(self):
        line = self.eat()["line"]
        struct = self.parse_primary()
        function = self.parse_stmt()

        return {
            "kind": "ImplStatement",
            "struct": struct,
            "method": function,
            "line": line,
        }

    # def parse_namespace(self):
    #     line = self.eat()["line"]
    #     namespace = self.expect(kind="identifier")["value"]
    #     body = []

    #     while (
    #         len(self.tokens) > 0
    #         and self.at()["kind"] != "EOF"
    #         and self.at()["value"] != ")"
    #     ):
    #         body.append(self.parse_stmt())

    #     return {
    #         "kind": "NamespaceDeclaration",
    #         "name": namespace,
    #         "body": body,
    #         "line": line,
    #     }

    def parse_primary(self):
        token = self.at()
        match token["kind"]:
            case "number":
                number_kind = self.get_number_kind(token["value"])
                if number_kind == "decimal":
                    if len(token["value"]) > 1 and token["value"][1] == ".":
                        return {
                            "kind": "FloatLiteral",
                            "value": float(self.eat()["value"]),
                            "line": token["line"],
                        }
                    else:
                        return {
                            "kind": "IntegerLiteral",
                            "value": int(self.eat()["value"], 10),
                            "line": token["line"],
                        }
                elif number_kind == "hex":
                    return {
                        "kind": "HexLiteral",
                        "value": int(self.eat()["value"], 16),
                        "line": token["line"],
                    }
                elif number_kind == "binary":
                    return {
                        "kind": "BinaryLiteral",
                        "value": int(self.eat()["value"], 2),
                        "line": token["line"],
                    }
                elif number_kind == "octal":
                    return {
                        "kind": "OctalLiteral",
                        "value": int(self.eat()["value"], 8),
                        "line": token["line"],
                    }
                else:
                    self.error_class.parsing_error(
                        f"Invalid number -> {token["value"]}", self.file, token["line"]
                    )
                    self.error_class.dump()
            case "string":
                return {
                    "kind": "StringLiteral",
                    "value": self.eat()["value"],
                    "line": token["line"],
                }
            case "char":
                return {
                    "kind": "CharLiteral",
                    "value": ord(self.eat()["value"]),
                    "line": token["line"],
                }
            case "identifier":
                return {
                    "kind": "IdentifierLiteral",
                    "value": self.eat()["value"],
                    "line": token["line"],
                }
            case _:
                if self.at()["value"] == "<":
                    self.eat()
                    types = []
                    while len(self.tokens) > 0 and self.at()["value"] != ">":
                        types.append(self.parse_type())

                    self.expect(">")
                    return {
                        "kind": "IdentifierLiteral",
                        "generics": types,
                        "value": self.expect(kind="identifier")["value"],
                        "line": token["line"],
                    }

                self.error_class.parsing_error(
                    "Invalid primary expression!", self.file, token["line"]
                )
                self.error_class.dump()
                return {}
