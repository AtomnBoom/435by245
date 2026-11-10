// ==========================================================================
// MAIN.JS — СИСТЕМНЫЕ ФЛАГИ CHROMIUM ДЛЯ СНЯТИЯ БЛОКИРОВКИ МИКРОФОНА
// ==========================================================================

const { app, BrowserWindow, ipcMain, session } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess = null;

// Порт для общения между Electron и Python
const BACKEND_PORT = 8190; 

// 🛠️ ЖЕЛЕЗНОЕ ИСПРАВЛЕНИЕ: Добавляем флаги Chromium для принудительного открытия микрофона
app.commandLine.appendSwitch('use-fake-ui-for-media-stream');
app.commandLine.appendSwitch('enable-speech-input');

function startPythonAgent() {
    const isPackaged = app.isPackaged;
    
    let pythonExecutable;
    let scriptPath;

    if (!isPackaged) {
        // Режим разработки: берем интерпретатор из виртуального окружения
        pythonExecutable = path.join(__dirname, '.venv', 'Scripts', 'python.exe');
        scriptPath = path.join(__dirname, 'demo_ai.py');
        
        pythonProcess = spawn(pythonExecutable, [scriptPath, '--port', BACKEND_PORT]);
    } else {
        // Режим собранного .exe: вызываем бинарник из внутренних ресурсов
        pythonExecutable = path.join(process.resourcesPath, 'agent_bin', 'demo_ai.exe');
        
        pythonProcess = spawn(pythonExecutable, ['--port', BACKEND_PORT]);
    }

    pythonProcess.stdout.on('data', (data) => {
        console.log(`[Python Agent]: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`[Python Error]: ${data}`);
    });
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1280,
        height: 800,
        minWidth: 900,
        minHeight: 600,
        backgroundColor: '#09090B',
        title: "A.E.G.I.S. Control Interface",
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        }
    });

    mainWindow.setMenu(null);
    mainWindow.loadFile(path.join(__dirname, 'src', 'aegis', 'web', 'index.html'));
    
    mainWindow.on('blur', () => {
        mainWindow.webContents.send('app-blur');
    });
}

app.whenReady().then(() => {
    // Автоматически одобряем доступ к микрофону на уровне сессии
    session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
        if (permission === 'audioCapture') {
            callback(true); 
        } else {
            callback(false); 
        }
    });

    startPythonAgent(); 
    createWindow();     

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

// Убиваем скрытый процесс питона при закрытии программы
app.on('window-all-closed', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
    if (process.platform !== 'darwin') app.quit();
});
