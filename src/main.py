import sys
from pathlib import Path
from preprocessor import *
from lexer import *
from parser import *
from semantic_analysis import *
from compiler import *
import link
import VERSION

argc = len(sys.argv)
argv = sys.argv

flags = []
for flag in argv:
    if flag.startswith("-"):
        flags.append(flag)

if "--version" in flags or "-v" in flags:
    print("azure version " + VERSION.version)
    sys.exit(0)

if argc < 2:
    print("Must provide a file!")
    sys.exit(1)

input_file = Path(argv[1])
output_file = Path("a.o")
if argc > 3 and argv[2] == "-o":
    output_file = Path(argv[3])
if not input_file.exists():
    print("Path does not exist!")
    sys.exit()(1)

with open(input_file) as f:
    source = PREPROCESSOR(f.read(), input_file.name).processed
    tokens = LEXER(source, input_file.name).tokens
    ast = PARSER(tokens, input_file.name).ast
    SEMANTIC_ANALYSIS(ast, input_file.name)
    module = COMPILER(ast, input_file.name)

if "--pppc" in flags:
    print(source)

if "--llvmir" in flags:
    print(module.module)

path = module.emit_obj(output_file)
link.link(path, output_file)
