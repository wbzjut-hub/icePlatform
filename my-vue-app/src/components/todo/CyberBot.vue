<template>
  <div class="cyber-bot-container">
    <svg 
      viewBox="0 0 200 200" 
      xmlns="http://www.w3.org/2000/svg" 
      class="bot-svg"
    >
      <!-- Glow Filter -->
      <defs>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>

      <!-- Group for Floating Animation -->
      <g class="bot-float">
        
        <!-- Antenna -->
        <line x1="100" y1="50" x2="100" y2="20" class="bot-structure" />
        <circle cx="100" cy="20" r="6" class="bot-light antenna-light" />

        <!-- Ears -->
        <g class="ear left-ear">
          <rect x="30" y="85" width="20" height="30" rx="5" class="bot-structure" />
          <line x1="30" y1="100" x2="20" y2="100" class="bot-accent" />
        </g>
        <g class="ear right-ear">
          <rect x="150" y="85" width="20" height="30" rx="5" class="bot-structure" />
          <line x1="170" y1="100" x2="180" y2="100" class="bot-accent" />
        </g>

        <!-- Head Shell -->
        <rect x="50" y="50" width="100" height="90" rx="25" class="bot-shell" />
        
        <!-- Face Screen -->
        <rect x="60" y="60" width="80" height="60" rx="15" class="bot-screen" />

        <!-- Eyes Container -->
        <g class="eyes-container">
          <!-- Left Eye -->
          <circle cx="80" cy="90" r="8" class="bot-eye left-eye">
            <animate attributeName="r" values="8;1;8" dur="4s" repeatCount="indefinite" begin="0s" />
          </circle>
          
          <!-- Right Eye -->
          <circle cx="120" cy="90" r="8" class="bot-eye right-eye">
            <animate attributeName="r" values="8;1;8" dur="4s" repeatCount="indefinite" begin="0s" />
          </circle>
        </g>

        <!-- Mouth -->
        <path d="M 90 105 Q 100 110 110 105" fill="none" class="bot-mouth" />
        
        <!-- Body/Neck Hint -->
        <path d="M 80 140 L 80 160 Q 100 170 120 160 L 120 140" fill="none" class="bot-structure body-neck" />
        
      </g>
    </svg>
    
    <!-- Hover Rings (CSS) -->
    <div class="hover-rings"></div>
  </div>
</template>

<style scoped>
.cyber-bot-container {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
}

.bot-svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}

/* --- Theme Variables Binding --- */
.bot-shell {
  fill: rgba(10, 25, 47, 0.9);
  stroke: var(--primary-accent-color);
  stroke-width: 3;
  filter: url(#glow);
}

.bot-screen {
  fill: rgba(0, 0, 0, 0.6);
  stroke: var(--secondary-accent-color);
  stroke-width: 1;
}

.bot-eye {
  fill: var(--primary-accent-color);
  filter: url(#glow);
}

.bot-mouth {
  stroke: var(--primary-accent-color);
  stroke-width: 2;
  stroke-linecap: round;
  opacity: 0.8;
}

.bot-structure {
  fill: none;
  stroke: var(--text-color-secondary);
  stroke-width: 3;
}

.bot-light {
  fill: var(--secondary-accent-color);
  filter: url(#glow);
}

.bot-accent {
  stroke: var(--secondary-accent-color);
  stroke-width: 2;
}

.body-neck {
  opacity: 0.5;
}

/* --- Animations --- */
.bot-float {
  animation: float 3s ease-in-out infinite;
  transform-origin: center;
}

@keyframes float {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-10px) rotate(2deg); }
}

.antenna-light {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

/* Interactive States */
.cyber-bot-container:hover .bot-eye {
  fill: var(--secondary-accent-color); /* Eyes change color on hover */
}

.cyber-bot-container:hover .bot-shell {
  stroke: var(--secondary-accent-color);
}
</style>
