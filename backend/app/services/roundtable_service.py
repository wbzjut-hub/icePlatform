from typing import List, Dict, Optional, Any
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.db.session import SessionLocal
from app.models.setting import SystemSetting
from app.models.workflow import Workflow
from app.core.config import settings
from pydantic import BaseModel
from enum import Enum


class RoundtablePhase(str, Enum):
    NOT_STARTED = "not_started"
    SELECTING_EXPERTS = "selecting_experts"
    DISCUSSING = "discussing"
    SUMMARIZING = "summarizing"
    COMPLETED = "completed"


class RoundtableExpert(BaseModel):
    id: str
    name: str
    description: str
    system_prompt: str
    domain: Optional[str] = None


class RoundtableState(BaseModel):
    topic: str = ""
    experts: List[RoundtableExpert] = []
    phase: RoundtablePhase = RoundtablePhase.NOT_STARTED
    current_speaker_idx: int = -1
    current_speaker_name: Optional[str] = None
    discussion_history: List[Dict[str, str]] = []  # [{speaker, content}]
    round_count: int = 0
    has_consensus: bool = False
    should_continue: bool = True  # 主持人判断是否继续
    summary: Optional[str] = None


# Global state for roundtable
_ROUNDTABLE_STATE = RoundtableState()


class RoundtableService:
    """圆桌会议服务 - 协调专家讨论"""
    
    # 领域关键词映射
    DOMAIN_KEYWORDS = {
        "金融核心": ["股票", "基金", "投资", "风险", "宏观", "加密", "交易", "金融", "货币", "市场"],
        "科技前沿": ["代码", "算法", "架构", "高并发", "数据", "系统", "编程", "技术", "开发", "软件", "AI"],
        "安全法务": ["安全", "漏洞", "合规", "法律", "隐私", "攻击", "防护"],
        "产品战略": ["产品", "增长", "用户", "商业", "创业", "市场", "战略"],
        "设计创意": ["UI", "设计", "游戏", "美学", "体验", "视觉", "交互"],
        "科学理论": ["模型", "统计", "科学", "理论", "物理", "数学", "实验"],
        "人文社科": ["历史", "心理", "行为", "周期", "社会", "文化"]
    }
    
    EXPERT_DOMAINS = {
        "Macro Strategist": "金融核心",
        "Quant Analyst": "金融核心",
        "Risk Manager": "金融核心",
        "Crypto Native": "金融核心",
        "System Architect": "科技前沿",
        "Algo Geek": "科技前沿",
        "DevOps Master": "科技前沿",
        "Data Alchemist": "科技前沿",
        "Security Spec Ops": "安全法务",
        "Legal Counsel": "安全法务",
        "Product Visionary": "产品战略",
        "Startup Founder": "产品战略",
        "User Researcher": "产品战略",
        "Design Lead": "设计创意",
        "Game Producer": "设计创意",
        "Space Architect": "设计创意",
        "Complex Systems Physicist": "科学理论",
        "Statistician": "科学理论",
        "Evolutionary Biologist": "科学理论",
        "Historian": "人文社科",
        "Behavioral Psychologist": "人文社科",
    }
    
    @staticmethod
    def get_state() -> RoundtableState:
        return _ROUNDTABLE_STATE
    
    @staticmethod
    def _get_llm(max_tokens: int = 500):
        db = SessionLocal()
        try:
            db_api_key = db.query(SystemSetting).filter(SystemSetting.key == "openai_api_key").first()
            db_base_url = db.query(SystemSetting).filter(SystemSetting.key == "openai_base_url").first()
            
            final_api_key = db_api_key.value if (db_api_key and db_api_key.value) else settings.OPENAI_API_KEY
            final_base_url = db_base_url.value if (db_base_url and db_base_url.value) else settings.OPENAI_BASE_URL
            
            if not final_api_key:
                return None
            
            model = "deepseek-chat"
            if final_base_url and "moonshot" in final_base_url:
                model = "moonshot-v1-8k"
            elif not final_base_url or "openai" in str(final_base_url):
                model = "gpt-3.5-turbo"

            return ChatOpenAI(
                model=model,
                api_key=final_api_key,
                base_url=final_base_url,
                temperature=0.7,
                max_tokens=max_tokens
            )
        except Exception as e:
            print(f"Error init LLM: {e}")
            return None
        finally:
            db.close()
    
    @staticmethod
    def _get_all_experts() -> List[Workflow]:
        db = SessionLocal()
        try:
            workflows = db.query(Workflow).filter(
                ~Workflow.id.in_(["wf_general", "wf_agent"])
            ).all()
            return workflows
        finally:
            db.close()
    
    @staticmethod
    def _get_expert_domain(expert_name: str) -> str:
        for key, domain in RoundtableService.EXPERT_DOMAINS.items():
            if key in expert_name:
                return domain
        return "通用"
    
    @staticmethod
    def _select_experts_by_topic(topic: str, all_experts: List[Workflow], count: int = 6) -> List[RoundtableExpert]:
        llm = RoundtableService._get_llm(max_tokens=300)
        
        if not llm:
            import random
            selected = random.sample(all_experts, min(count, len(all_experts)))
            return [RoundtableExpert(
                id=e.id, name=e.name, description=e.description,
                system_prompt=e.system_prompt,
                domain=RoundtableService._get_expert_domain(e.name)
            ) for e in selected]
        
        expert_list = "\n".join([f"- ID: {e.id}, 名称: {e.name}, 描述: {e.description}" for e in all_experts])
        
        prompt = f"""你是一位圆桌会议的组织者。根据以下议题，从专家列表中选择 {count} 位最相关的参会者。

议题: {topic}

专家列表:
{expert_list}

请返回一个 JSON 数组，包含选中专家的 ID。只返回 JSON，不要其他内容。
例如: ["id1", "id2", "id3", "id4", "id5", "id6"]"""

        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            selected_ids = json.loads(content)
            
            selected = []
            for expert in all_experts:
                if expert.id in selected_ids:
                    selected.append(RoundtableExpert(
                        id=expert.id,
                        name=expert.name,
                        description=expert.description,
                        system_prompt=expert.system_prompt,
                        domain=RoundtableService._get_expert_domain(expert.name)
                    ))
            
            if len(selected) < 5:
                remaining = [e for e in all_experts if e.id not in selected_ids]
                import random
                extra = random.sample(remaining, min(5 - len(selected), len(remaining)))
                for e in extra:
                    selected.append(RoundtableExpert(
                        id=e.id, name=e.name, description=e.description,
                        system_prompt=e.system_prompt,
                        domain=RoundtableService._get_expert_domain(e.name)
                    ))
            
            return selected[:7]
            
        except Exception as e:
            print(f"Expert selection error: {e}")
            import random
            selected = random.sample(all_experts, min(count, len(all_experts)))
            return [RoundtableExpert(
                id=e.id, name=e.name, description=e.description,
                system_prompt=e.system_prompt,
                domain=RoundtableService._get_expert_domain(e.name)
            ) for e in selected]
    
    @staticmethod
    def start_roundtable(topic: str) -> RoundtableState:
        global _ROUNDTABLE_STATE
        
        all_experts = RoundtableService._get_all_experts()
        selected_experts = RoundtableService._select_experts_by_topic(topic, all_experts)
        
        expert_names = [e.name for e in selected_experts]
        
        _ROUNDTABLE_STATE = RoundtableState(
            topic=topic,
            experts=selected_experts,
            phase=RoundtablePhase.DISCUSSING,
            current_speaker_idx=-1,
            discussion_history=[{
                "speaker": "主持人",
                "content": f"## 圆桌会议开始\n\n**议题**：{topic}\n\n**参会专家**：\n" + "\n".join([f"- {name}" for name in expert_names]) + "\n\n请各位专家从专业角度发表观点，可以提出质疑和不同意见。"
            }],
            round_count=0,
            has_consensus=False,
            should_continue=True
        )
        
        return _ROUNDTABLE_STATE
    
    @staticmethod
    def next_speaker() -> RoundtableState:
        state = _ROUNDTABLE_STATE
        
        if state.phase == RoundtablePhase.COMPLETED:
            return state
        
        if not state.experts:
            return state
        
        # 每轮结束后，主持人判断是否继续
        if state.current_speaker_idx == len(state.experts) - 1:
            state.round_count += 1
            # 主持人评估
            moderator_decision = RoundtableService._moderator_evaluate(state)
            state.discussion_history.append({
                "speaker": "主持人",
                "content": moderator_decision["comment"]
            })
            state.should_continue = moderator_decision["should_continue"]
            
            if not state.should_continue:
                # 自动生成总结
                return RoundtableService.generate_summary()
        
        # 移动到下一位专家
        state.current_speaker_idx = (state.current_speaker_idx + 1) % len(state.experts)
        
        current_expert = state.experts[state.current_speaker_idx]
        state.current_speaker_name = current_expert.name
        
        # 生成发言
        content = RoundtableService._generate_speech(current_expert, state)
        
        state.discussion_history.append({
            "speaker": current_expert.name,
            "content": content
        })
        
        return state
    
    @staticmethod
    def _moderator_evaluate(state: RoundtableState) -> Dict[str, Any]:
        """主持人评估讨论进展，决定是否继续"""
        llm = RoundtableService._get_llm(max_tokens=300)
        
        if not llm:
            return {"should_continue": state.round_count < 5, "comment": "请继续讨论。"}
        
        # 构建讨论摘要
        recent_history = state.discussion_history[-10:]
        history_text = "\n".join([f"【{h['speaker']}】: {h['content'][:100]}..." for h in recent_history])
        
        prompt = f"""你是一位专业的圆桌会议主持人。请评估当前讨论进展。

议题: {state.topic}
已进行轮数: {state.round_count}
讨论摘要:
{history_text}

请判断：
1. 讨论是否已经充分？各方观点是否都已表达？
2. 是否还有重要分歧需要进一步讨论？
3. 是否可以进入总结阶段？

请返回 JSON 格式：
{{
  "should_continue": true/false,
  "comment": "你的主持人点评（100字以内，用markdown格式）"
}}

只返回 JSON，不要其他内容。注意：至少讨论 5 轮才能结束。当前已讨论 {state.round_count} 轮。"""

        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            result = json.loads(content)
            return result
            
        except Exception as e:
            print(f"Moderator evaluation error: {e}")
            # 默认5轮后结束
            if state.round_count >= 5:
                return {"should_continue": False, "comment": "讨论已较为充分，进入总结阶段。"}
            return {"should_continue": True, "comment": "请继续深入讨论。"}
    
    @staticmethod
    def _generate_speech(expert: RoundtableExpert, state: RoundtableState) -> str:
        """生成专家发言 - 更加客观严肃"""
        llm = RoundtableService._get_llm(max_tokens=400)
        
        if not llm:
            return "(系统提示): 未配置 API Key，无法生成发言。"
        
        recent_history = state.discussion_history[-6:]
        history_text = "\n".join([f"【{h['speaker']}】: {h['content']}" for h in recent_history])
        
        # 更严肃、客观的提示词
        system_prompt = f"""{expert.system_prompt}

你正在参加一场**严肃的专业圆桌讨论会**。
议题是：{state.topic}

【重要要求】：
1. 保持客观、理性、专业的态度
2. 不要恭维或赞美其他专家
3. 如果有不同意见，直接提出，不要委婉客套
4. 用数据、事实、逻辑来支撑观点
5. 可以质疑其他专家的观点，指出潜在问题
6. 使用 Markdown 格式组织回答（可用加粗、列表、标题等）"""

        user_prompt = f"""最近的讨论:
{history_text}

当前是第 {state.round_count + 1} 轮。

请从你的专业角度发言：
- 直接表达观点，不要寒暄
- 如有不同意见，明确指出并说明理由
- 提供具体的见解或建议
- 字数：150-250字
- 使用 Markdown 格式"""

        try:
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            return response.content
        except Exception as e:
            return f"(发言生成错误): {str(e)}"
    
    @staticmethod
    def _check_consensus(state: RoundtableState) -> bool:
        if state.round_count >= 3:
            return True
        return False
    
    @staticmethod
    def generate_summary() -> RoundtableState:
        state = _ROUNDTABLE_STATE
        
        if state.phase == RoundtablePhase.COMPLETED:
            return state
        
        state.phase = RoundtablePhase.SUMMARIZING
        
        llm = RoundtableService._get_llm(max_tokens=1000)
        
        if not llm:
            state.summary = "未配置 API Key，无法生成总结。"
            state.phase = RoundtablePhase.COMPLETED
            return state
        
        all_history = "\n\n".join([f"【{h['speaker']}】: {h['content']}" for h in state.discussion_history])
        
        prompt = f"""请为以下圆桌讨论生成一份**完整、结构化的总结**。

议题: {state.topic}

讨论内容:
{all_history}

请使用 Markdown 格式输出，包含以下部分：

## 📋 核心结论
（讨论达成的主要共识，2-3点）

## 💡 关键洞察
（各专家贡献的重要观点，按专家或主题分类）

## ⚠️ 争议与分歧
（讨论中出现的不同意见）

## 🎯 行动建议
（基于讨论的具体可执行建议）

## 📌 注意事项
（潜在风险、限制条件）

总结要充分、全面、结构清晰。"""

        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            state.summary = response.content
        except Exception as e:
            state.summary = f"总结生成错误: {str(e)}"
        
        state.phase = RoundtablePhase.COMPLETED
        state.discussion_history.append({
            "speaker": "会议总结",
            "content": state.summary
        })
        
        return state
    
    @staticmethod
    def reset() -> RoundtableState:
        global _ROUNDTABLE_STATE
        _ROUNDTABLE_STATE = RoundtableState()
        return _ROUNDTABLE_STATE
