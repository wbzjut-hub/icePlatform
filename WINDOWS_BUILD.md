# IcePlatform Windows 构建指南 🪟

本文档指导如何在 Windows 环境下编译和打包 IcePlatform 应用。

## 🛠️ 环境准备

在开始之前，请确保您的电脑已安装以下软件：

1. **Python 3.10+**: [下载 Python](https://www.python.org/downloads/windows/)
   - **注意**: 安装时请务必勾选 "Add Python to PATH"
2. **Node.js 18+**: [下载 Node.js](https://nodejs.org/en/download/)
3. **Git**: [下载 Git](https://git-scm.com/download/win)

## 📁 关键依赖配置 (必读)

由于版权和体积原因，仓库未包含 Windows 版的 FFmpeg，您需要手动下载。

1. **下载 FFmpeg**:
   - 访问 [FFmpeg Builds](https://www.gyan.dev/ffmpeg/builds/)
   - 下载 `ffmpeg-git-full.7z` 或 `release-full.7z`
2. **解压并提取**:
   - 解压下载的压缩包。
   - 在 `bin` 文件夹中找到 `ffmpeg.exe`。
3. **放置文件**:
   - 将 `ffmpeg.exe` 复制到本项目的 `backend/bin/` 目录下。
   - **最终路径检查**: 确保存在 `backend/bin/ffmpeg.exe`。

## 📦 安装依赖

打开 CMD 或 PowerShell，在项目根目录下执行：

```bash
# 1. 安装后端依赖
cd backend
pip install -r requirements.txt
cd ..

# 2. 安装前端依赖
cd my-vue-app
npm install
cd ..
```

## 🚀 一键打包

项目已内置 Windows 专用打包脚本。

1. 双击项目根目录下的 **`build_release.bat`**。
2. 脚本将自动执行以下步骤：
   - 清理旧的构建产物
   - 使用 PyInstaller 打包后端
   - 使用 Electron-Builder 打包前端和客户端
3. 等待脚本运行完毕。

## 📂 获取安装包

打包成功后，安装包将位于：
`my-vue-app/dist_electron/IcePlatform Setup 1.0.0.exe`

---

## ❓ 常见问题

**Q: 打包时提示 `ffmpeg not found`?**
A: 请仔细检查 `backend/bin/` 目录下是否有 `ffmpeg.exe` 文件。

**Q: 运行 `pip install` 速度慢?**
A: 可以使用国内源：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

**Q: 启动 App 后一直转圈?**
A: 
1. 检查 `backend/.env` 文件是否存在且配置正确。
2. 按 `Ctrl+Shift+I` 打开控制台，查看 Console 报错信息。
