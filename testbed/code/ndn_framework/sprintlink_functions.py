from time import sleep 
from random import random, randint, choice
# from string import ascii_letters, digits
import ast
import importlib.util
import sys

def get_function_count() -> int:
    with open(__file__, "r") as f:
        tree = ast.parse(f.read())
        function_count: int = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if "get_" not in node.name: # Exclude getters
                    function_count += 1
        return function_count
    
def get_functions() -> dict:
    # Obtain func names in file.
    with open(__file__, "r") as f:
        tree = ast.parse(f.read())
        function_names: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if "get_" not in node.name: # Exclude getters
                    function_names.append(node.name)

    # Create module object with file.
    spec = importlib.util.spec_from_file_location("func_module", __file__)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules["func_module"] = module # Register the module

    # Create func dict with names and module.
    functions = {name: getattr(module, name) for name in function_names if hasattr(module, name)}    
    return functions

def get_function_names() -> list[str]:
    func_dict = get_functions()
    return list(func_dict.keys())

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def dummy1(value: int) -> None:
    sleep(5)
    if value == 0:
        return 0
    return randint(-value if value > 0 else value, value if value > 0 else -value)
        
def dummy2 (value: float) -> None:
    sleep(5)
    parity = (randint(0, 1)*2)-1    # +/- 1
    return random()*value*parity

def dummy3(value: str) -> None:
    sleep(5)
    if type(value) != str:
        return f"dummy3 needs a string input, received: {type(value)}."
    chars = [c for c in value]
    return "".join(choice(chars) for _ in range(10))
    

if __name__ == "__main__":
    functions  = get_functions()
    for name,func in functions.items():
        print(f"{name}: {functions[name]()}")