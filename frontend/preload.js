// Preload скрипт выполняется перед загрузкой веб-страницы
// и имеет доступ к API Node.js и Electron
const { contextBridge, ipcRenderer } = require('electron');

// Предоставляем безопасный мост между рендерером и основным процессом
contextBridge.exposeInMainWorld('electronAPI', {
  // Здесь можно добавить методы для взаимодействия с основным процессом Electron
  // Например:
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  checkDBStatus: () => ipcRenderer.invoke('check-db-status'),
  checkAPIHealth: () => ipcRenderer.invoke('check-api-health')
});