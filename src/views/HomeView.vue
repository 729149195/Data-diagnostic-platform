<template>
  <div class="all-layout">
    <el-container>
      <el-header class="header">
      </el-header>
      <el-container>
        <el-aside class="aside">
          <div class="aside-content">
            <el-card class="jump_switch" shadow="never">
              实验数据探索、通道分析模块
            </el-card>
            <el-card class="table" shadow="never">
              <span>可视化配置</span>
            </el-card>
          </div>
        </el-aside>
        <el-container>
          <el-main class="main">
            <el-card class="data_exploration" shadow="never">
              实验数据探索
            </el-card>
            <el-card class="two" shadow="never">
              <span>可视化配置</span>
            </el-card>
          </el-main>
        </el-container>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
</script>

<style scoped>

.el-card__body, .el-card__body {
  padding: 0;
  margin: 0;
}

.all-layout {
  width: 100vw;
  height: 100vh;
  background-color: #e2e2e2;
  overflow: hidden;
}

.header {
  width: 100vw;
  height: 5vh;
  background-color: #fff;
}

.aside {
  width: 15vw;
  background-color: #e9e9e9;
  height: 95vh;
  padding: 8px;
  box-sizing: border-box;
  display: flex;
}

.aside-content , .main{
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

.jump_switch {
  height: 80px;
  margin-bottom: 5px;
}

.data_exploration{
  height: 70%;
  margin-bottom: 5px;
}

.table, .two {
  flex-grow: 1;
}

.main {
  background-color: #e9e9e9;
}
</style>
