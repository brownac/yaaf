from yaaf import service

from api.users._service import UsersService


@service("HelloService")
class HelloService:
    def __init__(self, users: UsersService) -> None:
        self._users = users

    def message(self) -> str:
        user = self._users.get_user("1")
        return f"Hello from yaaf, {user['name']}"


service = HelloService
