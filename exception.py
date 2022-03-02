class API_Status(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        self.message = f'server is unavailable {self.message}'
        return self.message


class HomeWorkKeyError(Exception):
    def __init__(self, key) -> None:
        self.key = key
        super().__init__(self.key)

    def __str__(self) -> str:
        self.message = f'Homework {self.key} Error in API Server response'
        return self.message


class BotSendMessageError(Exception):
    def __init__(self) -> None:
        super().__init__(self)

    def __str__(self):
        return 'Message don`t send'
