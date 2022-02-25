

class API_Status(Exception):
    def __init__(self, response):
        self.status_code = response.status_code
        super().__init__(self.status_code)

    def __str__(self):
        self.message = f'Server is unavailable, code {self.status_code}'
        return self.message

class HomeWorkKeyError(Exception):
    def __init__(self, key) -> None:
        self.key = key
        super().__init__(self.key)

    def __str__(self) -> str:
        self.message = f'Homework {self.key} Error in API Server response'
        return self.message