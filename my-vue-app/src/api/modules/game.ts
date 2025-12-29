import request from '@/utils/request'
import type { GameState } from '@/types/game'

export const startGameApi = (topic: string) => {
    return request.post<any, GameState>('/game/start', { topic })
}

export const nextStepApi = () => {
    return request.post<any, GameState>('/game/next')
}

export const getGameStatusApi = () => {
    return request.get<any, GameState>('/game/status')
}
