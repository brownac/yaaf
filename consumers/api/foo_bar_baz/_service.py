from yaaf import service


@service("FooBarBazService", aliases=["FooBar", "fbb"])
class FooBarBazService:
    def __init__(self) -> None:
        self.name = "foo_bar_baz_service"

    def get_name(self) -> str:
        return self.name


service = FooBarBazService()
