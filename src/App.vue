<template>
  <div id="app">
    <h1>Paper Search</h1>
    <PaperSearch />
  </div>
</template>

<script>
import PaperSearch from './components/PaperSearch.vue'

export default {
  name: 'App',
  components: {
    PaperSearch
  }
}
</script>

<style>
#app {
  font-family: 'Arial', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  margin: 0;
  padding: 20px;
}

h1 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 30px;
}

body {
  margin: 0;
  background-color: #f5f5f5;
}
</style>
