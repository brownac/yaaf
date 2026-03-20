# Preferred: Import directly from the service module
from consumers.api.foo_bar_baz._service import FooBarBazService


async def get(service: FooBarBazService):
    return {"message": f"Hello from {service.get_name()}"}
