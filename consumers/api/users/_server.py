from consumers.api import UsersService
from yaaf.types import Params


async def get(params: Params, service: UsersService) -> dict[str, str]:
    user_id = params.get("id", "1")
    return service.get_user(user_id)
