<!-- src/App.vue -->
<template>
  <router-view />
</template>

<script setup lang="ts">
import { useTheme } from '@/hooks/useTheme'
// Initialize theme globally
useTheme()
</script>

<style>
/* Global styles are now imported from src/style.css */
</style>