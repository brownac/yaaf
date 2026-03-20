from yaaf import service


@service("UsersService")
class UsersService:
    def get_user(self, user_id: str) -> dict[str, str]:
        return {"id": user_id, "name": "Austin"}


service = UsersService()
