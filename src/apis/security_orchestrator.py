import requests

from typing import Any

class SecurityOrchestrator:
    _url: str

    def __init__(self, url: str):
        self._url = url

    def send_mspl(self, mspl: Any) -> bool:
        headers = {
            "Content-Type": "application/xml"
        }
        response = requests.post(f"{self._url}/meservice",
                                headers=headers,
                                data=mspl)
        return response.status_code == requests.codes.ok
