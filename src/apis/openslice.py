from fastapi import HTTPException, Response
from json import JSONDecodeError

class OpenSlice:
    _url: str

    def __init__(self, url: str):
        self._url = url

    def handle_response_not_ok(self, response: Response):
        try:
            detail = response.json()
        except JSONDecodeError:
            detail = "Timeout has occurred"
        except Exception as e:
            detail = f"An unexpected error occurred: {str(e)}"
        raise HTTPException(status_code=response.status_code, detail=detail)
