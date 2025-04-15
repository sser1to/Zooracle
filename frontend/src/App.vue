<template>
  <div id="app">
    <img alt="Vue logo" src="./assets/logo.png">
    <ElectronStatus />
    <ApiStatus />
    <DbStatus />
    <HelloWorld msg="Welcome to Your Vue.js App"/>
  </div>
</template>

<script>
import HelloWorld from './components/HelloWorld.vue'
import DbStatus from './components/DbStatus.vue'
import ApiStatus from './components/ApiStatus.vue'
import ElectronStatus from './components/ElectronStatus.vue'

export default {
  name: 'App',
  components: {
    HelloWorld,
    DbStatus,
    ApiStatus,
    ElectronStatus
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
