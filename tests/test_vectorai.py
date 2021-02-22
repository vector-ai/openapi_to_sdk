from openapi_to_sdk.sdk_automation import PythonSDKBuilder
def test_smoke():
    sdk = PythonSDKBuilder(
        inherited_properties=['username', 'api_key'],
        decorators=['retry()'],
        url='https://api.vctr.ai/'
    )
    sdk.to_python_file(class_name='ViAPIClient', import_strings=['from vectorai.api.utils import retry'], 
    include_response_parsing=False)
    assert True
