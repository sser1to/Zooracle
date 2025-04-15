const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  // Настройка публичного пути для корректной загрузки ресурсов в Electron
  publicPath: process.env.NODE_ENV === 'production' ? './' : '/',
  // Добавляем настройку прокси для разработки
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true
      },
      '/db-status': {
        target: 'http://localhost:8080',
        changeOrigin: true
      },
      '/health': {
        target: 'http://localhost:8080',
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
