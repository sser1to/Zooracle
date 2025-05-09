const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  publicPath: '/',
  devServer: {
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
  }
})
