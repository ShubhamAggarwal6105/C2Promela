from pycparser import c_parser, c_ast, parse_file
from pycparser.c_ast import StructRef, ID

class ASTToPromela(c_ast.NodeVisitor):
# Initializes symbol table, output list, and function definitions.
    def __init__(self, output):
        self.output = output
        self.declared_vars = set()
        self.func_defs = {}
        self.if_contains_continue = False

# Appends formatted Promela code lines to the output list.
    def emit(self, code, indent=0):
        self.output.write('    ' * indent + code + '\n')

# Visitor methods that handle specific AST node types.
    def visit_FileAST(self, node):
        for ext in node.ext:
            self.visit(ext)

    def map_c_type_to_promela(self, c_type_names):
        """
        Maps C types like 'unsigned char' or 'int' to Promela types like 'bit', 'byte', 'int'.
        """
        c_type = ' '.join(c_type_names).lower()

        type_mapping = {
            'char': 'byte',
            'unsigned char': 'byte',
            'signed char': 'byte',
            'short': 'int',
            'unsigned short': 'int',
            'int': 'int',
            'unsigned int': 'int',
            'long': 'int',
            'unsigned long': 'int',
            'float': 'int',
            'double': 'int',
            'bool': 'bit'
        }
        print(c_type)
        return type_mapping.get(c_type, 'int')


    def handle_malloc(self, indent=0):
        self.emit("int malloc_node_c;", indent)
        self.emit("int tmp;", indent)
        self.emit("atomic {", indent)
        self.emit("malloc_node_c = 1;", indent + 1)
        self.emit("do", indent + 1)
        self.emit(":: (malloc_node_c >= 9) -> break", indent + 2)
        self.emit(":: else ->", indent + 2)
        self.emit("if", indent + 3)
        self.emit(":: (node_valid[malloc_node_c] == 0) ->", indent + 4)
        self.emit("node_valid[malloc_node_c] = 1;", indent + 5)
        self.emit("break", indent + 5)
        self.emit(":: else -> malloc_node_c++", indent + 4)
        self.emit("fi", indent + 3)
        self.emit("od", indent + 1)
        self.emit("assert(malloc_node_c < 9);", indent + 1)
        self.emit("tmp = malloc_node_c;", indent + 1)
        self.emit("}", indent)
    
    def handle_free(self, var_name, indent=0):
        self.emit("d_step {", indent)
        self.emit(f"node_valid[{var_name}] = 0;", indent + 1)
        self.emit(f"node_mem[{var_name}].next = 0;", indent + 1)
        self.emit(f"node_mem[{var_name}].value = 0;", indent + 1)
        self.emit("}", indent)

# Visitor methods that handle specific AST node types.
    def visit_FuncDef(self, node):
        name = node.decl.name
        self.current_function = name

        params = [p.name for p in node.decl.type.args.params] if node.decl.type.args else []
        self.func_defs[name] = params

        if node.decl.type.type.type.names[0] == "void":
            self.emit(f"proctype {name}(" + "; ".join(f"int {p}" for p in params) + ") {")
        else:
            self.emit(f"proctype {name}(chan in_{name}; " + "; ".join(f"int {p}" for p in params) + ") {")

        self.visit(node.body)

        self.emit("end :",)
        self.emit("printf(\"End of " + name + "\\n\");",)
        self.emit("}\n")
    
# Visitor methods that handle specific AST node types.
    def visit_FuncCall(self, node, indent=1):
        func_name = self.expr_to_str(node.name)
        if func_name == 'malloc':
            self.handle_malloc(indent)
            return

        if func_name == "free":
            var_name = node.args.exprs[0].name
            self.handle_free(var_name, indent)
            return

        if func_name in self.func_defs:
            if node.args == None:
                args = []
            else:
                args = [self.expr_to_str(a) for a in node.args.exprs]

            self.emit(f"run {func_name}({', '.join(args)});", indent)
        else:
            # fallback for unknown functions
            self.emit(f"{self.expr_to_str(node)};", indent)

# Visitor methods that handle specific AST node types.
    def visit_Compound(self, node, indent=1):
        stmts = node.block_items or []
        i = 0
        while i < len(stmts):
            stmt = stmts[i]
            if isinstance(stmt, c_ast.If):
                # look ahead in the true branch for continue
                self.if_contains_continue = self.contains_continue(stmt.iftrue) and i + 1 < len(stmts)
                else_branch = stmt.iffalse
                self.visit(stmt)
                if self.if_contains_continue:
                    self.emit(":: else ->", indent)
                    for j in range(i + 1, len(stmts)):
                        self.visit(stmts[j])
                    
                    self.emit("fi", indent-1)
                    break
            elif isinstance(stmt, c_ast.Continue):
                self.visit(stmt)
                break  # skip rest of block
            else:
                self.visit(stmt)
            i += 1

    def contains_continue(self, node):
        """Recursively check if a block contains a `continue`."""
        if isinstance(node, c_ast.Continue):
            return True
        elif isinstance(node, c_ast.Compound):
            return any(self.contains_continue(stmt) for stmt in (node.block_items or []))
        elif hasattr(node, 'iftrue') or hasattr(node, 'iffalse'):
            return self.contains_continue(getattr(node, 'iftrue', None)) or self.contains_continue(getattr(node, 'iffalse', None))
        elif hasattr(node, '__dict__'):
            return any(self.contains_continue(val) for val in node.__dict__.values() if isinstance(val, c_ast.Node))
        return False

# Visitor methods that handle specific AST node types.
    def visit_If(self, node, indent=1):
        self.emit("if", indent - 1)
        cond = self.expr_to_str(node.cond)
        self.emit(f":: ({cond}) ->", indent)
        self.visit(node.iftrue)
        if node.iffalse:
            self.emit(":: else ->", indent)
            self.visit(node.iffalse)
        if not self.if_contains_continue:
            self.emit("fi;", indent - 1)

# Visitor methods that handle specific AST node types.
    def visit_While(self, node, indent=1):
        cond = self.expr_to_str(node.cond)
        self.emit("do", indent - 1)
        self.emit(f":: ({cond}) ->", indent)
        self.visit(node.stmt)
        self.emit(":: else -> break;", indent)
        self.emit("od;", indent - 1)

# Visitor methods that handle specific AST node types.
    def visit_For(self, node, indent=1):
        if node.init:
            self.visit(node.init)
        self.emit("do", indent - 1)
        cond = self.expr_to_str(node.cond) if node.cond else "true"
        self.emit(f":: ({cond}) ->", indent)
        self.visit(node.stmt)
        if node.next:
            self.visit(node.next)
        self.emit(":: else -> break;", indent)
        self.emit("od;", indent - 1)

# Visitor methods that handle specific AST node types.
    def visit_Struct(self, node, indent=1):
        if not node.decls or not node.name:
            return

        struct_name = node.name
        self.emit(f"typedef {struct_name} {{", indent - 1)

        for field in node.decls:
            field_name = field.name
            field_type = field.type

            if isinstance(field_type, c_ast.PtrDecl):
                # Pointer to struct — represent as an int index
                self.emit(f"int {field_name};", indent)
            elif isinstance(field_type, c_ast.TypeDecl):
                if isinstance(field_type.type, c_ast.Struct):
                    # Embedded struct type — treat as int for now (could extend)
                    self.emit(f"int {field_name};", indent)
                else:
                    base_type = ' '.join(field_type.type.names)
                    self.emit(f"{base_type} {field_name};", indent)
            else:
                self.emit(f"/* Unhandled type for field {field_name} */", indent)

        self.emit("}", indent - 1)
        self.emit(f"{struct_name} {struct_name}_mem[9];", indent - 1)
        self.emit(f"int {struct_name}_valid[9];\n", indent - 1)

# Visitor methods that handle specific AST node types.
    def visit_Break(self, node, indent=1):
        self.emit("break;", indent)

# Visitor methods that handle specific AST node types.
    def visit_Decl(self, node, indent=1):
        type_node = node.type
        var_name = node.name

        # Handle pointer declarations
        if isinstance(type_node, c_ast.PtrDecl):
            self.emit(f"int {var_name};", indent)
            if isinstance(node.init, c_ast.FuncCall) and self.expr_to_str(node.init.name)=="malloc":
                self.visit(node.init)
                self.emit(f"{var_name} = tmp;", indent)

        # Handle array declarations (both struct and primitive types)
        if isinstance(type_node, c_ast.ArrayDecl):
            elem_type = type_node.type
            size = self.expr_to_str(type_node.dim)
            # Struct array
            if isinstance(elem_type.type, c_ast.Struct):
                struct_name = elem_type.type.name
                self.emit(f"{struct_name} {var_name}[{size}];", indent)
            # Primitive array
            elif isinstance(elem_type, c_ast.TypeDecl):
                base_type = ' '.join(elem_type.type.names)
                self.emit(f"{base_type} {var_name}[{size}];", indent)
            else:
                # Fallback (just in case)
                self.emit(f"/* Unhandled array type for {var_name} */", indent)
            self.declared_vars.add(var_name)
            return

        # Struct single variable: struct node n;
        if isinstance(type_node, c_ast.TypeDecl) and isinstance(type_node.type, c_ast.Struct):
            struct_name = type_node.type.name
            if var_name not in self.declared_vars:
                self.emit(f"{struct_name} {var_name};", indent)
                self.declared_vars.add(var_name)
            return
        
        # struct node{ }
        if isinstance(type_node, c_ast.Struct):
            self.visit_Struct(type_node, indent)

        # Regular primitive variable
        if isinstance(type_node, c_ast.TypeDecl):
            if var_name not in self.declared_vars:
                base_type = self.map_c_type_to_promela(type_node.type.names)
                self.emit(f"{base_type} {var_name};", indent)
                self.declared_vars.add(var_name)

            if node.init:
                if isinstance(node.init, c_ast.TernaryOp):
                    self.handle_ternary_assignment(var_name, node.init, indent)
                elif isinstance(node.init, c_ast.FuncCall):
                    func_name = self.expr_to_str(node.init.name)
                    args = [self.expr_to_str(a) for a in node.init.args.exprs]
                    self.emit(f"chan ret_{func_name} = [0] of {{ int }};", indent)
                    self.emit(f"run {func_name}(ret_{func_name}, {', '.join(args)});", indent)
                    self.emit(f"ret_{func_name} ? {var_name};", indent)
                else:
                    self.emit(f"{var_name} = {self.expr_to_str(node.init)};", indent)

# Visitor methods that handle specific AST node types.
    def visit_Assignment(self, node, indent=1):
        lhs = self.expr_to_str(node.lvalue)
        rhs = node.rvalue

        # If RHS is a function call
        if isinstance(rhs, c_ast.FuncCall):
            func_name = self.expr_to_str(rhs.name)
            if func_name in self.func_defs:
                args = [self.expr_to_str(arg) for arg in rhs.args.exprs] if rhs.args else []
                self.emit(f"chan ret_{func_name} = [0] of {{ int }};", indent)
                self.emit(f"run {func_name}(ret_{func_name}, {', '.join(args)});", indent)
                self.emit(f"ret_{func_name} ? {lhs};", indent)
            else:
                # fallback to default C style function call representation
                self.emit(f"{lhs} = {func_name}({', '.join(self.expr_to_str(arg) for arg in rhs.args.exprs)});", indent)
        else:
            if isinstance(rhs, c_ast.TernaryOp):
                self.handle_ternary_assignment(lhs, rhs, indent)
            else:
                self.emit(f"{lhs} = {self.expr_to_str(rhs)};", indent)

# Visitor methods that handle specific AST node types.
    def visit_Return(self, node, indent=1):
        if isinstance(node.expr, c_ast.FuncCall):
            func_name = self.expr_to_str(node.expr.name)
            args = [self.expr_to_str(a) for a in node.expr.args.exprs]
            self.emit(f"    chan ret_{func_name} = [0] of {{ int }};")
            self.emit(f"    int tmp;")
            self.emit(f"run {func_name}(ret_{func_name}, {', '.join(args)});", indent)
            self.emit(f"ret_{func_name} ? tmp;", indent)
            self.emit(f"in_{self.current_function} ! tmp;", indent)
            self.emit("goto end", indent)
        else:
            val = self.expr_to_str(node.expr)
            self.emit(f"in_{self.current_function} ! {val};", indent)
            self.emit("goto end", indent)

    def handle_ternary_assignment(self, var_name, ternary_node, indent=1):
        cond = self.expr_to_str(ternary_node.cond)
        iftrue = self.expr_to_str(ternary_node.iftrue)
        iffalse = self.expr_to_str(ternary_node.iffalse)
        self.emit("if", indent)
        self.emit(f":: ({cond}) -> {var_name} = {iftrue};", indent + 1)
        self.emit(f":: else -> {var_name} = {iffalse};", indent + 1)
        self.emit("fi;", indent)

# Visitor methods that handle specific AST node types.
    def visit_UnaryOp(self, node, indent=1):
        if node.op in ("p++", "p--"):
            var = self.expr_to_str(node.expr)
            delta = "+ 1" if node.op == "p++" else "- 1"
            self.emit(f"{var} = {var} {delta};", indent)

# Visitor methods that handle specific AST node types.
    def visit_Switch(self, node, indent=1):
        switch_var = self.expr_to_str(node.cond)
        self.emit("if", indent - 1)
        for case in node.stmt.block_items:
            if isinstance(case, c_ast.Case):
                val = self.expr_to_str(case.expr)
                self.emit(f":: ({switch_var} == {val}) ->", indent)
                for stmt in case.stmts:
                    self.visit(stmt)
            elif isinstance(case, c_ast.Default):
                self.emit(":: else ->", indent)
                for stmt in case.stmts:
                    self.visit(stmt)
        self.emit("fi;", indent - 1)

    def expr_to_str(self, expr):
        """Convert an expression AST to a string."""
        if expr is None:
            return ""

        if isinstance(expr, StructRef):
            if expr.type == '->':
                # ptr->field => node_mem[ptr].field
                ptr = self.expr_to_str(expr.name)
                field = expr.field.name
                return f"node_mem[{ptr}].{field}"
            elif expr.type == '.':
                # struct.field => struct.field
                base = self.expr_to_str(expr.name)
                field = expr.field.name
                return f"{base}.{field}"

        # Fallback: use default C generator
        from pycparser.c_generator import CGenerator
        return CGenerator().visit(expr)


# Main function to perform the conversion by reading 'input.c' and writing 'output.pml'.
def convert():
    ast = parse_file("input.c", use_cpp=True,
                     cpp_path='gcc', cpp_args=['-E', r'-Ipycparser/utils/fake_libc_include'])

    with open("output.pml", 'w') as out:
        converter = ASTToPromela(out)
        converter.visit(ast)
        if 'main' in converter.func_defs:
            out.write("\ninit {\n   chan ret_main = [0] of { bit };\n   run main(ret_main);\n   ret_main ? 0\n}\n")
    print(f"Generated output.pml")


if __name__ == '__main__':
    convert()