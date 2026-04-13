def stringify_type(type, array_depth_checker=False):
    value = ""
    node = type
    array_depth = 0
    while node["kind"] != "BaseType":
        if node["kind"] == "ArrayType":
            value += "[]"
            if array_depth_checker and array_depth > 0 and node["size"] == None:
                return
            node = node["of"]
            array_depth += 1
        elif node["kind"] == "StructType":
            index = 0
            for member in node["members"]:
                value += stringify_type(member, array_depth_checker) + (
                    ", " if index != len(node["members"]) - 1 else ""
                )  # type: ignore
                index += 1
            break
        elif node["kind"] == "FunctionType":
            value += f"function({stringify_type(node["return"], array_depth_checker)}("
            for index, param in enumerate(node["params"]):
                if param == "varadic" or param["type"] == "varadic":
                    value += f"...{" " if index < len(node["params"]) - 1 else ""}"
                    continue
                value += f"{stringify_type(param, array_depth_checker)}{" " if index < len(node["params"]) - 1 else ""}"
            value += ")"
            break
        elif node["kind"] == "PointerType":
            value += "*"
            node = node["to"]
        elif node["kind"] == "GenericType":
            value += "<"
            index = 0
            for generic in node["generics"]:
                value += generic + ("" if index == len(node["generics"]) - 1 else " ")
                index += 1
            value += ">"
            node = node["of"]
    if "type" in node:
        value += node["type"]
    return value


def mangle(identifier: str = "", generics: list = [], watermark: str = ""):
    mangled = f"{watermark}"
    for generic in generics:
        if type(generic) == str:
            mangled += generic
        else:
            mangled += stringify_type(generic)  # type: ignore
    mangled += f"_{identifier}"
    return mangled


def mangle_with_llvm(identifier: str = "", generics: list = [], watermark: str = ""):
    mangled = f"{watermark}"
    for generic in generics:
        if type(generic) == str:
            mangled += generic
        else:
            mangled += str(generic)  # type: ignore
    mangled += f"_{identifier}"
    return mangled


# class TEMPLATE_SEARCH:
#     def __init__(self, template, ast: list, file: str = ""):
#         self.ast = ast
#         self.file = file
#         self.template_types = []
#         self.template = template

#         for node in self.ast:
#             self.scan(node)

#     def scan(self, node):
#         match node["kind"]:
#             case "VariableDeclaration":
#                 self.scan_variable_declaration(node)
#             case "FunctionDeclaration":
#                 self.scan_function_declaration(node)
#             case "TemplateDeclaration":
#                 self.scan_template_declaration(node)
#             case "IsStatement":
#                 self.scan_is_statement(node)
#             case "LoopStatement":
#                 self.scan_loop_statement(node)
#             case "IdentifierLiteral":
#                 self.scan_identifier_literal(node)
#             case "CallExpression":
#                 self.scan_call_expression(node)
#             case "BinaryExpression" | "AssignmentExpression":
#                 self.scan_binary_expression(node)
#             case "UnaryExpression" | "DereferenceExpression":
#                 self.scan_unary_expression(node)
#             case "IndexExpression" | "MemberExpression":
#                 self.scan_index_expression(node)
#             case "ImplStatement":
#                 self.scan_impl_statement(node)
#             case "StructDefenition":
#                 self.scan_struct_defenition(node)
#             case "ArrayLiteral" | "StructLiteral":
#                 self.scan_array_literal(node)

#     def scan_type(self, node):
#         match node["kind"]:
#             case "GenericType":
#                 if (
#                     node["of"]["kind"] == "BaseType"
#                     and node["of"]["type"] == self.template
#                 ):
#                     self.template_types.append(*node["types"])
#                 if (
#                     node["of"]["kind"] == "StructType"
#                     and node["of"]["name"] == self.template
#                 ):
#                     self.template_types.append(*node["types"])
#                 self.scan_type(node["of"])
#             case "PointerType":
#                 self.scan_type(node["to"])
#             case "ArrayType":
#                 self.scan_type(node["of"])
#             case "StructType":
#                 for member in node["members"]:
#                     self.scan_type(member)
#             case "FunctionType":
#                 self.scan_type(node["return"])
#                 for param in node["params"]:
#                     self.scan_type(param)

#     def scan_variable_declaration(self, node):
#         self.scan_type(node["type"])
#         self.scan(node["value"])

#     def scan_function_declaration(self, node):
#         self.scan_type(node["return_type"])
#         for param in node["params"]:
#             self.scan_type(param["type"])
#         for body_node in node["body"]:
#             self.scan(body_node)

#     def scan_template_declaration(self, node):
#         self.scan(node["stmt"])

#     def scan_is_statement(self, node):
#         self.scan(node["condition"])
#         for body_node in node["body"]:
#             self.scan(body_node)

#     def scan_loop_statement(self, node):
#         for body_node in node["body"]:
#             self.scan(body_node)

#     def scan_binary_expression(self, node):
#         self.scan(node["left"])
#         self.scan(node["right"])

#     def scan_unary_expression(self, node):
#         if node["value"] == None:
#             return
#         self.scan(node["value"])

#     def scan_impl_statement(self, node):
#         self.scan(node["method"])

#     def scan_array_literal(self, node):
#         for element in node["elements"]:
#             self.scan(element)

#     def scan_call_expression(self, node):
#         self.scan(node["function"])
#         for arg in node["args"]:
#             self.scan(arg)

#     def scan_index_expression(self, node):
#         self.scan(node["parent"])

#     def scan_identifier_literal(self, node):
#         if "generics" not in node:
#             return

#         if node["value"] == self.template:
#             self.template_types.append(*node["generics"])

#     def scan_struct_defenition(self, node):
#         for member in node["members"]:
#             self.scan_type(member["type"])
