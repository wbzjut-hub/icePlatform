export enum Role {
    AFF_1 = "正方一辩",
    AFF_2 = "正方二辩",
    AFF_3 = "正方三辩",
    AFF_4 = "正方四辩",
    NEG_1 = "反方一辩",
    NEG_2 = "反方二辩",
    NEG_3 = "反方三辩",
    NEG_4 = "反方四辩"
}

export enum GamePhase {
    NOT_STARTED = "not_started",
    OPENING = "opening",
    REBUTTAL = "rebuttal",
    FREE_DEBATE = "free_debate",
    CLOSING = "closing",
    GAME_OVER = "game_over"
}

export interface Player {
    id: number
    role: Role
    is_alive: boolean
    memory: string[]
}

export interface GameState {
    topic: string
    players: Player[]
    phase: GamePhase
    turn_index: number
    current_speaker_role?: Role
    history: string[]
    hidden_history: string[]
    winner: string | null
}
