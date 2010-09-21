
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

    # Expressions

    def Str(self, node):
        write(repr(node.s))

    def BinOp(self, node):
        process_node(node.left)
        write(" ")
        process_node(node.op)
        write(" ")
        process_node(node.right)

    def Attribute(self, node):
        process_node(node.value)
        write(".")
        write(node.attr)

    def Name(self, node):
        write(node.id)

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

    Add = _lit("+")

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
