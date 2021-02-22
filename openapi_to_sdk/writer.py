from typing import List
class PythonWriter:
    def add_indent(self):
        return self.indenter * (self.indent_level)

    def write_header(self, filename):
        with open(filename, 'w') as f:
            f.write("# This python file is auto-generated. Please do not edit.\n")

    def write_function(self, function_string, filename='api.py'):
        with open(filename, 'a') as f:
            f.write(function_string)
    
    def write_python_instance_methods(self, function_strings, filename='api.py'):
        with open(filename, 'a') as f:
            for func in function_strings:
                f.write('\t')
                f.write(func)
                f.write('\n\n')
    
    def write_imports(self, filename='api.py', import_strings: List[str]=[]):
        """Add imports to the Python file.
        """
        if not isinstance(import_strings, list):
            raise ValueError("Imports need to be in the format: ['import vectorai']")
        with open(filename, 'a') as f:
            for import_str in import_strings:
                f.write(import_str)
                f.write('\n')
            f.write('\n\n')
    
    def write_constructor(self, filename, class_name: str, inherited_properties: List[str]):
        with open(filename, 'a') as f:
            f.write("class " + class_name + ':')
            f.write("\n")
            f.write("\tdef __init__(self, ")
            for prop in inherited_properties:
                f.write(prop)
                f.write(", ")
            f.write("):\n")
            self.indent_level += 2
            for prop in inherited_properties:
                self.add_indent()
                f.write(self.add_indent())
                f.write(f"self.{prop} = {prop}")
                f.write(self.add_indent())
                f.write("\n")
            f.write("\n")
        self.indent_level -= 2             

