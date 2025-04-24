const { app, BrowserWindow, ipcMain, globalShortcut, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
const isDev = process.env.NODE_ENV !== 'production';

// Сохраняем глобальную ссылку на окно, иначе окно будет закрыто 
// автоматически, когда JavaScript объект будет собран сборщиком мусора
let win;
let frontendProcess = null;

// URL для фронтенда и API
const frontendUrl = 'http://localhost:8080';
const apiUrl = 'http://localhost:8000/api'; // Изменяем порт с 8080 на 8000 для API в докере

// Функция для проверки доступности фронтенд-сервера
function checkFrontendAvailability(url, callback) {
  http.get(url, (res) => {
    if (res.statusCode === 200) {
      callback(true);
    } else {
      callback(false);
    }
  }).on('error', () => {
    callback(false);
  });
}

// Функция для запуска фронтенд-сервера
function startFrontendServer() {
  console.log('Запуск фронтенд-сервера...');
  
  // Запускаем npm run serve в отдельном процессе
  const npmCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm';
  frontendProcess = spawn(npmCmd, ['run', 'serve'], {
    cwd: __dirname,
    shell: true,
    stdio: 'pipe'
  });

  frontendProcess.stdout.on('data', (data) => {
    console.log(`Frontend stdout: ${data}`);
  });

  frontendProcess.stderr.on('data', (data) => {
    console.error(`Frontend stderr: ${data}`);
  });

  frontendProcess.on('close', (code) => {
    console.log(`Фронтенд-сервер завершил работу с кодом ${code}`);
    frontendProcess = null;
  });
}

function createWindow() {
  // Создаем окно браузера
  win = new BrowserWindow({
    width: 1024,
    height: 768,
    webPreferences: {
      nodeIntegration: false, // отключение nodeIntegration для безопасности
      contextIsolation: true, // защита от prototype pollution
      preload: path.join(__dirname, 'preload.js'), // используем preload скрипт
      devTools: true, // явно разрешаем инструменты разработчика
    },
    // Отключаем стандартную верхнюю панель меню
    autoHideMenuBar: false, // временно включим меню для доступа к DevTools
    menuBarVisible: true,
    // Запуск приложения на весь экран
    show: false // Скрываем окно до максимизации
  });

  // Добавляем меню с опцией DevTools
  const menuTemplate = [
    {
      label: 'Разработка',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools', label: 'Открыть консоль разработчика' },
        { type: 'separator' },
        { role: 'quit', label: 'Выйти' }
      ]
    }
  ];
  const menu = Menu.buildFromTemplate(menuTemplate);
  Menu.setApplicationMenu(menu);

  // Максимизируем окно перед показом
  win.once('ready-to-show', () => {
    win.maximize();
    win.show();
  });

  // Загружаем URL приложения
  if (isDev) {
    // В режиме разработки используем сервер для разработки
    // Проверяем, доступен ли сервер разработки
    checkFrontendAvailability(frontendUrl, (isAvailable) => {
      if (!isAvailable && !frontendProcess) {
        console.log('Фронтенд-сервер не обнаружен, запускаем...');
        startFrontendServer();
        
        // Ждем, пока сервер запустится и повторяем попытку загрузки
        let attempts = 0;
        const maxAttempts = 30;
        const checkInterval = setInterval(() => {
          attempts++;
          checkFrontendAvailability(frontendUrl, (isRunning) => {
            if (isRunning) {
              clearInterval(checkInterval);
              win.loadURL(frontendUrl);
              // Открываем панель разработчика только если явно требуется для отладки
              // win.webContents.openDevTools();
            } else if (attempts >= maxAttempts) {
              clearInterval(checkInterval);
              console.error('Не удалось запустить фронтенд-сервер после нескольких попыток');
              // Можно показать сообщение об ошибке пользователю
            }
          });
        }, 1000); // Проверяем каждую секунду
      } else {
        win.loadURL(frontendUrl);
        // Открываем панель разработчика только если явно требуется для отладки
        // win.webContents.openDevTools();
      }
    });
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
      const response = await fetch(`${apiUrl}/db-status`);
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
      const response = await fetch(`${apiUrl}/health`);
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
  
  // Регистрируем глобальное сочетание клавиш для открытия консоли разработчика
  globalShortcut.register('F12', () => {
    if (win && win.webContents) {
      win.webContents.toggleDevTools();
    }
  });
  
  // Регистрируем Ctrl+Shift+I (или Command+Option+I на macOS) как альтернативный способ
  globalShortcut.register(process.platform === 'darwin' ? 'CommandOrControl+Option+I' : 'Ctrl+Shift+I', () => {
    if (win && win.webContents) {
      win.webContents.toggleDevTools();
    }
  });
});

// Выход, когда все окна закрыты
app.on('window-all-closed', () => {
  // В macOS приложения и их строка меню обычно остаются активными 
  // пока пользователь не выйдет явно через Cmd + Q
  if (process.platform !== 'darwin') {
    // Останавливаем фронтенд-сервер, если он был запущен
    if (frontendProcess) {
      frontendProcess.kill();
      frontendProcess = null;
    }
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

// Убеждаемся, что горячие клавиши освобождаются при выходе
app.on('will-quit', () => {
  globalShortcut.unregisterAll();
});

// Убеждаемся, что фронтенд-сервер завершится вместе с приложением
app.on('quit', () => {
  if (frontendProcess) {
    frontendProcess.kill();
    frontendProcess = null;
  }
});