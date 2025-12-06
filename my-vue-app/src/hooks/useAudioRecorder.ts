import { ref } from 'vue'

export function useAudioRecorder() {
    const isRecording = ref(false)
    const mediaRecorder = ref<MediaRecorder | null>(null)
    const audioChunks = ref<Blob[]>([])

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
            mediaRecorder.value = new MediaRecorder(stream)
            audioChunks.value = []

            mediaRecorder.value.ondataavailable = (event) => {
                audioChunks.value.push(event.data)
            }

            mediaRecorder.value.start()
            isRecording.value = true
        } catch (err) {
            console.error('无法调用麦克风:', err)
            alert('请允许麦克风权限')
        }
    }

    const stopRecording = (): Promise<Blob> => {
        return new Promise((resolve) => {
            if (!mediaRecorder.value) return

            mediaRecorder.value.onstop = () => {
                const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' })
                isRecording.value = false
                // 停止所有轨道，释放麦克风红点
                mediaRecorder.value?.stream.getTracks().forEach(track => track.stop())
                resolve(audioBlob)
            }

            mediaRecorder.value.stop()
        })
    }

    return { isRecording, startRecording, stopRecording }
}