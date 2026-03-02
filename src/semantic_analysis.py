from error import *


class SEMANTIC_ANALYSIS:
    def __init__(self, ast: list, file: str = ""):
        self.ast = ast
        self.file = file
        self.types = []
        self.structs = {}
        self.return_types = []
        self.stack_frame = []
        self.enums = {}
        self.operators = {
            "+": [
                {
                    "left": "u8",
                    "right": "u8",
                    "return": {"kind": "BaseType", "type": "u8"},
                },
                {
                    "left": "u16",
                    "right": "u16",
                    "return": {"kind": "BaseType", "type": "u16"},
                },
                {
                    "left": "u32",
                    "right": "u32",
                    "return": {"kind": "BaseType", "type": "u32"},
                },
                {
                    "left": "u64",
                    "right": "u64",
                    "return": {"kind": "BaseType", "type": "u64"},
                },
                {
                    "left": "i8",
                    "right": "i8",
                    "return": {"kind": "BaseType", "type": "i8"},
                },
                {
                    "left": "i16",
                    "right": "i16",
                    "return": {"kind": "BaseType", "type": "i16"},
                },
                {
                    "left": "i32",
                    "right": "i32",
                    "return": {"kind": "BaseType", "type": "i32"},
                },
                {
                    "left": "i64",
                    "right": "i64",
                    "return": {"kind": "BaseType", "type": "i64"},
                },
                {
                    "left": "f64",
                    "right": "f64",
                    "return": {"kind": "BaseType", "type": "f64"},
                },
                {
                    "left": "string",
                    "right": "string",
                    "return": {"kind": "BaseType", "type": "string"},
                },
            ],
            "-": [
                {
                    "left": "u8",
                    "right": "u8",
                    "return": {"kind": "BaseType", "type": "u8"},
                },
                {
                    "left": "u16",
                    "right": "u16",
                    "return": {"kind": "BaseType", "type": "u16"},
                },
                {
                    "left": "u32",
                    "right": "u32",
                    "return": {"kind": "BaseType", "type": "u32"},
                },
                {
                    "left": "u64",
                    "right": "u64",
                    "return": {"kind": "BaseType", "type": "u64"},
                },
                {
                    "left": "i8",
                    "right": "i8",
                    "return": {"kind": "BaseType", "type": "i8"},
                },
                {
                    "left": "i16",
                    "right": "i16",
                    "return": {"kind": "BaseType", "type": "i16"},
                },
                {
                    "left": "i32",
                    "right": "i32",
                    "return": {"kind": "BaseType", "type": "i32"},
                },
                {
                    "left": "i64",
                    "right": "i64",
                    "return": {"kind": "BaseType", "type": "i64"},
                },
                {
                    "left": "f64",
                    "right": "f64",
                    "return": {"kind": "BaseType", "type": "f64"},
                },
            ],
            "*": [
                {
                    "left": "u8",
                    "right": "u8",
                    "return": {"kind": "BaseType", "type": "u8"},
                },
                {
                    "left": "u16",
                    "right": "u16",
                    "return": {"kind": "BaseType", "type": "u16"},
                },
                {
                    "left": "u32",
                    "right": "u32",
                    "return": {"kind": "BaseType", "type": "u32"},
                },
                {
                    "left": "u64",
                    "right": "u64",
                    "return": {"kind": "BaseType", "type": "u64"},
                },
                {
                    "left": "i8",
                    "right": "i8",
                    "return": {"kind": "BaseType", "type": "i8"},
                },
                {
                    "left": "i16",
                    "right": "i16",
                    "return": {"kind": "BaseType", "type": "i16"},
                },
                {
                    "left": "i32",
                    "right": "i32",
                    "return": {"kind": "BaseType", "type": "i32"},
                },
                {
                    "left": "i64",
                    "right": "i64",
                    "return": {"kind": "BaseType", "type": "i64"},
                },
                {
                    "left": "f64",
                    "right": "f64",
                    "return": {"kind": "BaseType", "type": "f64"},
                },
            ],
            "/": [
                {
                    "left": "u8",
                    "right": "u8",
                    "return": {"kind": "BaseType", "type": "u8"},
                },
                {
                    "left": "u16",
                    "right": "u16",
                    "return": {"kind": "BaseType", "type": "u16"},
                },
                {
                    "left": "u32",
                    "right": "u32",
                    "return": {"kind": "BaseType", "type": "u32"},
                },
                {
                    "left": "u64",
                    "right": "u64",
                    "return": {"kind": "BaseType", "type": "u64"},
                },
                {
                    "left": "i8",
                    "right": "i8",
                    "return": {"kind": "BaseType", "type": "i8"},
                },
                {
                    "left": "i16",
                    "right": "i16",
                    "return": {"kind": "BaseType", "type": "i16"},
                },
                {
                    "left": "i32",
                    "right": "i32",
                    "return": {"kind": "BaseType", "type": "i32"},
                },
                {
                    "left": "i64",
                    "right": "i64",
                    "return": {"kind": "BaseType", "type": "i64"},
                },
                {
                    "left": "f64",
                    "right": "f64",
                    "return": {"kind": "BaseType", "type": "f64"},
                },
            ],
        }
        self.error_class = ERROR()
        for node in self.ast:
            self.analyze(node)
        if len(self.error_class.stack) > 0:
            self.error_class.dump()

    def analyze(self, node):
        match node["kind"]:
            case "VariableDeclaration":
                self.analyze_variable_declaration(node)
            case "FunctionDeclaration":
                self.analyze_function_declaration(node)
            case "StructDeclaration":
                self.analyze_struct_declaration(node)
            case "CallExpression":
                self.analyze_call_expression(node)
            case "BinaryExpression" | "DereferenceExpression" | "UnaryExpression":
                self.build_type_from_expr(node)
            case "DeclareForeignStatement":
                self.analyze_declare_foreign_statement(node)
            case "EnumDeclaration":
                self.analyze_enum_declaration(node)
            case "IsStatement":
                self.analyze_is_statement(node)
            case "LoopStatement":
                self.analyze_loop_statement(node)
            case "ImplStatement":
                self.analyze_impl_statement(node)

    def is_return_type(self, type, function_name):
        for data in self.return_types:
            if data["name"] == function_name and self.stringify_type(
                data["return_type"]
            ) == self.stringify_type(type):
                return True
        return False

    def get_return_type(self, function_name):
        for data in self.return_types:
            if data["name"] == function_name:
                return data["return_type"]
        return None

    def stringify_type(self, type, array_depth_checker=False):
        value = ""
        node = type
        array_depth = 0
        while node["kind"] != "BaseType":
            if node["kind"] == "ArrayType":
                value += "[]"
                if array_depth_checker and array_depth > 0 and node["size"] == None:
                    self.error_class.semantic_error(
                        f"Multi-dimensional array requires all inner elements to have a specified length.",
                        self.file,
                        node["line"],
                    )
                node = node["of"]
                array_depth += 1
            elif node["kind"] == "StructType":
                index = 0
                for member in node["members"]:
                    value += self.stringify_type(member, array_depth_checker) + (
                        ", " if index != len(node["members"]) - 1 else ""
                    )
                    index += 1
                break
            elif node["kind"] == "FunctionType":
                value += f"function({self.stringify_type(node["return"], array_depth_checker)}("
                for index, param in enumerate(node["params"]):
                    if param == "varadic" or param["type"] == "varadic":
                        value += f"...{" " if index < len(node["params"]) - 1 else ""}"
                        continue
                    value += f"{self.stringify_type(param, array_depth_checker)}{" " if index < len(node["params"]) - 1 else ""}"
                value += ")"
                break
            elif node["kind"] == "PointerType":
                value += "*"
                node = node["to"]
            elif node["kind"] == "GenericType":
                value += "<"
                index = 0
                for generic in node["generics"]:
                    value += generic + (
                        "" if index == len(node["generics"]) - 1 else " "
                    )
                    index += 1
                value += ">"
                node = node["of"]
        if "type" in node:
            value += node["type"]
        return value

    def implicit_int_conversion(self, type_t, type_v):
        current_t = type_t
        current_v = type_v

        while current_t["kind"] != "BaseType":
            if current_t["kind"] == "ArrayType":
                if "of" not in current_v:
                    return
                current_v = current_v["of"]
                current_t = current_t["of"]
            elif current_t["kind"] == "StructType":
                for index in range(len(current_t["members"])):
                    self.implicit_int_conversion(
                        current_t["members"][index], current_v["members"][index]
                    )
                break
            elif current_t["kind"] == "PointerType":
                if "to" not in current_v:
                    return
                current_v = current_v["to"]
                current_t = current_t["to"]
            elif current_t["kind"] == "FunctionType":
                break
            elif current_t["kind"] == "GenericType":
                if "of" not in current_v:
                    return
                current_v = current_v["of"]
                current_t = current_t["of"]

        if "type" not in current_v:
            return
        if current_t["type"] in (
            "u8",
            "u16",
            "u32",
            "u64",
            "i8",
            "i16",
            "i32",
            "i64",
        ) and current_v["type"] in (
            "u8",
            "u16",
            "u32",
            "u64",
            "i8",
            "i16",
            "i32",
            "i64",
        ):
            current_v["type"] = current_t["type"]

    def is_operator_compatible(self, operator, left, right):
        s_left = self.stringify_type(left)
        s_right = self.stringify_type(right)

        for data in self.operators[operator]:
            if data["left"] == s_left and data["right"] == s_right:
                return True

        return False

    def get_return_type_from_operator(self, operator, left, right):
        s_left = self.stringify_type(left)
        s_right = self.stringify_type(right)

        for data in self.operators[operator]:
            if data["left"] == s_left and data["right"] == s_right:
                return data["return"]

        return None

    def build_type_from_expr(self, node):
        stack_frame = self.stack_frame[len(self.stack_frame) - 1]
        result = None
        if node["kind"] == "IdentifierLiteral":
            is_func = False
            for data in self.return_types:
                if data["name"] == node["value"]:
                    result = {"kind": "PointerType", "to": data["type"]}
                    is_func = True
                    break
            if not is_func:
                result = stack_frame["variables"][node["value"]]["type"]
        elif node["kind"] == "CallExpression":
            result = self.build_type_from_expr(node["function"])["to"]["return"]  # type: ignore
        elif node["kind"] == "DereferenceExpression":
            expr = self.build_type_from_expr(node["value"])
            if "to" not in expr:
                self.error_class.semantic_error(
                    f"Cannot dereference '{self.stringify_type(expr)}'!",
                    self.file,
                    node["line"],
                )
                self.error_class.dump()
            result = expr["to"]  # type: ignore
        elif node["kind"] == "ArrayLiteral":
            result = {
                "kind": "ArrayType",
                "of": self.build_type_from_expr(node["elements"][0]),
            }
        elif node["kind"] == "StructLiteral":
            result = {"kind": "StructType", "members": []}

            for member in node["elements"]:
                result["members"].append(self.build_type_from_expr(member))
        elif node["kind"] == "ExplicitConversionExpression":
            result = node["type"]
        elif node["kind"] == "BinaryExpression":
            left_type = self.build_type_from_expr(node["left"])
            right_type = self.build_type_from_expr(node["right"])
            if not self.is_operator_compatible(node["operator"], left_type, right_type):
                self.error_class.semantic_error(
                    f"No operator '{node["operator"]}' for {self.stringify_type(left_type)} and {self.stringify_type(right_type)}!",
                    self.file,
                    node["line"],
                )
                self.error_class.dump()
            result = self.get_return_type_from_operator(
                node["operator"], left_type, right_type
            )
        elif node["kind"] == "EnumIndexExpression":
            result = {"kind": "BaseType", "type": node["parent"]}
        elif node["kind"] == "UnaryExpression":
            if node["operator"] == "-":
                result = self.build_type_from_expr(node["value"])
            elif node["operator"] == "&":
                result = {
                    "kind": "PointerType",
                    "to": self.build_type_from_expr(node["value"]),
                }
            else:
                self.error_class.semantic_error(
                    f"Invalid unary operator -> '{node["operator"]}'!",
                    self.file,
                    node["line"],
                )
                self.error_class.dump()
        elif node["kind"] == "IndexExpression":
            parent = self.build_type_from_expr(node["parent"])
            for index in node["child"]:
                if parent["kind"] != "ArrayType":
                    self.error_class.semantic_error(
                        f"Cannot index non-array type!",
                        self.file,
                        node["line"],
                    )
                    self.error_class.dump()
                child = self.build_type_from_expr(index)
                if child["type"] not in (
                    "u8",
                    "u16",
                    "u32",
                    "u64",
                    "i8",
                    "i16",
                    "i32",
                    "i64",
                ):
                    self.error_class.semantic_error(
                        f"Cannot index array with a non-integer value.",
                        self.file,
                        node["line"],
                    )
                    self.error_class.dump()
                parent = child
            result = parent["of"]
        elif node["kind"] == "MemberExpression":
            parent = self.build_type_from_expr(node["parent"])
            if parent["kind"] != "StructType":
                self.error_class.semantic_error(
                    f"Cannot access members of a non-struct type!",
                    self.file,
                    node["line"],
                )
                self.error_class.dump()
            data = self.structs[parent["name"]]  # type: ignore
            result = data["members"]
            for child in node["child"]:
                if child["value"] not in result:
                    self.error_class.semantic_error(
                        f"{child["value"]} is not a member of struct '{parent["name"]}'!",
                        self.file,
                        node["line"],
                    )
                    self.error_class.dump()
                result = result[child["value"]]

            return result
        elif node["kind"] in (
            "IntegerLiteral",
            "HexLiteral",
            "BinaryLiteral",
            "OctalLiteral",
        ):
            result = {"kind": "BaseType", "type": "i32"}
        elif node["kind"] == "FloatLiteral":
            result = {"kind": "BaseType", "type": "f32"}
        elif node["kind"] == "CharLiteral":
            result = {"kind": "BaseType", "type": "u8"}
        elif node["kind"] == "StringLiteral":
            result = {"kind": "BaseType", "type": "string"}
        else:
            self.error_class.semantic_error(
                f"Invalid type!",
                self.file,
                node["line"],
            )
            self.error_class.dump()
        return result

    def analyze_variable_declaration(self, node):
        stack_frame = self.stack_frame[len(self.stack_frame) - 1]
        if node["value"] == None:
            self.error_class.semantic_error(
                f"No value assigned to variable!",
                self.file,
                node["line"],
            )
            self.error_class.dump()
        self.analyze(node["value"])
        type = node["type"]
        value_type = self.build_type_from_expr(node["value"])

        if value_type == None:
            self.error_class.semantic_error(
                f"Invalid type!",
                self.file,
                node["line"],
            )
            self.error_class.dump()
        self.implicit_int_conversion(type, value_type)
        s_type = self.stringify_type(type, True)
        s_value_type = self.stringify_type(value_type)
        if s_type != s_value_type:
            self.error_class.semantic_error(
                f"Mismatch between type and value -> Type is '{s_type}', while value is '{s_value_type}'!",
                self.file,
                node["line"],
            )
        stack_frame["variables"][node["name"]] = {
            "name": node["name"],
            "type": node["type"],
        }

    def analyze_function_declaration(self, node):
        self.stack_frame.append(
            {
                "kind": "function",
                "name": node["name"],
                "variables": {},
            }
        )

        function_type = {
            "kind": "FunctionType",
            "return": node["return_type"],
            "params": [],
            "name": node["name"],
        }

        for param in node["params"]:
            function_type["params"].append(param["type"])

        self.return_types.append(
            {
                "name": node["name"],
                "params": node["params"],
                "return_type": node["return_type"],
                "type": function_type,
            }
        )

        for body_node in node["body"]:
            self.analyze(body_node)

        self.stack_frame.pop()

    def analyze_struct_declaration(self, node):
        struct_data = {"name": node["identifier"], "members": {}}

        for member in node["members"]:
            struct_data["members"][member["identifier"]] = member["type"]
        self.structs[node["identifier"]] = struct_data

    def analyze_call_expression(self, node):
        fn: dict = self.build_type_from_expr(node["function"])["to"]  # type: ignore
    
        if fn == None:
            self.error_class.semantic_error(
                f"'{fn["name"]}' is not a function!",
                self.file,
                node["line"],
            )
            self.error_class.dump()

        less_args_count = len(fn["params"])
        if node["function"]["kind"] == "MemberExpression":
            less_args_count -= 1
        if (
            fn["params"][len(fn["params"]) - 1] == "varadic"
        ):
            less_args_count -= 1

        if less_args_count > len(node["args"]):
            self.error_class.semantic_error(
                f"Too few arguments while calling '{fn["name"]}'!",
                self.file,
                node["line"],
            )
            self.error_class.dump()
        elif (
            fn["params"][len(fn["params"]) - 1] != "varadic"
        ) and len(fn["params"]) < len(node["args"]):
            self.error_class.semantic_error(
                f"Too many arguments while calling '{fn["name"]}'!",
                self.file,
                node["line"],
            )
            self.error_class.dump()
        # for param in fn["params"]:
        #     pass

    def analyze_declare_foreign_statement(self, node):
        if node["stmt"]["kind"] == "VariableDeclaration":
            stack_frame = self.stack_frame[len(self.stack_frame) - 1]
            self.stringify_type(node["stmt"]["type"], True)
            stack_frame["variables"][node["stmt"]["name"]] = {
                "name": node["name"],
                "type": node["type"],
            }
        elif node["stmt"]["kind"] == "FunctionDeclaration":
            function_type = {
                "kind": "FunctionType",
                "return": node["stmt"]["return_type"],
                "params": [],
                "name": node["stmt"]["name"],
            }

            for param in node["stmt"]["params"]:
                function_type["params"].append(param["type"])

            self.return_types.append(
                {
                    "name": node["stmt"]["name"],
                    "params": node["stmt"]["params"],
                    "return_type": node["stmt"]["return_type"],
                    "type": function_type,
                }
            )
        else:
            self.error_class.semantic_error(
                f"Invalid expression!",
                self.file,
                node["line"],
            )

    def analyze_enum_declaration(self, node):
        self.enums[node["identifier"]] = node["enums"]

    def analyze_is_statement(self, node):
        for body_node in node["body"]:
            self.analyze(body_node)

    def analyze_loop_statement(self, node):
        for body_node in node["body"]:
            self.analyze(body_node)

    def analyze_impl_statement(self, node):
        """
        {
            "kind": "ImplStatement",
            "struct": struct,
            "method": function,
            "line": line
        }
        """

        if node["struct"] not in self.structs:
            self.error_class.semantic_error(
                f"Cannot assign method to '{node["struct"]}' because it is not a struct!",
                self.file,
                node["line"],
            )
            self.error_class.dump()

        if node["method"]["kind"] != "FunctionDeclaration":
            self.error_class.semantic_error(
                "Invalid method expression -> method must be a function!",
                self.file,
                node["line"],
            )
            self.error_class.dump()

        self.stack_frame.append(
            {
                "kind": "function",
                "name": node["method"]["name"],
                "variables": {},
            }
        )
        for body_node in node["method"]["body"]:
            self.analyze(body_node)

        self.stack_frame.pop()
        function_type = {
            "kind": "FunctionType",
            "return": node["method"]["return_type"],
            "params": [],
            "name": node["method"]["name"],
        }

        for param in node["method"]["params"]:
            function_type["params"].append(param["type"])

        self.structs[node["struct"]]["members"][node["method"]["name"]] = {"kind": "PointerType", "to": function_type}
        