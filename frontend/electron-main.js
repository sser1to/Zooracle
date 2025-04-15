const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const isDev = process.env.NODE_ENV !== 'production';

// Сохраняем глобальную ссылку на окно, иначе окно будет закрыто 
// автоматически, когда JavaScript объект будет собран сборщиком мусора
let win;

function createWindow() {
  // Создаем окно браузера
  win = new BrowserWindow({
    width: 1024,
    height: 768,
    webPreferences: {
      nodeIntegration: false, // отключение nodeIntegration для безопасности
      contextIsolation: true, // защита от prototype pollution
      preload: path.join(__dirname, 'preload.js') // используем preload скрипт
    }
  });

  // Загружаем URL приложения
  if (isDev) {
    // В режиме разработки используем сервер для разработки
    win.loadURL('http://localhost:8080');
    // Открываем инструменты разработчика
    win.webContents.openDevTools();
  } else {
    // В производственном режиме загружаем HTML файл
    const distPath = path.join(__dirname, 'dist');
    win.loadFile(path.join(distPath, 'index.html'));
  }

  // Обрабатываем закрытие окна
  win.on('closed', () => {
    win = null;
  });
}

// Настройка IPC обработчиков
function setupIPCHandlers() {
  // Обработчик для получения версии приложения
  ipcMain.handle('get-app-version', () => {
    return app.getVersion();
  });

  // Обработчик для проверки статуса базы данных
  ipcMain.handle('check-db-status', async () => {
    try {
      // Здесь можно сделать запрос к API для проверки статуса БД
      const response = await fetch('http://localhost:8080/db-status');
      return await response.json();
    } catch (error) {
      console.error('Ошибка при проверке статуса БД:', error);
      return { status: 'error', message: error.message };
    }
  });

  // Обработчик для проверки работоспособности API
  ipcMain.handle('check-api-health', async () => {
    try {
      // Здесь можно сделать запрос к API для проверки его работоспособности
      const response = await fetch('http://localhost:8080/health');
      return await response.json();
    } catch (error) {
      console.error('Ошибка при проверке API:', error);
      return { status: 'error', message: error.message };
    }
  });
}

// Этот метод будет вызван, когда Electron закончит инициализацию
// и будет готов к созданию окон браузера.
app.whenReady().then(() => {
  setupIPCHandlers();
  createWindow();
});

// Выход, когда все окна закрыты
app.on('window-all-closed', () => {
  // В macOS приложения и их строка меню обычно остаются активными 
  // пока пользователь не выйдет явно через Cmd + Q
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // В macOS обычно пересоздают окно приложения, когда 
  // на иконку в доке нажали и других открытых окон нет
  if (win === null) {
    createWindow();
  }
});