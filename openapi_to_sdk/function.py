"""
Create a new function in Python
"""
import requests
from types import FunctionType
from typing import Tuple

def create_function(function_string: str, function_name: str, default_arguments: Tuple=None):
    foo_code = compile(function_string, "<string>", "exec")
    return FunctionType(foo_code.co_consts[0], globals(), function_name, argdefs=default_arguments)
