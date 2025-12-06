const { app, BrowserWindow, ipcMain, dialog, screen } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const http = require('http') // 用于检测后端端口
const fs = require('fs')

let mainWindow
let splashWindow
let bubbleWindow // 悬浮球窗口
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

    // 主窗口关闭时，不直接退出程序，而是隐藏 (Mac 风格 + 悬浮球模式)
    // 除非用户显式退出 (Cmd+Q 或 菜单退出)
    mainWindow.on('close', (event) => {
        // 如果不是在退出过程中，且没有强制退出标记
        if (!app.isQuiting && !process.env.FORCE_QUIT) {
            event.preventDefault()
            mainWindow.hide()
            // 如果是在 Dock 点击退出，才真正退出，但在 Electron 中通常 Dock 点击也是 hide
            // 除非显式 Cmd+Q
        }
        return false
    })
}

// --- 3.5 创建悬浮球窗口 ---
const createBubbleWindow = () => {
    const { width, height } = screen.getPrimaryDisplay().workAreaSize
    const bubbleSize = 70 // 略大一点以便点击

    bubbleWindow = new BrowserWindow({
        width: bubbleSize,
        height: bubbleSize,
        type: 'toolbar',    // 类似于工具栏窗口
        frame: false,       // 无边框
        transparent: true,  // 透明
        alwaysOnTop: true,  // 永远置顶
        resizable: false,
        hasShadow: false,   // 不要系统阴影，用 CSS 画
        // Default Left Bottom
        x: 50,
        y: height - bubbleSize - 100,
        skipTaskbar: true,  // 不显示在任务栏
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    })

    if (app.isPackaged) {
        // 加载 index.html 并带上 hash
        const indexPath = path.join(__dirname, '../dist/index.html')
        bubbleWindow.loadFile(indexPath, { hash: 'bubble' })
    } else {
        bubbleWindow.loadURL('http://localhost:5173/#/bubble')
    }

    // 调试用
    // bubbleWindow.webContents.openDevTools({ mode: 'detach' })
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
            setTimeout(() => checkBackendReady(silent), 100)
        }
    })

    req.on('error', (err) => {
        // 连接被拒绝 (Connection Refused)，说明端口还没开，继续等待
        setTimeout(() => checkBackendReady(silent), 100)
    })

    req.end()
}

// --- 应用生命周期 ---

// 标记是否正在退出
app.on('before-quit', () => {
    app.isQuiting = true
})

app.on('ready', () => {
    // A. 总是先显示启动画面 (提升用户体验)
    createSplashWindow()

    // B. 启动 Python 后端
    createPyProc()

    // C. 启动主窗口
    createMainWindow()

    // D. 启动悬浮球
    createBubbleWindow()

    // 可选：仍然在后台检查后端状态用于日志记录
    if (app.isPackaged) {
        checkBackendReady(true) // 传入 true 表示仅检查不创建窗口
    }

    // --- 全局快捷键 ---
    const { globalShortcut } = require('electron')
    // 注册 Option+Space (Alt+Space) 呼出/收起悬浮球输入框
    globalShortcut.register('Option+Space', () => {
        if (bubbleWindow && !bubbleWindow.isDestroyed()) {
            bubbleWindow.webContents.send('bubble-toggle-input')
        }
    })

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
        process.env.FORCE_QUIT = true // 标记为强制退出，绕过 Close 事件拦截
        app.relaunch() // 重新启动应用
        app.exit(0)    // 立即退出当前实例
    })

    // --- 4. 手动更新 (Manual Update) ---
    const { shell } = require('electron')

    ipcMain.handle('manual-update', async () => {
        const result = await dialog.showOpenDialog(mainWindow, {
            title: '选择安装包进行更新',
            properties: ['openFile'],
            filters: [
                { name: 'Installers', extensions: ['dmg', 'pkg', 'exe', 'zip'] }
            ]
        })

        if (!result.canceled && result.filePaths.length > 0) {
            const filePath = result.filePaths[0]
            console.log('用户选择更新包:', filePath)

            // 打开安装包
            shell.openPath(filePath)

            return { success: true }
        }
        return { success: false }
    })

    // 退出应用 (供前端在打开安装包后调用)
    ipcMain.on('quit-app', () => {
        process.env.FORCE_QUIT = true
        app.quit()
    })

    // --- 5. 悬浮球交互 ---
    ipcMain.on('bubble-clicked', () => {
        if (mainWindow) {
            if (mainWindow.isMinimized()) mainWindow.restore()
            if (!mainWindow.isVisible()) mainWindow.show()
            mainWindow.focus()
            // 通知前端跳转到 Agent 管理或对话页面
            mainWindow.webContents.send('navigate-to', '/agent-manager') // 或者直接激活 AI Lab
        }
    })

    // 悬浮球调整大小 (用于展开/收起输入框)
    ipcMain.on('bubble-resize', (event, { width, height }) => {
        if (bubbleWindow) {
            const bounds = bubbleWindow.getBounds()
            // 左下角模式：向右扩展，X 不变
            bubbleWindow.setBounds({
                x: bounds.x,
                y: bounds.y,
                width: width,
                height: height
            })
        }
    })

    // 悬浮球移动 (JS 模拟拖拽)
    let lastBubbleX = 50 // 记录未隐藏时的 X 坐标 (默认 50)

    ipcMain.on('bubble-move', (event, { x, y }) => {
        if (bubbleWindow) {
            bubbleWindow.setPosition(x, y)
            lastBubbleX = x // 更新记录
        }
    })

    // 悬浮球通知主窗口刷新 (添加日程后)
    ipcMain.on('notify-main-refresh', () => {
        if (mainWindow) {
            mainWindow.webContents.send('refresh-todos')
        }
    })

    // 悬浮球贴边隐藏 (Docking) - 智能左右侧
    ipcMain.on('bubble-dock', () => {
        if (bubbleWindow) {
            const bounds = bubbleWindow.getBounds()
            const { width: screenWidth } = screen.getPrimaryDisplay().workAreaSize

            // 记录当前位置 (如果在屏幕内)
            if (bounds.x >= 0 && bounds.x < screenWidth) {
                lastBubbleX = bounds.x
            }

            // 判断是在左半屏还是右半屏
            const isLeft = (bounds.x + bounds.width / 2) < (screenWidth / 2)

            if (isLeft) {
                // 左侧隐藏：只露出一部分
                // 窗口宽70, 移动到 -50 (露出20)
                bubbleWindow.setPosition(-50, bounds.y)
                // 通知前端：左侧停靠 (显示 > )
                bubbleWindow.webContents.send('dock-side-changed', 'left')
            } else {
                // 右侧隐藏
                // 移动到 screenWidth - 20
                bubbleWindow.setPosition(screenWidth - 20, bounds.y)
                // 通知前端：右侧停靠 (显示 < )
                bubbleWindow.webContents.send('dock-side-changed', 'right')
            }

            bubbleWindow.setOpacity(0.8) // 稍微透明一点，但不要太淡，因为条很细
        }
    })

    ipcMain.on('bubble-undock', () => {
        if (bubbleWindow) {
            const bounds = bubbleWindow.getBounds()
            // 恢复到之前的 X 位置
            const { width: screenWidth } = screen.getPrimaryDisplay().workAreaSize

            // 如果 lastBubbleX 数据异常 (比如在屏幕外)，重置
            let targetX = lastBubbleX
            if (targetX < 0) targetX = 50 // 默认左侧
            if (targetX > screenWidth - 70) targetX = screenWidth - 120 // 默认右侧

            bubbleWindow.setPosition(targetX, bounds.y)
            bubbleWindow.setOpacity(1.0)

            // 通知前端：已展开 (显示机器人)
            bubbleWindow.webContents.send('dock-side-changed', 'none')
        }
    })

})

// 激活应用 (Mac Dock 点击)
app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createMainWindow()
        if (!bubbleWindow) createBubbleWindow()
    } else {
        if (mainWindow) mainWindow.show()
    }
})

// 退出应用时清理后端进程
app.on('will-quit', exitPyProc)

// 针对 Mac 平台，因为有悬浮球，所以 WindowAllClosed 的逻辑可能需要调整
// 但我们现在让 Main Window 关闭时只是 Hidden，所以 WindowAllClosed 不会被轻易触发
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit()
    }
})