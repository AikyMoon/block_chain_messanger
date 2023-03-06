from termcolor import colored

class VerifyError(Exception):

    def __init__(self, *args: object) -> None:
        if args:
            self.message = args
        else:
            self.message = None
    

    def __str__(self) -> str:
        if self.message:
            return colored(f"Сообщение пользователя {self.message} было изменено", 'red')
        return colored("Сообщение было изменено", 'red')