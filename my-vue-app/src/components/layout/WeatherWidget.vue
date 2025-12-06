<template>
  <div v-if="weather" class="weather-pod-header">
    <div class="weather-left">
      <span class="location">{{ weather.city }}</span>
    </div>
    <div class="weather-right">
      <span class="temp">{{ Math.round(weather.temp_max) }}°</span>
      <div class="icon-container" :title="weatherStateText">
        <!-- Minimal SVG Icons -->
        <svg v-if="isSunny" viewBox="0 0 24 24" class="w-icon sunny"><circle cx="12" cy="12" r="5" fill="currentColor"/><path d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        <svg v-if="isCloudy" viewBox="0 0 24 24" class="w-icon cloudy"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <svg v-if="isRainy" viewBox="0 0 24 24" class="w-icon rainy"><path d="M16 13v8M8 13v8M12 15v8M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 3 16.29" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <svg v-if="isSnowy" viewBox="0 0 24 24" class="w-icon snowy"><path d="M12 3v18M5.64 5.64l12.72 12.72M18.36 5.64L5.64 18.36" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M12 3a9 9 0 1 0 9 9 9 9 0 0 0-9-9z" fill="none" stroke="currentColor" stroke-width="2"/></svg>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { getTodayWeatherApi } from '@/api/modules/system'

interface WeatherData {
  city: string;
  weather_code: number;
  temp_min: number;
  temp_max: number;
  source?: string;
}

const weather = ref<WeatherData | null>(null)

const loadWeather = async () => {
  try {
    const res = await getTodayWeatherApi()
    if (res) {
      weather.value = res
    }
  } catch (e) {
    console.error("Failed to load weather", e)
  }
}

onMounted(() => {
  loadWeather()
})

const weatherClass = computed(() => {
  if (!weather.value) return ''
  const code = weather.value.weather_code
  if (code <= 1) return 'sunny'
  if (code <= 48) return 'cloudy'
  if (code <= 77) return 'rainy' 
  return 'snowy'
})

const weatherStateText = computed(() => {
   switch(weatherClass.value) {
     case 'sunny': return '晴'
     case 'cloudy': return '多云'
     case 'rainy': return '雨'
     case 'snowy': return '雪'
     default: return ''
   }
})

const isSunny = computed(() => weatherClass.value === 'sunny')
const isCloudy = computed(() => weatherClass.value === 'cloudy')
const isRainy = computed(() => weatherClass.value === 'rainy')
const isSnowy = computed(() => weatherClass.value === 'snowy')

</script>

<style scoped>
.weather-pod-header {
  position: absolute;
  top: 15px;
  left: 20px;
  right: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 20;
  font-family: 'PingFang SC', -apple-system, BlinkMacSystemFont, sans-serif;
}

.weather-left .location {
  font-size: 12px;
  font-weight: 600;
  color: #909399; /* Grey text */
  letter-spacing: 1px;
  text-transform: uppercase;
}

.weather-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.temp {
  font-size: 16px;
  font-weight: bold;
  color: #303133; /* Dark text */
}

.icon-container {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #303133; 
}

.w-icon {
  width: 100%;
  height: 100%;
}

/* Minimal animations for life */
.sunny { color: #f59e0b; animation: spin 10s linear infinite; }
.rainy { color: #409eff; }
.cloudy { color: #909399; }
.snowy { color: #a0cfff; }

@keyframes spin { 100% { transform: rotate(360deg); } }

</style>
