
import ast
import sys

script = "".join(sys.stdin.readlines())

module = ast.parse(script)

indent = 0

def tabin():
    global indent
    indent = indent + 1

def tabout():
    global indent
    indent = indent - 1

def _write(string):
    sys.stdout.write(string)

def tabwrite(string):
    _write(("    " * indent) + string)

def tabwriteln(string):
    _write(("    " * indent) + string + "\n")

def write(string):
    _write(string)

def writeln(string):
    _write(string + "\n")

def see(obj):
    print repr(obj)
    print "    " + repr(dir(obj))

def err(msg, ctx):
    raise Exception("%s at line %i, column %i" % (msg, ctx.lineno, ctx.col_offset))

def _lit(string):
    s = [ string ]
    def func(self, node):
        write(s[0])
    return func

class Handler:

    # Statements

    def Module(self, node):
        process_nodes(node.body)

    def FunctionDef(self, node):

        if len(node.decorator_list) > 0:
            err("Decorators are not supported", node)
        
        if node.name:
            name = node.name
        else:
            name = ""
        tabwrite("Function %s(" % (name))

        bs_args = []

        for arg in node.args.args:
            bs_args.append(arg.id)

        write(", ".join(bs_args))

        writeln(")")

        tabin()
        process_nodes(node.body)
        tabout()

        tabwriteln("End Function")

    def Print(self, node):
        tabwrite("Print ")
        values = capture_nodes(node.values)
        write(", ".join(values))
        writeln("")

    def Assign(self, node):
        if len(node.targets) != 1:
            err("Only one lvalue allowed in assignment", node)
        lvalue = node.targets[0]
        if lvalue.__class__.__name__ == "Tuple":
            err("Can't assign to a tuple", node)

        tabwrite(lvalue.id + " = ")
        process_node(node.value)
        writeln("")

    def Expr(self, node):
        tabwrite("")
        process_node(node.value)
        writeln("")

    def While(self, node):

        if node.orelse:
            err("else clause on while is not supported", node)

        tabwrite("While ")
        process_node(node.test)
        writeln("")
        tabin()

        process_nodes(node.body)

        tabout()

        tabwriteln("End While")

    def If(self, node):

        tabwrite("If ")
        process_node(node.test)
        writeln("")
        tabin()

        process_nodes(node.body)

        tabout()

        if (node.orelse):

            if (len(node.orelse) > 1):
                err("Can't have more than one else block", node)
            
            tabwriteln("Else")
            tabin()
            process_node(node.orelse[0])
            tabout()
            
        tabwriteln("End If")

    def For(self, node):
        if node.orelse:
            err("Can't use an else block on a for statement", node)

        tabwrite("For ")
        process_node(node.target)
        write(" In ")
        process_node(node.iter)
        writeln("")
        tabin()
        process_nodes(node.body)
        tabout()
        tabwriteln("Next")
        

    # Expressions

    def Str(self, node):
        write(repr(node.s))

    def Num(self, node):
        write(repr(node.n))

    def BinOp(self, node):
        write("(")
        process_node(node.left)
        write(" ")
        process_node(node.op)
        write(" ")
        process_node(node.right)
        write(")")

    def UnaryOp(self, node):
        process_node(node.op)
        write(" ")
        process_node(node.operand)

    def BoolOp(self, node):
        op_str = " " + capture_node(node.op) + " "
        write("(")
        write(op_str.join(capture_nodes(node.values)))
        write(")")

    def Compare(self, node):
        if len(node.ops) > 1:
            err("Only one operator allowed in compare expr", node)

        op = node.ops[0]
        right = node.comparators[0]

        write("(")
        process_node(node.left)
        write(" ")
        process_node(op)
        write(" ")
        process_node(right)
        write(")")

    def Attribute(self, node):
        process_node(node.value)
        write(".")
        write(node.attr)

    def Name(self, node):
        name = node.id

        if name == "True":
            name = "true"
        elif name == "False":
            name = "false"
        elif name == "None":
            name = "invalid"

        write(name)

    def Call(self, node):

        if len(node.keywords) > 0:
            err("Keyword args are not supported", node)
        if node.starargs:
            err("*args is not supported", node)
        if node.kwargs:
            err("**kwargs is not supported", node)
        
        process_node(node.func)
        write("(")
        write(", ".join(capture_nodes(node.args)))
        write(")")
        process_nodes(node.keywords)

    def Subscript(self, node):
        process_node(node.value)
        write("[")
        process_node(node.slice.value)
        write("]")

    def Tuple(self, node):
        write("[")
        write(", ".join(capture_nodes(node.elts)))
        write("]")
    List = Tuple

    def Dict(self, node):
        write("{")
        for i in range(0, len(node.keys)):
            if i > 0:
                write(", ")
            key = node.keys[i]
            value = node.values[i]
            process_node(key)
            write(": ")
            process_node(value)
        write("}")
            

    Add = _lit("+")
    Sub = _lit("-")
    Gt = _lit(">")
    Lt = _lit("<")
    Eq = _lit("=")
    GtE = _lit(">=")
    LtE = _lit("<=")
    And = _lit("AND")
    Or = _lit("OR")
    Not = _lit("NOT")

    # Default function used for unhandled stuff
    def _default(self, node):
        print "Don't know what to do with a "+node.__class__.__name__+" object"
        print "It has these members:"
        print repr(dir(node))
        #err("Unsupported Python feature", node)

h = Handler()

def process_node(node):
    class_name = node.__class__.__name__
    handler = getattr(h, class_name, h._default)
    handler(node)

def process_nodes(nodes):
    for node in nodes:
        process_node(node)

def capture_node(node):
    global _write
    ret = [""]
    def fakewrite(str):
        ret[0] = ret[0] + str
    realwrite = _write
    _write = fakewrite
    process_node(node)
    _write = realwrite
    return ret[0]

def capture_nodes(nodes):
    ret = []
    for node in nodes:
        ret.append(capture_node(node))
    return ret


process_node(module)
