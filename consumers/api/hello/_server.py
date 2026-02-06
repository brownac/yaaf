from consumers.api import HelloService
from yaaf import Request


async def get(request: Request, service: HelloService) -> dict[str, str]:
    return {"message": service.message(), "path": request.path}
