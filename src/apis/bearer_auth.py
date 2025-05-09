import requests

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
        
    def __call__(self, request):
        request.headers["authorization"] = "Bearer " + self.token
        return request
