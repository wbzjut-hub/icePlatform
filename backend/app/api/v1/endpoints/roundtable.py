from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse
from app.services.roundtable_service import RoundtableService, RoundtableState
import json

router = APIRouter()


@router.post("/start", response_model=RoundtableState)
def start_roundtable(topic: str = Body(..., embed=True)):
    """
    启动圆桌会议
    - 根据议题自动选择 5-7 位相关专家
    - 返回初始状态和选中的专家列表
    """
    return RoundtableService.start_roundtable(topic)


@router.post("/next", response_model=RoundtableState)
def next_speaker():
    """
    推进到下一位专家发言
    """
    return RoundtableService.next_speaker()


@router.get("/status", response_model=RoundtableState)
def get_status():
    """
    获取当前圆桌会议状态
    """
    return RoundtableService.get_state()


@router.post("/summarize", response_model=RoundtableState)
def summarize():
    """
    结束讨论并生成总结
    """
    return RoundtableService.generate_summary()


@router.post("/reset", response_model=RoundtableState)
def reset():
    """
    重置圆桌会议
    """
    return RoundtableService.reset()
