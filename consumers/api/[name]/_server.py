from consumers.api import NameService
from yaaf.types import Params


async def get(params: Params, service: NameService) -> dict[str, str]:
    return {"message": service.greet(params["name"])}
