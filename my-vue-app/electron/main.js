const { app, BrowserWindow, ipcMain, dialog } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const http = require('http') // 用于检测后端端口
const fs = require('fs')

let mainWindow
let splashWindow
let pyProc = null

// --- 1. 启动 Python 后端进程 ---
const createPyProc = () => {
    let script = ''

    if (app.isPackaged) {
        // 生产环境：指向打包在资源目录下的 icePlatform 文件夹中的可执行文件
        // 原来的 OneFile 模式由于需要解压，启动很慢。改为 OneDir 模式后，路径多了一层文件夹。
        // Resources/icePlatform/icePlatform
        script = path.join(process.resourcesPath, 'icePlatform', 'icePlatform')
        if (process.platform !== 'win32') {
            try {
                fs.chmodSync(script, 0o755);
            } catch (e) {
                console.error('Failed to chmod backend:', e);
            }
        }
    } else {
        // 开发环境：不自动启动，由开发者手动在 PyCharm/终端 运行
        console.log('Dev mode: skipping python spawn. Please run backend manually.')
        return
    }

    console.log('正在启动后端服务，路径:', script)

    pyProc = spawn(script)

    pyProc.stdout.on('data', (data) => {
        console.log(`Backend: ${data}`)
    })

    pyProc.stderr.on('data', (data) => {
        console.error(`Backend Error: ${data}`)
    })

    pyProc.on('error', (err) => {
        dialog.showErrorBox('后端启动失败', `无法运行后端服务:\n${err.message}\n路径: ${script}`)
    })

    pyProc.on('close', (code) => {
        console.log(`后端进程退出，代码: ${code}`)
    })
}

// --- 2. 退出时清理后端进程 ---
const exitPyProc = () => {
    if (pyProc) {
        console.log('正在关闭后端进程...')
        pyProc.kill()
        pyProc = null
    }
}

// --- 3. 创建启动画面窗口 (Splash Screen) ---
const createSplashWindow = () => {
    splashWindow = new BrowserWindow({
        width: 400,
        height: 300,
        frame: false,       // 无边框
        alwaysOnTop: true,  // 总是置顶
        transparent: true,  // 透明背景 (配合 CSS 实现圆形或异形加载动画)
        resizable: false,
        webPreferences: {
            nodeIntegration: false
        }
    })

    // 加载 electron 目录下的 splash.html
    splashWindow.loadFile(path.join(__dirname, 'splash.html'))
}

// --- 4. 创建主应用窗口 ---
const createMainWindow = () => {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        center: true, // 1. Screen Center
        titleBarStyle: 'hiddenInset', // 2. Mac Style Hidden Title Bar (Traffic lights inset)
        // trafficLightPosition: { x: 12, y: 12 }, // Optional: Fine tune if needed
        backgroundColor: '#0a192f', // 3. Theme Background (Prevent white flash)
        show: false, // 关键：先隐藏，等加载完毕再显示，防止白屏
        webPreferences: {
            nodeIntegration: true, // 允许前端使用 Node API
            contextIsolation: false, // 允许前端使用 window.require
            webSecurity: false // 允许跨域
        }
    })

    // 根据环境加载页面
    if (app.isPackaged) {
        // 生产环境：加载打包好的 index.html
        mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
    } else {
        // 开发环境：加载 Vite 服务
        mainWindow.loadURL('http://localhost:5173')
    }

    // 当页面渲染完成（Ready-to-show）时触发
    mainWindow.once('ready-to-show', () => {
        // 1. 销毁启动画面
        if (splashWindow && !splashWindow.isDestroyed()) {
            splashWindow.destroy()
        }
        // 2. 显示主窗口
        mainWindow.show()
        // 3. 开发环境下自动打开控制台 (可选)
        // if (!app.isPackaged) mainWindow.webContents.openDevTools()
    })
}

// --- 5. 轮询检查后端是否就绪 ---
const checkBackendReady = (silent = false) => {
    // 尝试请求后端的根路径 (心跳检测)
    const req = http.get('http://127.0.0.1:8000/', (res) => {
        // 如果状态码是 200，说明后端启动成功
        if (res.statusCode === 200) {
            console.log('后端已就绪!')
            if (!silent) createMainWindow() // 只有非静默模式才创建窗口
        } else {
            // 虽然连上了但状态码不对，继续等待
            // console.log('后端响应异常，重试中...')
            setTimeout(() => checkBackendReady(silent), 100)
        }
    })

    req.on('error', (err) => {
        // 连接被拒绝 (Connection Refused)，说明端口还没开，继续等待
        // console.log('后端未就绪，重试中...')
        setTimeout(() => checkBackendReady(silent), 100)
    })

    req.end()
}

// --- 应用生命周期 ---

app.on('ready', () => {
    // A. 总是先显示启动画面 (提升用户体验)
    createSplashWindow()

    // B. 启动 Python 后端
    createPyProc()

    // C. 决定何时启动主窗口
    // C. 决定何时启动主窗口
    // 无论是开发还是生产环境，都并行启动 UI，无需等待后端就绪
    // 只要前端处理好 API 请求失败的情况（显示 loading 或 重试），用户体验会更好

    // 给后端一点点时间启动，避免 UI 刚出来就全是 502 错误，同时展示 Splash 
    createMainWindow()

    // 可选：仍然在后台检查后端状态用于日志记录
    if (app.isPackaged) {
        checkBackendReady(true) // 传入 true 表示仅检查不创建窗口
    }

    // --- IPC 监听配置 ---

    // 1. 切换调试控制台
    ipcMain.on('toggle-devtools', (event) => {
        const webContents = event.sender
        const win = BrowserWindow.fromWebContents(webContents)
        if (win) {
            win.webContents.toggleDevTools()
        }
    })

    // 2. 选择文件夹 (用于修改数据库路径)
    ipcMain.handle('select-directory', async () => {
        const result = await dialog.showOpenDialog(mainWindow, {
            properties: ['openDirectory', 'createDirectory'],
            title: '选择数据库保存位置',
            buttonLabel: '移动数据库到此处'
        })

        if (result.canceled) {
            return null
        } else {
            return result.filePaths[0]
        }
    })

    // 3. 重启应用 (用于数据库路径修改生效)
    ipcMain.on('restart-app', () => {
        console.log('收到重启指令，正在重启...')
        app.relaunch() // 重新启动应用
        app.exit(0)    // 立即退出当前实例
    })

    // --- 4. 自动更新 (Auto Update) ---
    const { autoUpdater } = require('electron-updater')
    const log = require('electron-log')

    // 配置日志
    log.transports.file.level = 'info'
    autoUpdater.logger = log

    // 这一步很重要：开发环境下强制启用，方便测试（如果不加，开发环境会跳过 update check）
    // if (!app.isPackaged) {
    //     Object.defineProperty(app, 'isPackaged', {
    //         get() { return true; }
    //     });
    //     autoUpdater.updateConfigPath = path.join(__dirname, '../dev-app-update.yml');
    // }

    // 主动检查更新
    ipcMain.on('check-for-update', () => {
        console.log('正在检查更新...')
        // 确保 autoUpdater 知道我们的 feedURL (在 package.json 配置了，这里自动读取)
        autoUpdater.checkForUpdates()
    })

    // 开始下载
    ipcMain.on('download-update', () => {
        autoUpdater.downloadUpdate()
    })

    // 退出并安装
    ipcMain.on('quit-and-install', () => {
        autoUpdater.quitAndInstall()
    })

    // 转发 updater 事件给前端
    autoUpdater.on('checking-for-update', () => {
        mainWindow.webContents.send('update-message', { type: 'checking', text: '正在检查更新...' })
    })
    autoUpdater.on('update-available', (info) => {
        mainWindow.webContents.send('update-message', { type: 'available', text: '发现新版本', info })
    })
    autoUpdater.on('update-not-available', (info) => {
        mainWindow.webContents.send('update-message', { type: 'not-available', text: '当前已是最新版本', info })
    })
    autoUpdater.on('error', (err) => {
        mainWindow.webContents.send('update-message', { type: 'error', text: '检查更新失败', error: err.message })
    })
    autoUpdater.on('download-progress', (progressObj) => {
        mainWindow.webContents.send('update-message', { type: 'progress', text: '下载中...', progress: progressObj })
    })
    autoUpdater.on('update-downloaded', (info) => {
        mainWindow.webContents.send('update-message', { type: 'downloaded', text: '下载完成，请重启安装', info })
    })

})

// 退出应用时清理后端进程
app.on('will-quit', exitPyProc)

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit()
    }
})