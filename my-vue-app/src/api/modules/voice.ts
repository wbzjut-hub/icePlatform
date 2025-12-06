import request from '@/utils/request'

export const transcribeAudioApi = (file: Blob) => {
    const formData = new FormData()
    formData.append('file', file)
    return request.post<any, { text: string }>('/api/v1/voice/transcribe', formData, {
        headers: { 'Content-Type': 'multipart/form-data' } // axios 会自动处理，但这行显式声明更安全
    })
}