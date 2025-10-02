import json


class Code(Exception):
    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f'Error {code}: {message}')

    def json(self) :
        information = {"code": self.code, "message": self.message}
        return json.dumps(information)