from yaaf.types import Params

from api.name_dynamic._service import NameService


async def get(params: Params, service: NameService) -> dict[str, str]:
    return {"message": service.greet(params["name"])}
