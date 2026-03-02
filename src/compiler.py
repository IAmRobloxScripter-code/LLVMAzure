import sys

from error import *
from llvmlite import ir, binding
import ctypes
import os


class COMPILER:
    def __init__(self, ast: list, file: str = ""):
        self.ast = ast
        self.file = file
        self.structs = {}
        self.stack = []
        self.context = []
        self.strings = {}
        self.functions = {}
        self.enums = {}
        self.module = None
        self.if_count = 0
        self.loop_count = 0
        self.error_class = ERROR()
        self.llvm_base_types = {
            "u8": ir.IntType(8),
            "u16": ir.IntType(16),
            "u32": ir.IntType(32),
            "u64": ir.IntType(64),
            "i8": ir.IntType(8),
            "i16": ir.IntType(16),
            "i32": ir.IntType(32),
            "i64": ir.IntType(64),
            "f32": ir.FloatType(),
            "f64": ir.DoubleType(),
            "bool": ir.IntType(1),
            "string": ir.IntType(8).as_pointer(),
            "void": ir.VoidType(),
        }

        self.init_bindings()
        self.create_module(file)

        for node in self.ast:
            self.compile_stmt(node)

        if len(self.error_class.stack) > 0:
            self.error_class.dump()

    def emit_obj(self, name):
        llvm_module = binding.parse_assembly(str(self.module))
        llvm_module.verify()

        target_triple = binding.get_default_triple()
        target = binding.Target.from_triple(target_triple)
        target_machine = target.create_target_machine(codemodel="default")
        obj = target_machine.emit_object(llvm_module)

        extension = ".obj" if sys.platform == "win32" else ".o"
        os.makedirs("_azure_temp_", exist_ok=True)
        obj_path = os.path.join(
            "_azure_temp_", os.path.splitext(os.path.basename(name))[0] + extension
        )
        with open(obj_path, "wb") as f:
            f.write(obj)
            f.close()
        return obj_path

    def init_bindings(self):
        binding.initialize_native_target()
        binding.initialize_native_asmprinter()

    def create_module(self, name: str = "main"):
        self.module = ir.Module(name=name)
        self.module.triple = binding.get_default_triple()
        self.module.data_layout = binding.Target.from_default_triple().create_target_machine(codemodel="default").target_data  # type: ignore

    def get_context(self):
        if len(self.context) > 0:
            return self.context[len(self.context) - 1]
        else:
            return None

    def compile_type(self, node, value=None):
        if node["kind"] == "BaseType":
            return self.llvm_base_types[node["type"]]
        elif node["kind"] == "PointerType":
            inner = self.compile_type(node["to"], value)
            return inner.as_pointer()
        elif node["kind"] == "ArrayType":
            element = self.compile_type(node["of"], value)
            if node["size"] == None:
                if value and "elements" in value:
                    return ir.ArrayType(element, len(value["elements"]))
                else:
                    return element.as_pointer()
            else:
                return ir.ArrayType(element, node["size"])
        elif node["kind"] == "StructType":
            return self.structs[node["name"]]["type"]
        elif node["kind"] == "FunctionType":
            return_type = self.compile_type(node["return"])
            param_types = []
            var_args = False
            for param in node["params"]:
                if param == "varadic" or param["type"] == "varadic":
                    var_args = True
                    break
                param_types.append(self.compile_type(param))
    
            return ir.FunctionType(return_type, param_types, var_arg=var_args)
        else:
            self.error_class.compiler_error("Uknown type!", self.file, node["line"])
            self.error_class.dump()

    def get_current_stack_frame(self, line: int = 1):
        if len(self.stack) > 0:
            return self.stack[len(self.stack) - 1]
        else:
            self.error_class.compiler_error(
                "Cannot declare variable outside of a scope!", self.file, line
            )
            self.error_class.dump()

    def compile_stmt(self, node):
        match node["kind"]:
            case "VariableDeclaration":
                return self.compile_variable(node)
            case "FunctionDeclaration":
                return self.compile_function(node)
            case "BinaryExpression":
                return self.compile_binary(node)
            case "IntegerLiteral" | "HexLiteral" | "OctalLiteral" | "BinaryLiteral":
                context = self.get_context()
                if context and (
                    "VariableDeclaration" in context["kind"]
                    or "TypeCast" in context["kind"]
                ):
                    return ir.Constant(context["type"], node["value"])
                else:
                    return ir.Constant(ir.IntType(32), node["value"])
            case "IdentifierLiteral":
                stack_frame = self.get_current_stack_frame(node["line"])
                context = self.get_context()
                if node["value"] in self.functions:
                    return self.functions[node["value"]]

                if context != None and "ReturnPointerVariable" in context["kind"]:
                    return stack_frame["variables"][node["value"]]["memory"]
                return stack_frame["builder"].load(
                    stack_frame["variables"][node["value"]]["memory"]
                )
            case "StringLiteral":
                return self.compile_string(node)
            case "ArrayLiteral":
                return self.compile_array(node)
            case "DeclareForeignStatement":
                return self.compile_declare_foreign(node)
            case "CallExpression":
                return self.compile_call(node)
            case "IndexExpression":
                return self.compile_index_expression(node)
            case "UnaryExpression":
                return self.compile_unary_expression(node)
            case "DereferenceExpression":
                return self.compile_dereference(node)
            case "AssignmentExpression":
                return self.compile_assignment(node)
            case "IsStatement":
                return self.compile_is(node)
            case "LoopStatement":
                return self.compile_loop(node)
            case "JumpStatement":
                return self.compile_break_continue(node)
            case "StructDeclaration":
                return self.compile_struct(node)
            case "StructLiteral":
                return self.compile_struct_literal(node)
            case "MemberExpression":
                return self.compile_struct_index(node)
            case "EnumDeclaration":
                return self.compile_enum(node)
            case "EnumIndexExpression":
                return self.compile_enum_index(node)

    def retrieve_basic_type(self, node):
        if node["kind"] == "BaseType":
            return node["type"]
        elif node["kind"] == "ArrayType" or node["kind"] == "GenericType":
            return self.retrieve_basic_type(node["of"])
        elif node["kind"] == "PointerType":
            return self.retrieve_basic_type(node["to"])
        elif node["kind"] == "StructType":
            return node

    def compile_variable(self, node):
        stack_frame = self.get_current_stack_frame(node["line"])
        variable_type = self.compile_type(node["type"], node["value"])
        self.context.append(
            {"kind": "VariableDeclaration", "type": variable_type, "raw": node["type"]}
        )
        stack_frame["variables"][node["name"]] = {
            "memory": stack_frame["builder"].alloca(variable_type, name=node["name"]),
            "type": node["type"],
        }
        value = self.compile_stmt(node["value"])
        stack_frame["builder"].store(
            value, stack_frame["variables"][node["name"]]["memory"]
        )
        self.context.pop()

    def compile_function(self, node):
        return_type = self.compile_type(node["return_type"])
        params = []
        for param in node["params"]:
            params.append(self.compile_type(param["type"]))

        func_type = ir.FunctionType(return_type, params)
        main_func = ir.Function(self.module, func_type, name=node["name"])
        param_index = 0
        variables = {}
        for param in node["params"]:
            main_func.args[param_index].name = param["name"]
            param_index += 1

        block = main_func.append_basic_block(name="entry")
        builder = ir.IRBuilder(block)
        for index, param in enumerate(node["params"]):
            variables[param["name"]] = {
                "memory": main_func.args[index],
                "type": param["type"],
            }
        
        self.functions[node["name"]] = main_func
        self.stack.append({"builder": builder, "variables": variables})

        for body_node in node["body"]:
            self.compile_stmt(body_node)

        if (
            len(node["body"]) == 0
            or node["body"][len(node["body"]) - 1]["kind"] != "ReturnExpression"
        ):
            if isinstance(return_type, ir.VoidType):
                builder.ret_void()
            else:
                builder.ret(ir.Constant(return_type, 0))

        self.stack.pop()
        return func_type

    def compile_binary(self, node):
        stack_frame = self.get_current_stack_frame(node["line"])
        left = None
        right = None
        if node["operator"] == "==":
            self.context.append({
                "kind": ["ReturnPointerVariable"]
            })
            left = self.compile_stmt(node["left"])
            self.context.pop()
            self.context.append({
                "kind": ["CmpEq"],
                "left": left
            })
            right = self.compile_stmt(node["right"])
            self.context.pop()
            if node["right"]["kind"] == "EnumIndexExpression":
                left = stack_frame["builder"].load(stack_frame["builder"].gep(
                    left,
                    [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)],
                ))
            
            # left = stack_frame["builder"].gep(
            #         left,
            #         [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)],
            #     )
        else:
            left = self.compile_stmt(node["left"])
            right = self.compile_stmt(node["right"])
        result = None
        match node["operator"]:
            case "+":
                result = stack_frame["builder"].add(left, right)
            case "-":
                result = stack_frame["builder"].sub(left, right)
            case "==" | "!=" | ">" | "<" | ">=" | "<=":
                if isinstance(left.type, ir.IntType):  # type: ignore
                    result = stack_frame["builder"].icmp_signed(
                        node["operator"], left, right
                    )
                elif isinstance(left.type, ir.FloatType) or isinstance(left.type, ir.DoubleType):  # type: ignore
                    result = stack_frame["builder"].fcmp_ordered(
                        node["operator"], left, right
                    )
        return result

    def compile_string(self, node):
        stack_frame = self.get_current_stack_frame(node["line"])
        value = node["value"][1:-1]
        context = self.get_context()
        zero = ir.Constant(ir.IntType(32), 0)
        if value in self.strings:
            if context and "ReturnPointerVariable" in context["kind"]:
                return self.strings[value]
            return stack_frame["builder"].gep(
                self.strings[value], [zero, zero], inbounds=True
            )

        encoded = (value + "\0").encode("utf-8")
        string_type = ir.ArrayType(ir.IntType(8), len(encoded))

        global_var = ir.GlobalVariable(
            self.module, string_type, name=f".str.{len(self.strings)}"
        )
        global_var.global_constant = True
        global_var.linkage = "internal"
        global_var.initializer = ir.Constant(string_type, bytearray(encoded))  # type: ignore

        self.strings[value] = global_var
        if context and "ReturnPointerVariable" in context["kind"]:
            return global_var
        return stack_frame["builder"].gep(global_var, [zero, zero], inbounds=True)

    def compile_array(self, node):
        stack_frame = self.get_current_stack_frame(node["line"])
        builder = stack_frame["builder"]

        elements = []
        context = self.get_context()

        if context == None:
            return

        element_type = self.compile_type(context["raw"]["of"])

        self.context.append(
            {"kind": "TypeCast", "type": element_type, "raw": context["raw"]["of"]}
        )

        for element in node["elements"]:
            elements.append(self.compile_stmt(element))

        self.context.pop()

        array_type = ir.ArrayType(element_type, len(elements))
        arr_ptr = builder.alloca(array_type)

        zero = ir.Constant(ir.IntType(32), 0)

        for i, elem in enumerate(elements):
            index = ir.Constant(ir.IntType(32), i)
            element_pointer = builder.gep(arr_ptr, [zero, index])
            builder.store(elem, element_pointer)

        return builder.load(arr_ptr)

    def compile_declare_foreign(self, node):
        if node["stmt"]["kind"] == "VariableDeclaration":
            counter = ir.GlobalVariable(
                self.module,
                self.compile_type(node["stmt"]["type"]),
                name=node["stmt"]["name"],
            )
            counter.linkage = "external"
            counter.initializer = None
        elif node["stmt"]["kind"] == "FunctionDeclaration":
            args = []
            varadic = False
            for arg in node["stmt"]["params"]:
                if arg["type"] == "varadic":
                    varadic = True
                    break
                args.append(self.compile_type(arg["type"]))
            func_type = ir.FunctionType(
                self.compile_type(node["stmt"]["return_type"]), args, var_arg=varadic
            )

            param_index = 0
            for param in node["stmt"]["params"]:
                if param["type"] == "varadic":
                    break
                func_type.args[param_index].name = param["name"]
                param_index += 1

            fn = ir.Function(self.module, func_type, name=node["stmt"]["name"])
            self.functions[node["stmt"]["name"]] = fn

    def compile_call(self, node):
        stack_frame = self.get_current_stack_frame(node["line"])
        function = self.compile_stmt(node["function"])
        args = []

        if node["function"]["kind"] == "MemberExpression":
            self.context.append({"kind": "ReturnPointerVariable"})
            this = self.compile_stmt(node["function"]["parent"])
            self.context.pop()
            args.append(this)

        for arg in node["args"]:
            args.append(self.compile_stmt(arg))

        return stack_frame["builder"].call(function, args)

    def compile_index_expression(self, node):
        self.context.append({"kind": "ReturnPointerVariable"})
        parent = self.compile_stmt(node["parent"])
        self.context.pop()
        stack_frame = self.get_current_stack_frame(node["line"])
        context = self.get_context()
        pointer = None

        for chain_node in node["child"]:
            child = self.compile_stmt(chain_node)
            pointer = stack_frame["builder"].gep(
                parent, [ir.Constant(ir.IntType(32), 0), child]
            )
            parent = pointer

        if context and context["kind"] == "ReturnPointerVariable":
            return pointer
        else:
            return stack_frame["builder"].load(pointer)

    def compile_unary_expression(self, node):
        stack_frame = self.get_current_stack_frame(node["line"])

        if node["operator"] == "-":
            value = self.compile_stmt(node["value"])
            if isinstance(value.type, ir.IntType):
                zero = ir.Constant(value.type, 0)
                return stack_frame["builder"].sub(zero, value)

            elif isinstance(value.type, ir.FloatType) or isinstance(
                value.type, ir.DoubleType
            ):
                return stack_frame["builder"].fneg(value)

            else:
                self.error_class.compiler_error(
                    "Cannot apply unary '-' to this type!", self.file, node["line"]
                )
                self.error_class.dump()
        elif node["operator"] == "&":
            self.context.append({"kind": "ReturnPointerVariable"})
            value = self.compile_stmt(node["value"])
            self.context.pop()
            return value

    def compile_dereference(self, node):
        # self.context.append({"kind": "ReturnPointerVariable"})
        value = self.compile_stmt(node["value"])
        # self.context.pop()
        stack_frame = self.get_current_stack_frame(node["line"])
        return stack_frame["builder"].load(value)

    def compile_assignment(self, node):
        self.context.append({"kind": "ReturnPointerVariable"})
        left = self.compile_stmt(node["left"])
        self.context.pop()
        right = self.compile_stmt(node["right"])
        stack_frame = self.get_current_stack_frame(node["line"])
        stack_frame["builder"].store(right, left)

    def compile_is(self, node):
        stack_frame = self.get_current_stack_frame(node["line"])
        condition = self.compile_stmt(node["condition"])
        then_block = stack_frame["builder"].append_basic_block(f"then_{self.if_count}")
        else_block = stack_frame["builder"].append_basic_block(f"else_{self.if_count}")
        merge_block = stack_frame["builder"].append_basic_block(f"if_{self.if_count}")
        self.if_count += 1
        stack_frame["builder"].cbranch(condition, then_block, else_block)

        stack_frame["builder"].position_at_start(then_block)
        body_has_branch = False
        for body_node in node["body"]:
            if body_node["kind"] == "JumpStatement":
                body_has_branch = True
            self.compile_stmt(body_node)
        if not body_has_branch:
            stack_frame["builder"].branch(merge_block)

        stack_frame["builder"].position_at_start(else_block)
        if node["else_body"]:
            else_body_has_branch = False
            for body_node in node["else_body"]:
                if body_node["kind"] == "JumpStatement":
                    else_body_has_branch = False
                self.compile_stmt(body_node)
            if not else_body_has_branch:
                stack_frame["builder"].branch(merge_block)
        else:
            stack_frame["builder"].branch(merge_block)
        stack_frame["builder"].position_at_start(merge_block)

    def compile_loop(self, node):
        stack_frame = self.get_current_stack_frame(node["line"])
        loop_block = stack_frame["builder"].append_basic_block(
            f"loop_{self.loop_count}"
        )
        loop_end = stack_frame["builder"].append_basic_block(
            f"loop_end_{self.loop_count}"
        )
        stack_frame["builder"].branch(loop_block)

        self.loop_count += 1

        stack_frame["builder"].position_at_start(loop_block)
        self.context.append(
            {
                "kind": "LoopStatement",
                "start": loop_block,
                "end": loop_end,
            }
        )
        body_has_branch = False
        for body_node in node["body"]:
            if body_node["kind"] == "JumpStatement":
                body_has_branch = True
            self.compile_stmt(body_node)
        self.context.pop()
        if not body_has_branch:
            stack_frame["builder"].branch(loop_block)
        stack_frame["builder"].position_at_start(loop_end)

    def compile_break_continue(self, node):
        stack_frame = self.get_current_stack_frame(node["line"])
        context = self.get_context()

        if context and context["kind"] == "LoopStatement":
            if node["value"] == "stop":
                stack_frame["builder"].branch(context["end"])
            elif node["value"] == "continue":
                stack_frame["builder"].branch(context["start"])

    def compile_struct(self, node):
        struct_type = ir.global_context.get_identified_type(node["identifier"])
        members = []
        methods = []
        members_with_name = []
        for member in node["members"]:
            member_type = self.compile_type(member["type"])
            members.append(member_type)
            members_with_name.append(
                {"name": member["identifier"], "type": member["type"]}
            )

        self.structs[node["identifier"]] = {
            "type": struct_type,
            "members": members_with_name,
            "methods": methods
        }

        for ast_node in self.ast:
            if ast_node["kind"] == "ImplStatement" and ast_node["struct"] == node["identifier"]:
                args = []
                for arg in ast_node["method"]["params"]:
                    args.append(self.compile_type(arg["type"]))
                method_type = ir.FunctionType(self.compile_type(ast_node["method"]["return_type"]), args)
                members.append(method_type.as_pointer())
        struct_type.set_body(*members)

        for ast_node in self.ast:
            if ast_node["kind"] == "ImplStatement" and ast_node["struct"] == node["identifier"]:
                method_name = f"AZ@{node["identifier"]}_{ast_node["method"]["name"]}"
                ast_node["method"]["name"] = method_name
                method_type = self.compile_function(ast_node["method"])
                methods.append({"name": method_name, "type": method_type.as_pointer()})

    def compile_struct_literal(self, node):
        context = self.get_context()
        if context == None:
            return
        value = []

        for index, element in enumerate(node["elements"]):
            self.context.append(
                {
                    "kind": ["TypeCast", "ReturnPointerVariable"],
                    "type": self.compile_type(context["raw"]["members"][index]),
                    "raw": context["raw"]["members"][index],
                }
            )
            compiled_element = self.compile_stmt(element)
            value.append(compiled_element)
            self.context.pop()
        struct_data = self.structs[context["raw"]["name"]]
        for index, method in enumerate(struct_data["methods"]):
            value.append(self.module.get_global(method["name"])) # type: ignore

        return ir.Constant(context["type"], value)

    def compile_struct_index(self, node):
        self.context.append({"kind": "ReturnPointerVariable"})
        parent = self.compile_stmt(node["parent"])
        self.context.pop()
        stack_frame = self.get_current_stack_frame(node["line"])
        context = self.get_context()
        pointer = None
        struct_type = parent.type
        struct_name = None

        if isinstance(struct_type, ir.PointerType):
            struct_type = struct_type.pointee  # type: ignore

        if isinstance(struct_type, ir.IdentifiedStructType):
            struct_name = struct_type.name

        for chain_node in node["child"]:
            child = chain_node["value"]
            index = 0
            found = False
            for member in self.structs[struct_name]["members"]:
                if member["name"] == child:
                    found = True
                    break
                index += 1
            if found == False:
                index -= 1
                for member in self.structs[struct_name]["methods"]:
                    if member["name"] == f"AZ@{struct_name}_{child}":
                        found = True
                        break
                index += 1
            if found == False:
                self.error_class.compiler_error(
                    f"{child} is not a member of {struct_name}!",
                    self.file,
                    chain_node["line"],
                )
                self.error_class.dump()
            
            pointer = stack_frame["builder"].gep(
                parent,
                [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), index)],
            )
            parent = pointer

        if context and context["kind"] == "ReturnPointerVariable":
            return pointer
        else:
            return stack_frame["builder"].load(pointer)

    def compile_enum(self, node):
        enum_data = {}
        index = 0
        for enum in node["enums"]:
            enum_data[enum["identifier"]] = {
                "type": self.llvm_base_types["void"],
                "tag": index,
                "raw": {"kind": "BaseType", "type": "void"},
            }
            if len(enum["type"]) == 1:
                enum_data[enum["identifier"]] = {
                    "type": self.compile_type(enum["type"][0]),
                    "tag": index,
                    "raw": enum["type"][0],
                }
            elif len(enum["type"]) > 1:
                types = []
                for type in enum["type"]:
                    types.append(self.compile_type(type))
                enum_data[enum["identifier"]] = {
                    "type": ir.LiteralStructType(types),
                    "tag": index,
                    "raw": enum["type"],
                }
            index += 1

        enum_type = ir.global_context.get_identified_type(node["identifier"])
        amount = len(node["enums"])
        tag_type = None
        if amount <= 127:
            tag_type = ir.IntType(8)
        elif amount <= 32767:
            tag_type = ir.IntType(16)
        elif amount <= 2147483647:
            tag_type = ir.IntType(32)
        elif amount <= 9223372036854775807:
            tag_type = ir.IntType(64)

        target_data = self.module.data_layout  # type: ignore

        max_size = 0
        max_align = 1

        for variant in enum_data.values():
            size = 0
            align = 0
            if not isinstance(variant["type"], ir.VoidType):
                size = variant["type"].get_abi_size(target_data)
                align = variant["type"].get_abi_alignment(target_data)

            max_size = max(max_size, size)
            max_align = max(max_align, align)

        if max_size == 0:
            payload = ir.LiteralStructType([])
        else:
            payload = ir.ArrayType(ir.IntType(8), max_size)

        enum_type.set_body(tag_type, payload)
        self.enums[node["identifier"]] = {
            "data": enum_data,
            "type": enum_type,
            "raw": [tag_type, payload],
        }
        self.llvm_base_types[node["identifier"]] = enum_type

    def compile_enum_index(self, node):
        stack_frame = self.get_current_stack_frame(node["line"])
        context = self.get_context()
        enum_data = self.enums[node["parent"]]
        enum_args = node["args"]
        child = enum_data["data"][node["child"]]

        if context and "CmpEq" in context["kind"]:
            left_value = context["left"]
            tag_pointer = stack_frame["builder"].gep(
                left_value,
                [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)],
            )
            payload_pointer = stack_frame["builder"].gep(
                left_value,
                [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 1)],
            )

            payload = stack_frame["builder"].load(payload_pointer)
            if isinstance(child["type"], (ir.LiteralStructType, ir.IdentifiedStructType)):
                index = 0
                typed_pointer = stack_frame["builder"].bitcast(
                    payload_pointer,
                    child["type"].as_pointer()
                )
                for arg in enum_args:
                    stack_frame["variables"][arg["value"]] = {
                        "memory": stack_frame["builder"].alloca(
                            self.compile_type(child["raw"][index]),
                            name=arg["value"],
                        ),
                        "type": child["raw"][index],
                    }
                    value_pointer = stack_frame["builder"].gep(
                        typed_pointer,
                        [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), index)],
                    )
                    value = stack_frame["builder"].load(value_pointer)
    
                    stack_frame["builder"].store(
                        value, stack_frame["variables"][arg["value"]]["memory"]
                    )
                    index += 1
            else:
                stack_frame["variables"][enum_args[0]["value"]] = {
                    "memory": stack_frame["builder"].alloca(
                        child["type"], name=enum_args[0]["value"]
                    ),
                    "type": child["raw"],
                }
                typed_pointer = stack_frame["builder"].bitcast(
                    payload_pointer,
                    child["type"].as_pointer()
                )
                stack_frame["builder"].store(
                    stack_frame["builder"].load(typed_pointer), stack_frame["variables"][enum_args[0]["value"]]["memory"]
                )
            return ir.Constant(enum_data["raw"][0], child["tag"])
        enum_pointer = stack_frame["builder"].alloca(enum_data["type"])
 
        tag = 0
        for name in enum_data["data"]:
            if name == node["child"]:
                break
            tag += 1

        tag_pointer = stack_frame["builder"].gep(
            enum_pointer,
            [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)],
        )
        stack_frame["builder"].store(ir.Constant(enum_data["raw"][0], tag), tag_pointer)
        if len(enum_args) > 0 and not isinstance(child["type"], ir.VoidType):
            payload_pointer = stack_frame["builder"].gep(
                enum_pointer,
                [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 1)],
            )
            if len(enum_args) == 1:
                self.context.append(
                    {"kind": ["TypeCast"], "type": child["type"], "raw": child["raw"]}
                )
                compiled_value = self.compile_stmt(enum_args[0])
                self.context.pop()
            else:
                typed_union_pointer = stack_frame["builder"].bitcast(
                        payload_pointer,
                        child["type"].as_pointer()
                    )
                for i, arg_node in enumerate(enum_args):
                    self.context.append(
                        {"kind": ["TypeCast"], "type": self.compile_type(child["raw"][i]), "raw": child["raw"]}
                    )
                    value = self.compile_stmt(arg_node)
                    self.context.pop()
                    
                    field_pointer = stack_frame["builder"].gep(
                        typed_union_pointer,
                        [
                            ir.Constant(ir.IntType(32), 0),
                            ir.Constant(ir.IntType(32), i),
                        ],
                    )
                    stack_frame["builder"].store(value, field_pointer)
                compiled_value = stack_frame["builder"].load(typed_union_pointer)
            cast_pointer = stack_frame["builder"].bitcast(
                payload_pointer, compiled_value.type.as_pointer()
            )
            stack_frame["builder"].store(compiled_value, cast_pointer)

        return stack_frame["builder"].load(enum_pointer)