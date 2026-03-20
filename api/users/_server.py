from yaaf.types import Params

# Preferred: Import directly from the service module
from api.users._service import UsersService


async def get(params: Params, service: UsersService) -> dict[str, str]:
    user_id = params.get("id", "1")
    return service.get_user(user_id)
