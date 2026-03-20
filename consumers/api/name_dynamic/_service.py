from yaaf import service


@service("NameService")
class NameService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}"


service = NameService
