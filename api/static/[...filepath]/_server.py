from yaaf_static import static_files


async def get(path_params, static=static_files("public")):
    return static(path_params)
