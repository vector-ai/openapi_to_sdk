# from openapi_to_sdk.sdk_automation import PythonSDKBuilder
# def test_smoke():
#     sdk = PythonSDKBuilder(
#         inherited_properties=['username', 'api_key'],
#         decorators=['retry()'],
#         url='https://api.vctr.ai/'
#     )
#     sdk.to_python_file(class_name='ViAPIClient', import_strings=['from vectorai.api.utils import retry'], 
#     include_response_parsing=False)
#     assert True


from openapi_to_sdk.sdk_automation import PythonSDKBuilder
def test_smoke():
    sdk = PythonSDKBuilder(
        url="https://api.vctr.ai",
        inherited_properties=['username', 'api_key'],
        decorators=[
            # 'retry()', 
            "return_curl_or_response('json')"],
    )
    sdk.to_python_file(
        class_name="ViAPIClient", 
        filename='api.py',
        import_strings=['import requests', 'from vectorai.api.utils import retry, return_curl_or_response'], 
        internal_functions=[
            "list_collections",
            "create_collection",
            "search"
        ]
    )

def test_import():
    import api
    import os
    from api import ViAPIClient
    vi = ViAPIClient(os.environ['VI_USERNAME'], os.environ['VI_API_KEY'])
    assert len(vi._list_collections()) > 0
