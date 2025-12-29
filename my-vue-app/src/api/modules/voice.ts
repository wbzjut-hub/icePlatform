import request from '@/utils/request'

export const voiceApi = {
    transcribe(audioFile: File) {
        const formData = new FormData()
        formData.append('file', audioFile)
        return request.post<{ text: string }>('/voice/transcribe', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })
    }
}