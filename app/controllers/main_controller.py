from fastapi import APIRouter
from fastapi_restful.cbv import cbv

main_router = APIRouter()

@cbv(main_router)
class MainController:
    @main_router.get('/')
    async def root(self) -> dict[str, str]:
        return { "message": "Hello World" }
    
    @main_router.get('/ping')
    async def ping(self) -> dict[str, str]:
        return { "ping": "pong" }
        
        