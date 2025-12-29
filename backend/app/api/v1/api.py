from fastapi import APIRouter
from app.api.v1.endpoints import menus, cards, todos, ai, logs, system, voice, weather, game, roundtable


api_router = APIRouter()

api_router.include_router(menus.router, prefix="/menus", tags=["Menus"])
api_router.include_router(cards.router, prefix="/cards", tags=["Cards"])
api_router.include_router(todos.router, prefix="/todos", tags=["Todos"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])
api_router.include_router(logs.router, prefix="/logs", tags=["Logs"])
api_router.include_router(system.router, prefix="/system", tags=["System"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])
api_router.include_router(weather.router, prefix="/weather", tags=["Weather"])
api_router.include_router(game.router, prefix="/game", tags=["Game"])
api_router.include_router(roundtable.router, prefix="/roundtable", tags=["Roundtable"])