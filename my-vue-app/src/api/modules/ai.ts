import request from '@/utils/request'

export interface ChatSession {
    id: string;
    title: string;
    created_at: string;
}

export interface ChatMessage {
    id?: string;
    role: 'user' | 'assistant';
    content: string;
    created_at?: string;
    // 🌟 新增 usage
    usage?: {
        prompt_tokens: number;
        completion_tokens: number;
        total_tokens: number;
    };
}

export interface ChatResponse {
    reply: string;
    session_id: string;
    session_title: string;
    // 🌟 新增 usage
    usage?: {
        prompt_tokens: number;
        completion_tokens: number;
        total_tokens: number;
    };
    // 🌟 新增 actions (执行的工具列表)
    actions?: string[];
}

export interface Workflow {
    id?: string;
    name: string;
    description: string;
    system_prompt: string;
    tools_config: string[];
}

export const getSessionsApi = () => request.get<any, ChatSession[]>('/ai/sessions')
export const getMessagesApi = (sessionId: string) => request.get<any, ChatMessage[]>(`/ai/sessions/${sessionId}/messages`)
export const deleteSessionApi = (sessionId: string) => request.delete(`/ai/sessions/${sessionId}`)

export const chatWithAiApi = (message: string, sessionId?: string | null, workflowId: string = 'wf_agent') =>
    request.post<any, ChatResponse>('/ai/chat', { message, session_id: sessionId, workflow_id: workflowId })

export const getWorkflowsApi = () => request.get<any, Workflow[]>('/ai/workflows')
export const createWorkflowApi = (data: Workflow) => request.post<any, Workflow>('/ai/workflows', data)
export const updateWorkflowApi = (id: string, data: Workflow) => request.put<any, Workflow>(`/ai/workflows/${id}`, data)
export const deleteWorkflowApi = (id: string) => request.delete(`/ai/workflows/${id}`)