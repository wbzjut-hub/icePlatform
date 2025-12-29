import random
import json
from datetime import datetime
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.db.session import SessionLocal
from app.models.setting import SystemSetting
from app.core.config import settings
from app.schemas.game import GameState, Player, Role, GamePhase

_GLOBAL_GAME_STATE = GameState(players=[])

# 定义发言顺序队列
# ... (same as before)
_SPEECH_SEQUENCE = [
    (Role.AFF_1, GamePhase.OPENING),
    (Role.NEG_1, GamePhase.OPENING),
    (Role.NEG_2, GamePhase.REBUTTAL),
    (Role.AFF_2, GamePhase.REBUTTAL),
    (Role.AFF_3, GamePhase.REBUTTAL),
    (Role.NEG_3, GamePhase.REBUTTAL),
    (Role.AFF_1, GamePhase.FREE_DEBATE),
    (Role.NEG_1, GamePhase.FREE_DEBATE),
    (Role.AFF_2, GamePhase.FREE_DEBATE),
    (Role.NEG_2, GamePhase.FREE_DEBATE),
    (Role.AFF_3, GamePhase.FREE_DEBATE),
    (Role.NEG_3, GamePhase.FREE_DEBATE),
    (Role.NEG_4, GamePhase.CLOSING),
    (Role.AFF_4, GamePhase.CLOSING)
]

class GameService:
    @staticmethod
    def get_game_state() -> GameState:
        return _GLOBAL_GAME_STATE

    @staticmethod
    def start_game(topic: str) -> GameState:
        global _GLOBAL_GAME_STATE
        
        # 初始化 8 个玩家
        players = []
        players.append(Player(id=1, role=Role.AFF_1))
        players.append(Player(id=2, role=Role.AFF_2))
        players.append(Player(id=3, role=Role.AFF_3))
        players.append(Player(id=4, role=Role.AFF_4))
        players.append(Player(id=5, role=Role.NEG_1))
        players.append(Player(id=6, role=Role.NEG_2))
        players.append(Player(id=7, role=Role.NEG_3))
        players.append(Player(id=8, role=Role.NEG_4))
            
        _GLOBAL_GAME_STATE = GameState(
            topic=topic,
            players=players,
            phase=GamePhase.NOT_STARTED,
            turn_index=-1, 
            history=[f"辩论赛即将开始，辩题：{topic}"],
            hidden_history=["Game Init"]
        )
        return _GLOBAL_GAME_STATE

    @staticmethod
    def next_step() -> GameState:
        state = _GLOBAL_GAME_STATE
        if state.phase == GamePhase.GAME_OVER:
            return state

        next_idx = state.turn_index + 1
        
        # 检查是否结束
        if next_idx >= len(_SPEECH_SEQUENCE):
            state.phase = GamePhase.GAME_OVER
            state.current_speaker_role = None
            state.history.append("=== 辩论赛结束 ===")
            state.winner = "待定 (请观众投票)" 
            return state

        # 获取下一个发言者和阶段
        role, phase = _SPEECH_SEQUENCE[next_idx]
        state.turn_index = next_idx
        state.phase = phase
        state.current_speaker_role = role
        
        # 找到对应玩家
        player = next(p for p in state.players if p.role == role)
        
        # --- 模拟 AI 发言 ---
        content = GameService._mock_speech(state.topic, player, phase)
        
        state.history.append(content)
        return state

    # ... helper to get LLM ...
    @staticmethod
    def _get_llm():
        db = SessionLocal()
        try:
            # Fetch config from DB
            db_api_key = db.query(SystemSetting).filter(SystemSetting.key == "openai_api_key").first()
            db_base_url = db.query(SystemSetting).filter(SystemSetting.key == "openai_base_url").first()
            
            final_api_key = db_api_key.value if (db_api_key and db_api_key.value) else settings.OPENAI_API_KEY
            final_base_url = db_base_url.value if (db_base_url and db_base_url.value) else settings.OPENAI_BASE_URL
            
            if not final_api_key:
                return None
            
            # 自动判断模型
            model = "gpt-3.5-turbo"
            if final_base_url and "deepseek" in final_base_url:
                model = "deepseek-chat"
            elif final_base_url and "moonshot" in final_base_url:
                model = "moonshot-v1-8k"

            return ChatOpenAI(
                model=model,
                api_key=final_api_key,
                base_url=final_base_url,
                temperature=0.7,
                max_tokens=300 # Default limit
            )
        except Exception as e:
            print(f"Error init LLM: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    def _mock_speech(topic: str, player: Player, phase: GamePhase) -> str:
        llm = GameService._get_llm()
        state = _GLOBAL_GAME_STATE
        
        prefix = f"【{player.role.value}】"
        side = "正方" if "正" in player.role.value else "反方"
        
        if not llm:
            return f"{prefix} (系统提示): 未配置 API Key，无法生成 AI 发言。"

        try:
            # 1. System Prompt
            system_prompt = f"""你正在参加一场激烈的辩论赛。
你的角色是：{side}{player.role.value}。
辩题是：{topic}。
你的立场是：{'支持' if side == '正方' else '反对'}该辩题。
请用犀利、有逻辑的语言进行辩论。不要使用“作为AI”等出戏的词汇。直接代入角色。"""

            # 2. Phase Prompt
            user_instruction = ""
            limit_instruction = "字数限制：200字以内。"
            
            # 获取上一条发言作为上下文
            last_speech = ""
            if state.history and len(state.history) > 1: # >1 because init msg
                 last_speech = f"\n上一位辩手的发言：{state.history[-1]}\n"

            if phase == GamePhase.OPENING:
                user_instruction = f"现在是{side}立论环节。请发表你的开篇立论。阐述核心观点。{limit_instruction}"
            
            elif phase == GamePhase.REBUTTAL:
                user_instruction = f"现在是驳论/攻辩环节。{last_speech}请针对上一位发言或对方核心观点进行驳斥。{limit_instruction}"
            
            elif phase == GamePhase.FREE_DEBATE:
                llm.max_tokens = 100 # Stricter limit enforcement
                user_instruction = f"现在是自由辩论环节。{last_speech}请进行快速反击。要求：**短平快，字字珠玑，不要长篇大论！强烈限制在50字以内！**"
            
            elif phase == GamePhase.CLOSING:
                user_instruction = f"现在是总结陈词环节。请总结你方观点，升华主题，并回击对方漏洞。{limit_instruction}"

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_instruction)
            ]
            
            # Invoke
            response = llm.invoke(messages)
            return f"{prefix}: {response.content}"
            
        except Exception as e:
            return f"{prefix} (AI Error): {str(e)}"
