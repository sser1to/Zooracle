const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  // Настройка публичного пути для корректной загрузки ресурсов
  // Всегда используем абсолютный путь '/' для предотвращения проблем с вложенными маршрутами
  publicPath: '/',
  // Добавляем настройку прокси для разработки
  devServer: {
    // Настройка для поддержки HTML5 History API
    historyApiFallback: true,
    proxy: {
      '/api': {
        target: process.env.FRONTEND_URL,
        changeOrigin: true
      },
      '/db-status': {
        target: process.env.FRONTEND_URL,
        changeOrigin: true
      },
      '/health': {
        target: process.env.FRONTEND_URL,
        changeOrigin: true
      }
    }
  },
  // Настройки для сборки Electron
  pluginOptions: {
    electronBuilder: {
      preload: 'preload.js',
      // Настройки сборщика Electron
      builderOptions: {
        appId: 'com.zooracle.app',
        productName: 'Zooracle',
        directories: {
          output: 'electron-dist'
        },
        win: {
          icon: 'public/favicon.ico'
        }
      }
    }
  }
})
