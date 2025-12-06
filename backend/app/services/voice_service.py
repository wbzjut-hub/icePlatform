import os

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from faster_whisper import WhisperModel
from app.core.config import settings


class VoiceService:
    def __init__(self):
        self.model = None
        # 模型存储在用户数据目录，避免每次打包导致应用体积过大
        self.model_path = settings.APP_DATA_DIR / "models" / "whisper"
        self.model_size = "base"  # 可选: tiny (最快), base (平衡), small (较准)

    def _load_model(self):
        if not self.model:
            print(f"正在加载 Whisper 模型 ({self.model_size})...")
            # device="cpu" 保证兼容性，compute_type="int8" 保证速度
            self.model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",
                download_root=str(self.model_path)
            )
            print("Whisper 模型加载完成")

    def transcribe(self, file_path: str) -> str:
        self._load_model()

        segments, info = self.model.transcribe(
            file_path,
            beam_size=5,
            language="zh"  # 强制中文，或者去掉让它自动识别
        )

        text = "".join([segment.text for segment in segments])
        return text.strip()


voice_service = VoiceService()