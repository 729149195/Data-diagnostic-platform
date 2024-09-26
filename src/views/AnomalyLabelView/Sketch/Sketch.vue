<template>
    <div class="sketch-container">
      <div class="canvas-container">
        <canvas ref="canvas"></canvas>
        <button class="clear-button" @click="clearCanvas">×</button>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, onBeforeUnmount } from 'vue';
  
  const canvas = ref(null);
  let ctx = null;
  let isDrawing = false;
  let lastX = 0;
  let lastY = 0;
  
  // 网格参数
  const gridSize = 20;
  const gridColor = '#e0e0e0';
  
  // 绘制网格函数
  function drawGrid() {
    if (!ctx) return;
    const { width, height } = canvas.value;
  
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
  
    // 绘制垂直线
    for (let x = 0; x <= width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
  
    // 绘制水平线
    for (let y = 0; y <= height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
  }
  
  // 初始化画布
  function initCanvas() {
    const canvasEl = canvas.value;
    ctx = canvasEl.getContext('2d');
  
    // 设置画布大小
    resizeCanvas();
  
    // 绘制网格
    drawGrid();
  
    // 设置绘图样式
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
  }
  
  // 调整画布大小以适应容器
  function resizeCanvas() {
    const canvasEl = canvas.value;
    const container = canvasEl.parentElement;
    canvasEl.width = container.clientWidth;
    canvasEl.height = container.clientHeight;
  }
  
  // 处理窗口大小变化
  function handleResize() {
    if (!ctx) return;
    // 保存当前绘图
    const imageData = ctx.getImageData(0, 0, canvas.value.width, canvas.value.height);
  
    // 清空画布
    ctx.clearRect(0, 0, canvas.value.width, canvas.value.height);
  
    // 重新调整大小
    resizeCanvas();
  
    // 重新绘制网格
    drawGrid();
  
    // 恢复之前的绘图
    ctx.putImageData(imageData, 0, 0);
  }
  
  // 鼠标按下事件
  function startDrawing(e) {
    isDrawing = true;
    const { x, y } = getMousePos(e);
    lastX = x;
    lastY = y;
  }
  
  // 鼠标移动事件
  function draw(e) {
    if (!isDrawing) return;
    const { x, y } = getMousePos(e);
    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
    ctx.lineTo(x, y);
    ctx.stroke();
    lastX = x;
    lastY = y;
  }
  
  // 鼠标松开或离开事件
  function stopDrawing() {
    isDrawing = false;
  }
  
  // 获取鼠标在画布上的位置
  function getMousePos(e) {
    const rect = canvas.value.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    };
  }
  
  // 清空画布并重新绘制网格
  function clearCanvas() {
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.value.width, canvas.value.height);
    drawGrid();
  }
  
  onMounted(() => {
    initCanvas();
  
    // 事件监听
    canvas.value.addEventListener('mousedown', startDrawing);
    canvas.value.addEventListener('mousemove', draw);
    canvas.value.addEventListener('mouseup', stopDrawing);
    canvas.value.addEventListener('mouseleave', stopDrawing);
    window.addEventListener('resize', handleResize);
  });
  
  onBeforeUnmount(() => {
    // 移除事件监听
    canvas.value.removeEventListener('mousedown', startDrawing);
    canvas.value.removeEventListener('mousemove', draw);
    canvas.value.removeEventListener('mouseup', stopDrawing);
    canvas.value.removeEventListener('mouseleave', stopDrawing);
    window.removeEventListener('resize', handleResize);
  });
  </script>
  
  <style scoped>
  .sketch-container {
    margin-top: 10px;
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  
  .canvas-container {
    position: relative;
    flex: 1;
  }
  
  canvas {
    border: 1px solid #ccc;
    display: block;
    width: 100%;
    height: 100%;
    cursor: crosshair;
  }
  
  /* 清空按钮样式 */
  .clear-button {
    position: absolute;
    top: 10px;
    right: 10px;
    background: rgba(255, 255, 255, 0.8);
    border: none;
    color: #333;
    font-size: 18px;
    line-height: 1;
    padding: 4px 8px;
    cursor: pointer;
    border-radius: 50%;
    box-shadow: 0 0 5px rgba(0,0,0,0.2);
    transition: background 0.3s, color 0.3s;
  }
  
  .clear-button:hover {
    background: rgba(255, 17, 0, 0.274);
    color: #fff;
  }
  </style>
  