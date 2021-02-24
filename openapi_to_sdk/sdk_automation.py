"""SDK Automation
"""
import json
import requests
from typing import List, Dict
from .function import create_function
from .writer import PythonWriter

class PythonSDKBuilder(PythonWriter):
    def __init__(self, url: str='', sample_endpoint: str='', 
    inherited_properties: List[str]=[], json_fn: str=None, 
    decorators: Dict[str, str]={}, override_param_defaults={}, 
    internal_functions: set={}):
        """
        Args:
            url: 
            Sample endpoint: Endpoint for quick testing 
            override_param_defaults: Override param defaults in SDK
        """
        self.sample_endpoint = sample_endpoint
        self.url = url
        if json_fn is not None:
            self.data = json.load(open(json_fn))
        else:
            self.data = self._download_json()
        self.inherited_properties = inherited_properties
        self.decorators = decorators
        self.indent_level = 0
        self.override_param_defaults=override_param_defaults
        self.internal_functions = internal_functions
    
    def _download_json(self):
        return requests.get(self.url + "/openapi.json").json()
    
    @property
    def sample(self):
        return self.data['paths'][self.sample_endpoint]

    def get_request_type(self, endpoint_metadata):
        return self.get_field_value(endpoint_metadata)
    
    def get_field_value(self, dictionary):
        return list(dictionary.keys())[0]

    def get_tags(self, endpoint_metadata):
        return endpoint_metadata['tags']

    def get_summary(self, endpoint_metadata):
        return endpoint_metadata['summary']

    def get_request_body(self, endpoint_metadata):
        request_type = self.get_request_type(endpoint_metadata)
        body = endpoint_metadata[request_type]
        if request_type == 'post':
            return body['requestBody']['content']['application/json']['schema']['$ref']
        elif request_type == 'get':
            return body['parameters']
     
    def get_body_name(self, endpoint_metadata):
        request_body = self.get_request_body(endpoint_metadata)
        return request_body.split('/')[-1]
    
    def get_body(self, endpoint_metadata):
        body_name = self.get_body_name(endpoint_metadata)
        return self.data['components']['schemas'][body_name]

    def get_body_info(self, endpoint_metadata):
        if self.get_request_type(endpoint_metadata) == 'post':
            return self.get_body(endpoint_metadata)['properties']
        elif self.get_request_type(endpoint_metadata) == 'get':
            return self.get_params(endpoint_metadata)
    
    def get_params(self, endpoint_metadata):
        response = self.get_request_body(endpoint_metadata)
        return response
    
    def get_request_func(self, endpoint_metadata):
        return getattr(requests, self.get_request_type(endpoint_metadata))
    
    def create_endpoint_metadata_string(self, endpoint, include_response_parsing=False):
        function_name = endpoint.split('/')[-1]
        endpoint_metadata = self.data['paths'][endpoint]
        body_kwargs = self.get_body_kwargs(endpoint_metadata)
        return self.get_request_template(
            function_name, 
            endpoint, 
            self.get_request_type(endpoint_metadata), body_kwargs,
            include_response_parsing)
        
    def get_body_kwargs(self, endpoint_metadata):
        if self.get_request_type(endpoint_metadata) == 'post':
            return list(self.get_body_info(endpoint_metadata).items())
        if self.get_request_type(endpoint_metadata) == 'get':
            return self.get_body_info(endpoint_metadata)
    
    def get_request_template(self, endpoint_metadata_name, endpoint, endpoint_metadata_type, 
    body_kwargs, include_response_parsing: bool):
        decorator_string = self.get_decorator_string()
        if endpoint_metadata_type == 'post':
            return decorator_string + self.get_request_post_template(endpoint_metadata_name, 
            endpoint, body_kwargs, include_response_parsing)[0]
        elif endpoint_metadata_type == 'get':
            return decorator_string + self.get_request_get_template(endpoint_metadata_name, 
            endpoint, body_kwargs, include_response_parsing)[0]

    def create_documentation(self, endpoint):
        documentation = ''
        endpoint_request_type = self.get_request_type(self.get_endpoint_metadata(endpoint))
        documentation += self.data['paths'][endpoint][endpoint_request_type]['summary'] + '\n' + \
        self.data['paths'][endpoint][endpoint_request_type]['description'] + '\n'
        documentation += "Args\n"
        documentation += "========\n"
        if endpoint_request_type == 'post':
            for k, v in self.get_body_kwargs(self.get_endpoint_metadata(endpoint)):
                documentation += k + ': '
                if 'description' in v.keys():
                    documentation += v['description']
                documentation += '\n'
        elif endpoint_request_type == 'get':
            for v in self.get_body_kwargs(self.get_endpoint_metadata(endpoint)):
                documentation += v['name'] + ': '
                if 'description' in v.keys():
                    v['description']
                documentation += '\n'
        documentation += '\n'
        return documentation

    def get_default_value_from_override(self, param):
        if 'title' in param.keys():
            if param['title'] in self.override_param_defaults:
                return self.override_param_defaults[param['title']]
        if 'name' in param.keys():
            if param['name'] in self.override_param_defaults:
                return self.override_param_defaults[param['name']]
        return self.missing_value
    
    def get_default_value_from_override_by_param_name(self, param_name: str):
        if param_name in self.override_param_defaults.keys():
            return self.override_param_defaults[param_name]
        return self.missing_value

    def get_default_value_in_param(self, param=None):
        default_value = self.get_default_value_from_override(param)
        if default_value != self.missing_value:
            return default_value
        if 'default' in param.keys():
            return param['default']
        if 'schema' in param.keys():
            if 'default' in param['schema']:
                return param['schema']['default']
        return self.missing_value
    
    @property
    def missing_value(self):
        return -99999

    def get_decorator_string(self):
        string = ''
        for i, decorator in enumerate(self.decorators):
            if i == 0:
                string += "@" + decorator + '\n'
            else:
                string += self.add_indent() + "@" + decorator + '\n'
        return string
    
    @property
    def internal_function_prefix(self):
        return "_"

    def get_request_get_template(self, endpoint_metadata_name, endpoint, body_kwargs, 
    include_response_parsing: bool=False):
        string = self.add_indent() + f"""def """
        is_internal_function = endpoint_metadata_name in self.internal_functions
        if is_internal_function:
            string += self.internal_function_prefix
        string += f"""{endpoint_metadata_name}(self,"""
        # store default parameters to add them later.
        default_parameters = {}
        for param in body_kwargs:
            if param['name'] in self.inherited_properties:
                continue
            default_parameter = self.get_default_value_in_param(param)
            if default_parameter != self.missing_value:
                if isinstance(default_parameter, str):
                    default_parameter = '"' + str(default_parameter) + '"'
                # string += "=" + str(default_parameter)
                default_parameters[param['name']] = str(default_parameter)
                continue
            string +=param['name']
            string +=  ', '
        for k, default_parameter_string in default_parameters.items():
            string += k + '=' + str(default_parameter_string) + ', '
        string += '**kwargs):\n'
        self.indent_level += 1
        string += self.add_indent() + f"""return requests.get(\n"""
        self.indent_level += 1
        string += self.add_indent() + f"""url='{self.url + endpoint}',\n"""
        string += self.add_indent () + 'params=dict(\n'
        self.indent_level += 1
        default_arguments = []
        for param in body_kwargs:
            default_parameter = self.get_default_value_in_param(param)
            if default_parameter != self.missing_value:
                default_arguments.append(default_parameter)
                string += self.add_indent() + param['name'] + '=' + param['name'] + ', '
            elif param['name'] in self.inherited_properties:
                string += self.add_indent() + param['name'] + '=' + 'self.' + param['name'] + ', '
            else:
                string += self.add_indent() + param['name'] + '=' + param['name'] + ', '
            string += '\n'
        string += self.add_indent() + '))'
        if include_response_parsing:
            string += self.response_type_dict[self.get_response_type(endpoint)]
        self.indent_level -= 3
        return string, default_arguments

    @property
    def indenter(self):
        return '\t'
    
    def get_request_post_template(self, endpoint_metadata_name, endpoint, body_kwargs, 
    include_response_parsing=False):
        string = self.add_indent() + f"""def """
        is_internal_function = endpoint_metadata_name in self.internal_functions
        if is_internal_function:
            string += self.internal_function_prefix
        string += f"""{endpoint_metadata_name}(self, """
        # string = self.add_indent() + f"""def {endpoint_metadata_name}(self,"""
        # Store default parameters so you can add them last
        default_parameters = {}
        for k, v in body_kwargs:
            if k in self.inherited_properties:
                continue
            if k in self.override_param_defaults.keys():
                default_parameter = self.get_default_value_from_override_by_param_name(k)
            else:
                default_parameter = self.get_default_value_in_param(v)
            if default_parameter != self.missing_value:
                if isinstance(default_parameter, str):
                    default_parameter = '"' + str(default_parameter) + '"'
                # string += "=" + str(default_parameter)
                default_parameters[k] = str(default_parameter)
                continue
            string += k
            string += ', '
        for k, default_param_string in default_parameters.items():
            string += k + "=" + default_param_string + ', '
        string += '**kwargs):\n'
        self.indent_level += 1
        string += self.add_indent() + '"""' + self.create_documentation(endpoint) + '"""\n'
        string += self.add_indent() + f"""return requests.post(\n"""
        self.indent_level += 1
        string += self.add_indent() + f"""url='{self.url + endpoint}',\n"""
        string += self.add_indent() + 'json=dict(\n'
        default_arguments = []
        self.indent_level += 1
        for k, v in body_kwargs:
            if 'default' in v.keys():
                default_arguments.append(v['default'])
                string += self.add_indent() + k + '=' + k + ', '
            elif k in self.inherited_properties:
                string += self.add_indent() + k + '=' + 'self.' + k + ','
            else:
                string += self.add_indent() + k + '=' + k + ', '
            string += '\n'
        string += self.add_indent() + '**kwargs))'
        if include_response_parsing:
            string += self.response_type_dict[self.get_response_type(endpoint)]
        self.indent_level = self.indent_level - 3
        return string, default_arguments

    def get_endpoint_metadata(self, endpoint):
        return self.data['paths'][endpoint]

    def get_response_content(self, endpoint):
        endpoint_metadata = self.get_endpoint_metadata(endpoint)
        if self.get_request_type(endpoint_metadata) == 'get':
            return self.data['paths'][endpoint]['get']['responses']['200']['content']
        elif self.get_request_type(endpoint_metadata) == 'post':
            return self.data['paths'][endpoint]['post']['responses']['200']['content']
    @property
    def response_type_dict(self):
        return {
        'json': '.json()',
        'html': '.content'
    }    

    def get_response_type(self, endpoint):
        if 'json' in list(self.get_response_content(endpoint).keys())[0]:
            return 'json'
        if 'html' in list(self.get_response_content(endpoint).keys())[0]:
            return 'html'
    
    def create_function_string(self):
        endpoint_metadatas_dict = {}
        for path in self.data['paths'].keys():
            func_string, default_args = self.create_endpoint_metadata_string(path)
            new_func = create_function(func_string, function_name=path.split('/')[-1], default_arguments=tuple(default_args))
            endpoint_metadatas_dict.update({new_func.__name__: func_string})
        return endpoint_metadatas_dict

    def to_python_file(self, class_name, filename='api.py', import_strings=[], include_response_parsing=True):
        """
        Args:
            class_name: THe name of the class
            internal_functions: The name of the internal functions
        """
        self.write_header(filename)
        self.write_imports(filename, import_strings)
        self.write_constructor(filename, class_name=class_name, inherited_properties=self.inherited_properties)
        self.indent_level += 1
        endpoint_metadatas_dict = {}
        func_strings = []
        for path in self.data['paths'].keys():
            func_string = self.create_endpoint_metadata_string(
                path, 
                include_response_parsing=include_response_parsing,
            )
            func_strings.append(func_string)
        self.write_python_instance_methods(func_strings, filename=filename)
    
    def create_function_dict(self):
        endpoint_metadatas_dict = {}
        for path in self.data['paths'].keys():
            func_string, default_args = self.create_endpoint_metadata_string(path)
            new_func = create_function(func_string, function_name=path.split('/')[-1], default_arguments=tuple(default_args))
            new_func.__doc__ = self.create_documentation(path)
            endpoint_metadatas_dict.update({new_func.__name__: new_func})
        return endpoint_metadatas_dict
