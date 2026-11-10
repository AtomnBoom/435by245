const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('AegisDesktop', {
    // Передаем в UI-движок адрес запущенного питоновского бэкенда
    getAgentUrl: () => `http://localhost:8190`,
    
    // Подписка на событие потери фокуса для мгновенного скрытия тултипов
    onWindowBlur: (callback) => ipcRenderer.on('app-blur', (_event) => callback())
});
