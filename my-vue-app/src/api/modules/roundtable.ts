import request from '@/utils/request';

export interface RoundtableExpert {
    id: string;
    name: string;
    description: string;
    system_prompt: string;
    domain?: string;
}

export interface DiscussionMessage {
    speaker: string;
    content: string;
}

export interface RoundtableState {
    topic: string;
    experts: RoundtableExpert[];
    phase: 'not_started' | 'selecting_experts' | 'discussing' | 'summarizing' | 'completed';
    current_speaker_idx: number;
    current_speaker_name?: string;
    discussion_history: DiscussionMessage[];
    round_count: number;
    has_consensus: boolean;
    summary?: string;
}

// 启动圆桌会议
export const startRoundtableApi = (topic: string): Promise<RoundtableState> => {
    return request.post('/roundtable/start', { topic });
};

// 下一位专家发言
export const nextSpeakerApi = (): Promise<RoundtableState> => {
    return request.post('/roundtable/next');
};

// 获取当前状态
export const getRoundtableStatusApi = (): Promise<RoundtableState> => {
    return request.get('/roundtable/status');
};

// 生成总结并结束
export const summarizeRoundtableApi = (): Promise<RoundtableState> => {
    return request.post('/roundtable/summarize');
};

// 重置会议
export const resetRoundtableApi = (): Promise<RoundtableState> => {
    return request.post('/roundtable/reset');
};
