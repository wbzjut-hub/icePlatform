from fastapi import APIRouter, Body
from app.services.game_service import GameService
from app.schemas.game import GameState

router = APIRouter()

@router.post("/start", response_model=GameState)
def start_game(topic: str = Body(..., embed=True)):
    """
    初始化并开始新游戏
    """
    return GameService.start_game(topic)

@router.post("/next", response_model=GameState)
def next_step():
    """
    推进游戏一步
    """
    return GameService.next_step()

@router.get("/status", response_model=GameState)
def get_game_status():
    """
    获取当前游戏状态
    """
    return GameService.get_game_state()
