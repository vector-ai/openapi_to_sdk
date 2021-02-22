"""SDK Automation
"""
import json
import requests
from typing import List, Dict
from .function import create_function
from .writer import PythonWriter

class PythonSDKBuilder(PythonWriter):
    def __init__(self, url: str='', sample_endpoint: str='', 
    inherited_properties: List[str]=[], json_fn: str=None, decorators: Dict[str, str]={}):
        """
        Args:
            url: 
            Sample endpoint: Endpoint for quick testing 
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
        endpoint_metadata_name = endpoint.split('/')[-1]
        endpoint_metadata = self.data['paths'][endpoint]
        body_kwargs = self.get_body_kwargs(endpoint_metadata)
        return self.get_request_template(
            endpoint_metadata_name, 
            endpoint, 
            self.get_request_type(endpoint_metadata), body_kwargs,
            include_response_parsing)
        
    def get_body_kwargs(self, endpoint_metadata):
        if self.get_request_type(endpoint_metadata) == 'post':
            return list(self.get_body_info(endpoint_metadata).items())
        if self.get_request_type(endpoint_metadata) == 'get':
            return self.get_body_info(endpoint_metadata)
    
    def get_request_template(self, endpoint_metadata_name, endpoint, endpoint_metadata_type, 
    body_kwargs, include_response_parsing):
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

    def get_default_value_in_param(self, param):
        if 'default' in param.keys():
            return param['default']
        if 'schema' in param.keys():
            if 'default' in param['schema']:
                return param['schema']['default']

    def get_decorator_string(self):
        string = ''
        for decorator in self.decorators:
            string += "@" + decorator + '\n'
        return string
    

    def get_request_get_template(self, endpoint_metadata_name, endpoint, body_kwargs, 
    include_response_parsing: bool=False):
        string = self.add_indent() + f"""def {endpoint_metadata_name}(self,"""
        for param in body_kwargs:
            if param['name'] in self.inherited_properties:
                continue
            string +=param['name'] + ', '
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
            if default_parameter is not None:
                default_arguments.append(default_parameter)
                continue
            elif param['name'] in self.inherited_properties:
                string += self.add_indent() + param['name'] + '=' + 'self.' + param['name'] + ', '
            else:
                string += self.add_indent() + param['name'] + '=' + param['name'] + ', '
            string += '\n'
        string += self.add_indent() + '**kwargs))'
        if include_response_parsing:
            string += self.response_type_dict[self.get_response_type(endpoint)]
        self.indent_level -= 3
        return string, default_arguments

    @property
    def indenter(self):
        return '\t'
    
    def get_request_post_template(self, endpoint_metadata_name, endpoint, body_kwargs, include_response_parsing=False):
        string = self.add_indent() + f"""def {endpoint_metadata_name}(self,"""
        for k, v in body_kwargs:
            if k in self.inherited_properties:
                continue
            string += k + ', '
        string += '):\n'
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
                continue
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
        self.write_header(filename)
        self.write_imports(filename, import_strings)
        self.write_constructor(filename, class_name=class_name, inherited_properties=self.inherited_properties)
        self.indent_level += 1
        endpoint_metadatas_dict = {}
        func_strings = []
        for path in self.data['paths'].keys():
            func_string = self.create_endpoint_metadata_string(path, 
            include_response_parsing=include_response_parsing)
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
