<!-- src/views/GenericPage.vue -->
<template>
  <div class="generic-container">
    <h1>{{ $route.meta.name || '新页面' }}</h1>
    <p>这是一个动态创建的页面。</p>
    <p>路由路径: {{ $route.path }}</p>
    <!-- 未来可以在这里添加可配置的组件 -->
  </div>
</template>

<script setup lang="ts">
//
</script>

<style scoped>
.generic-container {
  padding: 20px;
  border-radius: 8px;
  background-color: var(--card-bg-color);
  border: 1px solid var(--border-color-tech);
}
h1 {
  color: var(--primary-accent-color);
}
</style>