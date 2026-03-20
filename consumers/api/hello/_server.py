from yaaf import Request

# Preferred: Import directly from the service module
from consumers.api.hello._service import HelloService


async def get(request: Request, service: HelloService) -> dict[str, str]:
    return {"message": service.message(), "path": request.path}
