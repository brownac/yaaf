from consumers.api import FooBarBazService

async def get(service: FooBarBazService):
    return {"message": f"Hello from {service.get_name()}"}
