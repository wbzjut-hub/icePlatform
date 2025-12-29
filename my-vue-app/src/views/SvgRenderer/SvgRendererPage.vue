<template>
  <div class="svg-renderer-layout">
    <!-- Main Content Area -->
    <div class="content-area">
      <!-- Tab 1: Code Editor -->
      <div class="editor-pane" v-show="activeTab === 'code'">
        <div class="pane-header">
          <div class="header-left">
             <el-icon><EditPen /></el-icon>
             <span>Code</span>
          </div>
          <div class="header-actions">
            <el-button size="small" type="primary" link @click="formatCode">Format</el-button>
            <el-button size="small" type="danger" link @click="clearCode">Clear</el-button>
          </div>
        </div>
        
        <!-- Highlighted Editor Container -->
        <div class="editor-content-wrapper">
            <!-- 1. Backdrop for Syntax Highlighting -->
            <pre class="code-backdrop" aria-hidden="true"><code ref="highlightCodeBlock" class="language-xml" v-html="highlightedCode"></code></pre>
            
            <!-- 2. Transparent Input -->
            <textarea
              v-model="svgCode"
              class="code-input-textarea"
              placeholder="Paste your SVG code here (or click Format to generate demo)..."
              spellcheck="false"
              @scroll="syncScroll"
              ref="textareaRef"
            ></textarea>
        </div>

        <div class="editor-footer">
          <span class="status-text" :class="{ error: hasError }">
            {{ statusMessage }}
          </span>
        </div>
      </div>

      <!-- Tab 2: Preview -->
      <div class="preview-pane" v-show="activeTab === 'preview'">
        <div class="pane-header">
          <div class="header-left">
             <el-icon><View /></el-icon>
             <span>Preview</span>
          </div>
          
          <!-- Zoom Controls -->
          <div class="zoom-controls">
              <el-button-group size="small">
                <el-button :icon="ZoomOut" @click="zoom(-0.2)" />
                <el-tooltip content="Reset View" placement="top">
                    <el-button :icon="RefreshRight" @click="resetView" />
                </el-tooltip>
                <el-button @click="resetView" style="min-width: 60px">{{ Math.round(zoomScale * 100) }}%</el-button>
                <el-button :icon="ZoomIn" @click="zoom(0.2)" />
              </el-button-group>
          </div>
          
          <!-- Action Buttons -->
          <div class="action-buttons" style="margin-right: 15px; display: flex; gap: 8px;">
              <!-- Download Dropdown -->
              <el-dropdown trigger="click" @command="handleDownload">
                <el-button size="small" type="primary" plain :icon="Download">
                  Download<el-icon class="el-icon--right"><arrow-down /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="png">Download as PNG</el-dropdown-item>
                    <el-dropdown-item command="jpg">Download as JPG</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
          </div>

          <div class="bg-controls">
            <el-tooltip content="Dark Background" placement="top">
              <div class="bg-option dark" :class="{ active: bgMode === 'dark' }" @click="bgMode = 'dark'"></div>
            </el-tooltip>
            <el-tooltip content="Light Background" placement="top">
              <div class="bg-option light" :class="{ active: bgMode === 'light' }" @click="bgMode = 'light'"></div>
            </el-tooltip>
            <el-tooltip content="Transparent Grid" placement="top">
              <div class="bg-option grid" :class="{ active: bgMode === 'grid' }" @click="bgMode = 'grid'"></div>
            </el-tooltip>
          </div>
        </div>
        
        <div 
            class="preview-content" 
            :class="bgMode" 
            @wheel.prevent="handleWheel"
            @mousedown="handleMouseDown"
        >
          <div 
            class="svg-transform-layer"
            ref="svgTransformLayerRef"
            :style="transformStyle"
          >
            <div class="svg-wrapper" v-html="sanitizedSvg" v-if="svgCode" ref="svgWrapperRef"></div>
            
            <div class="empty-preview" v-else-if="!svgCode">
                <el-icon :size="60"><Picture /></el-icon>
                <p>No SVG content to render</p>
                <p class="hint-text">Drag & Drop SVG file here</p>
                <el-button type="primary" plain size="small" @click="activeTab = 'code'">Go to Code</el-button>
            </div>
          </div>
        </div>
        
        <div class="preview-info" v-if="svgCode && !hasError">
            <span>Size: {{ svgSize }} | Zoom: {{ Math.round(zoomScale * 100) }}% | Pan: {{ Math.round(panX) }}, {{ Math.round(panY) }}</span>
        </div>
      </div>
    </div>

    <!-- Drag Overlay -->
    <div class="drag-overlay" v-if="isDraggingFile">
        <el-icon :size="50"><UploadFilled /></el-icon>
        <span>Drop SVG file to open</span>
    </div>

    <!-- Bottom Toolbar -->
    <div class="bottom-toolbar">
        <div class="tab-switch">
            <div class="tab-btn" :class="{ active: activeTab === 'code' }" @click="activeTab = 'code'">
                <el-icon><EditPen /></el-icon>
                <span>Code</span>
            </div>
            <div class="tab-btn" :class="{ active: activeTab === 'preview' }" @click="activeTab = 'preview'">
                <el-icon><View /></el-icon>
                <span>Preview</span>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { EditPen, View, Picture, ZoomIn, ZoomOut, UploadFilled, RefreshRight, Download, ArrowDown } from '@element-plus/icons-vue'
import hljs from 'highlight.js/lib/core'
import xml from 'highlight.js/lib/languages/xml'
import { ElMessage } from 'element-plus'
import 'highlight.js/styles/vs2015.css'

hljs.registerLanguage('xml', xml)

const activeTab = ref<'code' | 'preview'>('code')
const svgCode = ref('')
const bgMode = ref('grid') 
const hasError = ref(false)
const statusMessage = ref('Ready')
// Fix Crop Coordinate Logic
const svgTransformLayerRef = ref<HTMLElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const highlightCodeBlock = ref<HTMLElement | null>(null)
const svgWrapperRef = ref<HTMLElement | null>(null)

// 2. CSS: Ensures SVG fills wrapper exactly
// See style block below

// --- Drag & Drop File State ---
const isDraggingFile = ref(false)

const handleDragEnter = (e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.dataTransfer?.types.includes('Files')) {
        isDraggingFile.value = true
    }
}

const handleDragOver = (e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
}

const handleDragLeave = (e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.relatedTarget === null) {
        isDraggingFile.value = false
    }
}

const handleDrop = async (e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    isDraggingFile.value = false
    
    const files = e.dataTransfer?.files
    if (!files || files.length === 0) return
    
    const file = files[0]
    if (!file) return;

    if (file.type !== 'image/svg+xml' && !file.name.endsWith('.svg')) {
        ElMessage.error('Please drop a valid SVG file')
        return
    }
    
    try {
        const text = await file.text()
        svgCode.value = text
        if (text.includes('<svg')) {
            activeTab.value = 'preview'
            resetView()
            ElMessage.success('SVG loaded')
        }
    } catch (err) {
        ElMessage.error('Failed to read file')
    }
}

onMounted(() => {
    window.addEventListener('dragenter', handleDragEnter)
    window.addEventListener('dragover', handleDragOver)
    window.addEventListener('dragleave', handleDragLeave)
    window.addEventListener('drop', handleDrop)
    
    window.addEventListener('mousemove', handleGlobalMouseMove)
    window.addEventListener('mouseup', handleGlobalMouseUp)
})

onUnmounted(() => {
    window.removeEventListener('dragenter', handleDragEnter)
    window.removeEventListener('dragover', handleDragOver)
    window.removeEventListener('dragleave', handleDragLeave)
    window.removeEventListener('drop', handleDrop)
    window.removeEventListener('mousemove', handleGlobalMouseMove)
    window.removeEventListener('mouseup', handleGlobalMouseUp)
})



// --- Zoom & Pan State ---
const zoomScale = ref(1)
const panX = ref(0)
const panY = ref(0)
const isDragging = ref(false)
const lastMouseX = ref(0)
const lastMouseY = ref(0)

const transformStyle = computed(() => ({
    transform: `translate(${panX.value}px, ${panY.value}px) scale(${zoomScale.value})`,
    cursor: isDragging.value ? 'grabbing' : 'grab'
}))

const zoom = (delta: number) => {
    const newScale = zoomScale.value + delta
    if (newScale > 0.1 && newScale < 10) {
        zoomScale.value = newScale
    }
}

const resetView = () => {
    zoomScale.value = 1
    panX.value = 0
    panY.value = 0
}

const handleWheel = (e: WheelEvent) => {
    if (e.ctrlKey) {
        // --- ZOOM (Pinch) ---
        const zoomIntensity = 0.01
        const delta = -e.deltaY * zoomIntensity
        let newScale = zoomScale.value + delta
        if (newScale < 0.1) newScale = 0.1
        if (newScale > 10) newScale = 10
        zoomScale.value = newScale
    } else {
        // --- PAN (Scroll) ---
        panX.value -= e.deltaX
        panY.value -= e.deltaY
    }
}

const handleMouseDown = (e: MouseEvent) => {
    if (!svgCode.value) return 
    
    // --- Pan Start ---
    e.preventDefault()
    isDragging.value = true
    lastMouseX.value = e.clientX
    lastMouseY.value = e.clientY
}

const handleGlobalMouseMove = (e: MouseEvent) => {
    if (isDragging.value) {
        // --- Pan Drag ---
         const dx = e.clientX - lastMouseX.value
         const dy = e.clientY - lastMouseY.value
         panX.value += dx
         panY.value += dy
         lastMouseX.value = e.clientX
         lastMouseY.value = e.clientY
    }
}

const handleGlobalMouseUp = () => {
    isDragging.value = false
}

// --- Export Logic ---
const handleDownload = (format: string) => {
    if (!svgCode.value || !svgWrapperRef.value) return
    const svgEl = svgWrapperRef.value.querySelector('svg')
    if (!svgEl) {
        ElMessage.warning('No renderable SVG found')
        return
    }

    const serializer = new XMLSerializer()
    let source = serializer.serializeToString(svgEl)
    
    // Ensure namespace
    if(!source.match(/^<svg[^>]+xmlns="http\:\/\/www\.w3\.org\/2000\/svg"/)){
        source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"')
    }
    // XML header
    if(!source.match(/^<\?xml/)){
        source = '<?xml version="1.0" standalone="no"?>\r\n' + source
    }

    const img = new Image()
    const url = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(source)
    
    img.onload = () => {
        const canvas = document.createElement('canvas')
        const context = canvas.getContext('2d')
        
        // High res conversion
        const scale = 2
        canvas.width = img.width * scale || 800
        canvas.height = img.height * scale || 800
        
        if (context) {
            // 1. Ensure clean slate (Transparent)
            context.clearRect(0, 0, canvas.width, canvas.height)
            
            // 2. Optional: Fill background for formats that don't support transparency
            if (format === 'jpg' || format === 'jpeg') {
                context.fillStyle = '#FFFFFF'
                context.fillRect(0, 0, canvas.width, canvas.height)
            }
            
            // 3. Draw SVG
            context.drawImage(img, 0, 0, canvas.width, canvas.height)
            
            const link = document.createElement('a')
            link.download = `exported-image.${format}`
            link.href = canvas.toDataURL(`image/${format === 'jpg' ? 'jpeg' : 'png'}`)
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            ElMessage.success(`Downloaded as ${format.toUpperCase()} (Transparent Background if PNG)`)
        }
    }
    img.onerror = () => {
        ElMessage.error('Failed to parse SVG for export')
    }
    img.src = url
}

// Compute highlighted HTML
const highlightedCode = computed(() => {
    // Escape HTML first to prevent injection in pre block (though hljs handles it usually)
    // Actually hljs.highlight returns an object with value
    if (!svgCode.value) return ' ' // Ensure line height match
    
    try {
        const result = hljs.highlight(svgCode.value, { language: 'xml' })
        // Add a newline at end to match textarea behavior if user types enter at end
        return result.value + (svgCode.value.endsWith('\n') ? '\n' : '')
    } catch (e) {
        return svgCode.value
    }
})

// Sync scrolling
const syncScroll = () => {
    if (textareaRef.value && highlightCodeBlock.value) {
        highlightCodeBlock.value.parentElement!.scrollTop = textareaRef.value.scrollTop
        highlightCodeBlock.value.parentElement!.scrollLeft = textareaRef.value.scrollLeft
    }
}

// Computed sanitized SVG for rendering
const sanitizedSvg = computed(() => {
  if (!svgCode.value.trim()) return ''
  try {
    // Basic validation: check if it looks like SVG
    if (!svgCode.value.includes('<svg') || !svgCode.value.includes('</svg>')) {
      throw new Error('Missing <svg> tags')
    }
    return svgCode.value
  } catch (e) {
    return ''
  }
})

// Watch for errors
watch(svgCode, (newVal) => {
  if (!newVal) {
    hasError.value = false
    statusMessage.value = 'Ready'
    return
  }
  
  // Reset view on new valid SVG? user might prefer keeping zoom
  // Let's reset if it was empty before
  // if (oldVal === '') resetView() 
  
  // Simple parser check
  const parser = new DOMParser()
  const doc = parser.parseFromString(newVal, 'image/svg+xml')
  const parserError = doc.querySelector('parsererror')
  
  if (parserError) {
    // If strict fails, check if we are just missing xmlns (common in HTML5 SVGs)
    if (newVal.includes('<svg') && !newVal.includes('xmlns="http://www.w3.org/2000/svg"')) {
        hasError.value = false
        statusMessage.value = '⚠️ Valid HTML5 SVG (Missing xmlns for standout)'
    } else {
        hasError.value = true
        // Extract a short error message if possible
        const errText = parserError?.textContent ?? ''
        // Suppress the specific "This page contains..." message which is useless to the user
        if (errText.includes("This page contains the following errors")) {
             statusMessage.value = '⚠️ Loose HTML5 SVG (XML Strict Mode Failed)'
             // Actually, if it's just that, we might want to treat it as a warning, not an error
             hasError.value = false 
        } else {
             statusMessage.value = 'Syntax Error: ' + (errText.split('\n')[0] || 'Invalid XML').substring(0, 50)
        }
    }
  } else if (!newVal.includes('<svg')) {
    hasError.value = true
    statusMessage.value = 'Warning: No <svg> tag detected'
  } else {
    hasError.value = false
    statusMessage.value = 'Rendered successfully'
  }
})

const svgSize = computed(() => {
  // Try to extract width/height
  const wMatch = svgCode.value.match(/width="([^"]+)"/)
  const hMatch = svgCode.value.match(/height="([^"]+)"/)
  if (wMatch && hMatch) return `${wMatch[1]} x ${hMatch[1]}`
  return 'Auto'
})

const clearCode = () => {
  svgCode.value = ''
  resetView()
}

const formatCode = () => {
    // If empty, generate a cool cyberpunk demo SVG
    if (!svgCode.value.trim()) {
        svgCode.value = `<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="cyber-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#00f260;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#0575e6;stop-opacity:1" />
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <circle cx="100" cy="100" r="80" stroke="url(#cyber-grad)" stroke-width="4" fill="none" filter="url(#glow)" />
  <path d="M60 100 L140 100 M100 60 L100 140" stroke="#00f260" stroke-width="2" />
  <text x="50%" y="90%" text-anchor="middle" fill="#00f260" font-family="monospace" font-size="14">SYSTEM_READY</text>
</svg>`
        resetView()
        return
    }

    let code = svgCode.value.trim()
    
    // Auto-fix: Add xmlns if missing (critical for valid SVG)
    if (code.includes('<svg') && !code.includes('xmlns=')) {
        code = code.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"')
    }
    
    // Strip existing newlines to re-process
    code = code.replace(/\n/g, '').replace(/>\s*</g, '><')
    
    // --- Alternative Cleaner Implementation ---
    const processXML = (xml: string) => {
        let formatted = ''
        let pad = 0
        const nodes = xml.replace(/>\s*</g, '>\n<').split('\n')
        
        nodes.forEach(node => {
            let indent = 0
            if (node.match(/^<\/\w/)) {
                pad -= 1
            } else if (node.match(/^<\w[^>]*[^\/]>.*<\/\w+>$/)) {
                // Single line content <text>...</text> -> no change in pad
                indent = 0 
            } else if (node.match(/^<\w[^>]*[^\/]>$/) && !node.startsWith('<!')) {
                 // Opening tag
                 indent = 1
            } else {
                 // Self closing or comments
                 indent = 0
            }
            
            if (pad < 0) pad = 0
            
            formatted += new Array(pad * 2 + 1).join('  ') + node + '\n'
            
            // Post-increment for next line
            if (indent === 1) pad += 1
        })
        return formatted
    }
    
    svgCode.value = processXML(code).trim()
}
</script>

<style scoped>
.svg-renderer-layout {
  display: flex;
  flex-direction: column; /* Changed to column */
  height: 100%;
  width: 100%;
  background-color: var(--bg-color-deep-space);
  color: var(--text-color-primary);
  overflow: hidden;
}

.content-area {
    flex: 1;
    position: relative;
    overflow: hidden;
    display: flex; /* Ensure children can fill it */
}

/* Common Pane Styles */
.editor-pane, .preview-pane {
  flex: 1; /* Take full space */
  display: flex;
  flex-direction: column;
  min-width: 0;
  width: 100%; /* Explicitly full width */
}

.editor-pane {
  border-right: none; /* No separator needed in tab mode */
}

.pane-header {
  height: 40px; /* Compress header */
  display: flex;
  align-items: center;
  padding: 0 15px;
  background-color: rgba(10, 25, 47, 0.8);
  border-bottom: 1px solid var(--border-color-tech);
  gap: 10px;
  font-weight: 600;
  letter-spacing: 0.5px;
  font-size: 13px;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 6px;
}

.pane-header .el-icon {
  color: var(--primary-accent-color);
  font-size: 16px;
}

.header-actions {
  margin-left: auto;
}

/* Zoom Controls */
.zoom-controls {
    margin-left: auto; /* Push to right, before bg controls */
    margin-right: 15px;
}
.zoom-controls .el-button {
    background: transparent;
    border-color: rgba(255,255,255,0.2);
    color: #ddd;
    padding: 6px 10px;
}
.zoom-controls .el-button:hover {
    color: var(--primary-accent-color);
    border-color: var(--primary-accent-color);
    background: rgba(0, 242, 96, 0.1);
}

/* --- Editor Stack Layout (Backdrop + Input) --- */
.editor-content-wrapper {
  flex: 1;
  position: relative;
  background-color: #1e1e1e; /* VSCode Dark BG */
  overflow: hidden; /* Scroll handled by children */
}

/* Shared styles for perfect alignment */
.code-backdrop, .code-input-textarea {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  padding: 15px; /* Comfortable padding */
  margin: 0;
  border: none;
  font-family: 'JetBrains Mono', Consolas, monospace !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
  box-sizing: border-box;
  overflow: auto;
  white-space: pre; /* Don't wrap */
}

.code-backdrop {
  z-index: 1;
  background-color: transparent !important;
  pointer-events: none; /* Let clicks pass through */
}

.code-backdrop code {
    font-family: inherit;
    background: transparent !important;
    padding: 0;
}

.code-input-textarea {
  z-index: 2;
  color: transparent; /* Hide text color so backdrop shows */
  background: transparent;
  caret-color: #fff; /* Show cursor */
  outline: none;
  resize: none;
}

.editor-footer {
  height: 28px;
  background-color: var(--bg-color-panel);
  border-top: 1px solid var(--border-color-tech);
  display: flex;
  align-items: center;
  padding: 0 15px;
  font-size: 11px;
  z-index: 5;
}

.status-text { color: var(--primary-accent-color); opacity: 0.8; }
.status-text.error { color: #ff5f56; }

/* Preview Specific */
.bg-controls {
  /* margin-left: auto; */ /* Removed auto since zoom controls are here */
  display: flex;
  gap: 8px;
}

.bg-option {
  width: 18px; height: 18px;
  border-radius: 4px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
}
.bg-option:hover { transform: scale(1.1); }
.bg-option.active { border-color: var(--primary-accent-color); transform: scale(1.1); }

.bg-option.dark { background-color: #0a192f; border-color: #333; }
.bg-option.light { background-color: #ffffff; border-color: #ddd; }
.bg-option.grid {
  background-image: 
    linear-gradient(45deg, #ccc 25%, transparent 25%), 
    linear-gradient(-45deg, #ccc 25%, transparent 25%), 
    linear-gradient(45deg, transparent 75%, #ccc 75%), 
    linear-gradient(-45deg, transparent 75%, #ccc 75%);
  background-size: 16px 16px;
  background-color: #fff;
}

.preview-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden; /* Hide overflow for transform */
  padding: 0;
  position: relative;
  user-select: none; /* Prevent text selection during drag */
  cursor: grab; /* Default cursor for panning */
}
.preview-content:active {
    cursor: grabbing;
}



.svg-transform-layer {
    transition: transform 0.05s linear; /* Smoothness vs responsiveness trade-off */
    transform-origin: center center;
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative; /* Context for absolute crop box */
}


.preview-content.dark { background-color: #0a192f; }
.preview-content.light { background-color: #ffffff; }
.preview-content.grid { 
  background-image: 
    linear-gradient(45deg, #333 25%, transparent 25%), 
    linear-gradient(-45deg, #333 25%, transparent 25%), 
    linear-gradient(45deg, transparent 75%, #333 75%), 
    linear-gradient(-45deg, transparent 75%, #333 75%);
  background-size: 20px 20px;
  background-color: #1e1e1e; /* Dark grid for cyberpunk feel */
}
.preview-content.grid {
    background-color: #2b2b2b;
    background-image:
    linear-gradient(45deg, #3a3a3a 25%, transparent 25%),
    linear-gradient(-45deg, #3a3a3a 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #3a3a3a 75%),
    linear-gradient(-45deg, transparent 75%, #3a3a3a 75%);
}


.svg-wrapper {
  /* No constraints? Let transform handle scale? 
     Actually, we initially want it 'fit' or 'max'.
     If we use transform scale=1, it should be natural size.
  */
  pointer-events: none; /* Let clicks pass to container for drag */
}
:deep(svg) {
    /* Ensure it behaves */
    display: block;
}

.empty-preview {
  color: var(--text-color-secondary);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  opacity: 0.5;
}

.preview-info {
  position: absolute;
  bottom: 0;
  right: 0;
  background: rgba(0,0,0,0.6);
  color: #aaa;
  font-size: 11px;
  padding: 5px 10px;
  border-top-left-radius: 6px;
  pointer-events: none;
}

/* --- Drag Overlay --- */
.drag-overlay {
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-color: rgba(0, 242, 96, 0.2);
    backdrop-filter: blur(5px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    color: #fff;
    font-size: 18px;
    font-weight: 600;
    pointer-events: none; /* Let events pass strictly (though it overlays everything, usually fine for visual feedback)*/
}

.hint-text {
    margin-top: 5px;
    font-size: 12px;
    color: #aaa;
}

/* --- Bottom Toolbar --- */
.bottom-toolbar {
    height: 50px;
    background-color: #050b14; /* Darker footer */
    border-top: 1px solid var(--border-color-tech);
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 0 10px;
}

.tab-switch {
    display: flex;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 20px;
    padding: 3px;
    gap: 5px;
}

.tab-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 20px;
    border-radius: 16px;
    font-size: 13px;
    font-weight: 600;
    color: var(--text-color-secondary);
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.tab-btn:hover {
    color: var(--text-color-primary);
    background-color: rgba(255, 255, 255, 0.1);
}

.tab-btn.active {
    background-color: var(--primary-accent-color);
    color: #000;
    box-shadow: 0 0 10px rgba(0, 242, 96, 0.4);
}

</style>
