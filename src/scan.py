def mangle(namespace: str = "", identifier: str = "", generics: list[str] = [], watermark: str = ""):
    mangled = f"{watermark}"
    for generic in generics:
        mangled += generic
    mangled += f"_{namespace}_{identifier}"
    return mangled

class TEMPLATE_SEARCH:
    def __init__(self, template, ast: list, file: str = ""):
        self.ast = ast
        self.file = file
        self.template_types = []
        self.template = template

        for node in self.ast:
            self.scan(node)

    def scan(self, node):
        match node["kind"]:
            case "VariableDeclaration":
                self.scan_variable_declaration(node)
            case "FunctionDeclaration":
                self.scan_function_declaration(node)
            case "TemplateDeclaration":
                self.scan_template_declaration(node)
            case "IsStatement":
                self.scan_is_statement(node)
            case "LoopStatement":
                self.scan_loop_statement(node)
            case "IdentifierLiteral":
                self.scan_identifier_literal(node)
            case "CallExpression":
                self.scan_call_expression(node)
            case "BinaryExpression" | "AssignmentExpression":
                self.scan_binary_expression(node)
            case "UnaryExpression" | "DereferenceExpression":
                self.scan_unary_expression(node)
            case "IndexExpression" | "MemberExpression":
                self.scan_index_expression(node)
            case "ImplStatement":
                self.scan_impl_statement(node)
            case "StructDefenition":
                self.scan_struct_defenition(node)
            case "ArrayLiteral" | "StructLiteral":
                self.scan_array_literal(node)

    def scan_type(self, node):
        match node["kind"]:
            case "GenericType":
                if node["of"]["kind"] == "BaseType" and node["of"]["type"] == self.template:
                    self.template_types.append(*node["types"])
                if node["of"]["kind"] == "StructType" and node["of"]["name"] == self.template:
                    self.template_types.append(*node["types"])
                self.scan_type(node["of"])
            case "PointerType":
                self.scan_type(node["to"])
            case "ArrayType":
                self.scan_type(node["of"])
            case "StructType":
                for member in node["members"]:
                    self.scan_type(member)
            case "FunctionType":
                self.scan_type(node["return"])
                for param in node["params"]:
                    self.scan_type(param)

    def scan_variable_declaration(self, node):
        self.scan_type(node["type"])
        self.scan(node["value"])

    def scan_function_declaration(self, node):
        self.scan_type(node["return_type"])
        for param in node["params"]:
            self.scan_type(param["type"])
        for body_node in node["body"]:
            self.scan(body_node)

    def scan_template_declaration(self, node):
        self.scan(node["stmt"])

    def scan_is_statement(self, node):
        self.scan(node["condition"])
        for body_node in node["body"]:
            self.scan(body_node)

    def scan_loop_statement(self, node):
        for body_node in node["body"]:
            self.scan(body_node)
    
    def scan_binary_expression(self, node):
        self.scan(node["left"])
        self.scan(node["right"])

    def scan_unary_expression(self, node):
        if node["value"] == None:
            return
        self.scan(node["value"])

    def scan_impl_statement(self, node):
        self.scan(node["method"])

    def scan_array_literal(self, node):
        for element in node["elements"]:
            self.scan(element)

    def scan_call_expression(self, node):
        self.scan(node["function"])
        for arg in node["args"]:
            self.scan(arg)

    def scan_index_expression(self, node):
        self.scan(node["parent"])

    def scan_identifier_literal(self, node):
        if "generics" not in node:
            return

        if node["value"] == self.template:
            self.template_types.append(*node["generics"])

    def scan_struct_defenition(self, node):
        for member in node["members"]:
            self.scan_type(member["type"])