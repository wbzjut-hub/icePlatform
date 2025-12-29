from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

class Role(str, Enum):
    # 正方 (Affirmative)
    AFF_1 = "正方一辩"
    AFF_2 = "正方二辩"
    AFF_3 = "正方三辩"
    AFF_4 = "正方四辩"
    # 反方 (Negative)
    NEG_1 = "反方一辩"
    NEG_2 = "反方二辩"
    NEG_3 = "反方三辩"
    NEG_4 = "反方四辩"

class GamePhase(str, Enum):
    NOT_STARTED = "not_started"
    OPENING = "opening"         # 立论
    REBUTTAL = "rebuttal"       # 驳论/攻辩
    FREE_DEBATE = "free_debate" # 自由辩论
    CLOSING = "closing"         # 总结陈词
    GAME_OVER = "game_over"

class Player(BaseModel):
    id: int
    role: Role
    is_alive: bool = True # 辩论赛始终为 True
    memory: List[str] = [] 

class GameState(BaseModel):
    topic: str = "" # 辩题
    players: List[Player]
    phase: GamePhase = GamePhase.NOT_STARTED
    turn_index: int = 0  # 当前在 speech_sequence 中的索引
    current_speaker_role: Optional[Role] = None # 当前应该是谁发言
    history: List[str] = [] 
    hidden_history: List[str] = []
    winner: Optional[str] = None
