import sys
import json
import shutil
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List


# --- 1. 智能计算 .env 文件路径 ---
def get_env_path():
    """
    判断运行环境，返回 .env 文件的绝对路径
    """
    # getattr(sys, 'frozen', False) 是 PyInstaller 打包后的标志
    if getattr(sys, 'frozen', False):
        # 打包模式：.env 文件位于可执行文件同级目录 (Resources)
        # sys.executable 指向打包后的 icePlatform 二进制文件
        application_path = Path(sys.executable).parent
    else:
        # 开发模式：.env 位于项目根目录 (即 app/core/../../.env)
        application_path = Path(__file__).resolve().parent.parent.parent

    return application_path / ".env"


env_path = get_env_path()
print(f"Loading .env from: {env_path}")  # 方便调试日志查看


# --- 2. [新增] FFmpeg 路径配置函数 ---
def setup_ffmpeg_path():
    """
    将本地的 bin 目录加入系统 PATH，以便 faster-whisper 能找到 ffmpeg
    兼容 Dev 模式和 PyInstaller 打包模式
    """
    # 1. 确定 Base Path
    if getattr(sys, 'frozen', False):
        # 打包后：PyInstaller 会把二进制文件解压到临时目录 sys._MEIPASS
        base_path = sys._MEIPASS
    else:
        # 开发模式：base_path 是 backend 根目录
        # 当前文件在 app/core/config.py，往上跳 3 级
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # 2. 拼接 bin 目录
    bin_path = os.path.join(base_path, 'bin')

    # 3. 将 bin 加入环境变量 PATH 的最前面，确保优先使用自带的 ffmpeg
    if os.path.exists(bin_path):
        os.environ["PATH"] = bin_path + os.pathsep + os.environ["PATH"]
        print(f"🔧 FFmpeg path setup: {bin_path}")
    else:
        print(f"⚠️ Warning: FFmpeg bin path not found at {bin_path}")


class Settings(BaseSettings):
    PROJECT_NAME: str = "IcePlatform Backend"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # AI 配置 (默认使用 DeepSeek API)
    OPENAI_API_KEY: str = "sk-ed6aaafe768b4f8f8fe60b87d348cb02"
    OPENAI_BASE_URL: str = "https://api.deepseek.com"
    TAVILY_API_KEY: str = "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"

    # --- 系统路径配置 ---
    @property
    def APP_DATA_DIR(self) -> Path:
        APP_NAME = "IcePlatform"
        home = Path.home()
        if sys.platform == "win32":
            data_dir = home / "AppData" / "Roaming" / APP_NAME
        elif sys.platform == "darwin":
            data_dir = home / "Library" / "Application Support" / APP_NAME
        else:
            data_dir = home / ".local" / "share" / APP_NAME
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    @property
    def CONFIG_FILE(self) -> Path:
        return self.APP_DATA_DIR / "db_config.json"

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        # 默认数据库路径
        final_db_path = self.APP_DATA_DIR / "ice_platform.db"

        # 尝试读取配置文件
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    custom_path = config.get('db_path')
                    if custom_path and Path(custom_path).exists():
                        final_db_path = Path(custom_path) / "ice_platform.db"
            except:
                pass

        print(f"Database Path: {final_db_path}")
        return f"sqlite:///{final_db_path}"

    def move_database(self, new_dir_str: str) -> str:
        new_dir = Path(new_dir_str)
        if not new_dir.exists(): raise FileNotFoundError("Target dir not found")

        current_url = self.SQLALCHEMY_DATABASE_URL
        if current_url.startswith("sqlite:///"):
            curr_path = Path(current_url.replace("sqlite:///", ""))
        else:
            curr_path = Path(current_url)

        tgt_path = new_dir / "ice_platform.db"
        if curr_path.resolve() == tgt_path.resolve(): return str(tgt_path)

        if curr_path.exists():
            if tgt_path.exists(): os.remove(tgt_path)
            shutil.move(str(curr_path), str(tgt_path))

        with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({"db_path": str(new_dir)}, f)

        return str(tgt_path)

    class Config:
        # 关键修改：告诉 Pydantic 使用我们计算出的绝对路径
        env_file = str(env_path)
        case_sensitive = True
        extra = "ignore"


settings = Settings()