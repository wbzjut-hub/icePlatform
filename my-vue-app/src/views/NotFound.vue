<!-- src/views/NotFound.vue -->

<template>
  <div class="not-found-container">
    <div class="content">
      <h1 class="glitch" data-text="404">404</h1>
      <p class="description">Page Not Found</p>
      <p class="message">您访问的页面不存在或已被传送至未知维度。</p>
      <router-link to="/" class="home-link">返回控制台</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
// No script logic needed for this simple page
</script>

<style scoped>
.not-found-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  text-align: center;
  background-color: var(--bg-color-deep-space);
  font-family: 'JetBrains Mono', Consolas, monospace;
}

.content {
  position: relative;
}

.glitch {
  font-size: 8rem;
  font-weight: 700;
  color: var(--primary-accent-color);
  position: relative;
  animation: glitch-animation 2.5s infinite linear alternate-reverse;
}

.glitch::before,
.glitch::after {
  content: attr(data-text);
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: var(--bg-color-deep-space);
}

.glitch::before {
  left: 2px;
  text-shadow: -2px 0 var(--secondary-accent-color);
  animation: glitch-anim-1 2s infinite linear alternate-reverse;
}

.glitch::after {
  left: -2px;
  text-shadow: -2px 0 #00fff9, 2px 2px var(--secondary-accent-color);
  animation: glitch-anim-2 2.5s infinite linear alternate-reverse;
}

@keyframes glitch-animation {
  0% { transform: translate(0); }
  20% { transform: translate(-3px, 3px); }
  40% { transform: translate(-3px, -3px); }
  60% { transform: translate(3px, 3px); }
  80% { transform: translate(3px, -3px); }
  100% { transform: translate(0); }
}

@keyframes glitch-anim-1 {
  0% { clip-path: polygon(0 2%, 100% 2%, 100% 5%, 0 5%); }
  10% { clip-path: polygon(0 78%, 100% 78%, 100% 82%, 0 82%); }
  /* ... (add more clip-path steps for a more complex effect) ... */
  100% { clip-path: polygon(0 50%, 100% 50%, 100% 55%, 0 55%); }
}

@keyframes glitch-anim-2 {
  0% { clip-path: polygon(0 50%, 100% 50%, 100% 55%, 0 55%); }
  /* ... (add more clip-path steps) ... */
  100% { clip-path: polygon(0 2%, 100% 2%, 100% 5%, 0 5%); }
}

.description {
  font-size: 1.5rem;
  color: var(--text-color-primary);
  margin-top: -1rem;
  margin-bottom: 0.5rem;
}

.message {
  color: var(--text-color-secondary);
  margin-bottom: 2rem;
}

.home-link {
  color: var(--primary-accent-color);
  text-decoration: none;
  border: 1px solid var(--primary-accent-color);
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.home-link:hover {
  background-color: var(--primary-accent-color);
  color: var(--bg-color-deep-space);
  box-shadow: 0 0 15px var(--primary-accent-color);
}
</style>