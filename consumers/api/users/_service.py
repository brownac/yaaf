class Service:
    def get_user(self, user_id: str) -> dict[str, str]:
        return {"id": user_id, "name": "Austin"}


service = Service()
