# Vector API to SDK.

Python SDK for API automation.
Currently supports FastAPI implementation.

It is used as below:

```{python}
from automation_tool.sdk_automation import PythonSDKBuilder
sdk = PythonSDKBuilder(
    url="https://api.vctr.ai",
    inherited_properties=['username', 'api_key'],
    decorators=['retry()'],
)
sdk.to_python_file(import_strings=['from vectorai.api.utils import retry'])
```

Sample Output: 
```
# This python file is auto-generated. Please do not edit.
from vectorai.api.utils import retry


class ViAPIClient:
	def __init__(self, username, api_key, ):
		self.username = username		
		self.api_key = api_key		

	@retry()
	def request_api_key(self,email, description, referral_code, ):
		"""Request an api key
Make sure to save the api key somewhere safe. If you have a valid referral code, you can recieve the api key more quickly.
    
Args
========
username: Username you'd like to create, lowercase only
email: Email you are using to sign up
description: Description of your intended use case
referral_code: The referral code you've been given to allow you to register for an api key before others

"""
		return requests.post(
			url='https://api.vctr.ai//project/request_api_key',
			json=dict(
				username=self.username,
				email=email, 
				description=description, 
				**kwargs)).json()

```

# Improvements

- Add more documentation.
