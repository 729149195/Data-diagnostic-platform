<template>
  <!-- 全局表头 -->
  <div class="header-row">
      <span>通道类别</span>
      <span>通道名</span>
      <span>异常类别</span>
  </div>

  <!-- 渲染每个 channel_type 卡片 -->
  <div v-for="(item, index) in data" :key="index" class="card">
      <!-- 通道类别行 -->
      <table class="channel-table">
          <tbody>
              <!-- 渲染每个通道名及其对应的异常类别 -->
              <template v-for="(channel, cIndex) in item.channels">
                  <tr v-for="(error, eIndex) in channel.errors" :key="`${cIndex}-${eIndex}`">
                      <!-- 通道类别：合并属于该通道类别的所有通道名的行，并且内容上对齐 -->
                      <td v-if="eIndex === 0 && cIndex === 0"
                          :rowspan="item.channels.reduce((total, c) => total + c.errors.length, 0)"
                          class="channel-type">
                          <span>{{ item.channel_type }}</span>
                          <div class="type-header">
                              <el-color-picker v-model="item.color" @change="setChannelColor(item)"
                                  class="category-color-picker" size="small" show-alpha
                                  :predefine="predefineColors"/>
                              <!-- 通道类型的复选框 -->
                              <el-checkbox v-model="item.checked" @change="toggleChannelCheckboxes(item)"
                                  class="checkbox-margin"></el-checkbox>
                          </div>
                      </td>

                      <!-- 通道名：合并该通道名下的所有异常类别的行 -->
                      <td v-if="eIndex === 0" :rowspan="channel.errors.length" :class="{
                          'channel-name': true,
                          'channel-name-last': cIndex === item.channels.length - 1
                      }">
                          <div class="name-container">
                              <span>{{ channel.channel_name }}</span>
                              <div class="name-right">
                                  <!-- 修改为单独处理每个通道颜色的函数 -->
                                  <el-color-picker v-model="channel.channel.color"
                                      @change="setSingleChannelColor(channel)" class="channel-color-picker" show-alpha
                                      :predefine="predefineColors"
                                      size="small" />
                                  <!-- 通道的复选框 -->
                                  <el-checkbox v-model="channel.checked" @change="updateChannelTypeCheckbox(item)"
                                      class="checkbox-margin"></el-checkbox>
                              </div>
                          </div>
                      </td>

                      <!-- 渲染异常类别 -->
                      <td :class="{
                          'error-column': true,
                          'error-last':
                              eIndex === channel.errors.length - 1 &&
                              cIndex !== item.channels.length - 1
                      }">
                          <span :title="error.errors_name">
                              {{ formatError(error.errors_name) }}
                          </span>
                      </td>
                  </tr>
              </template>
          </tbody>
      </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useStore } from 'vuex'

const store = useStore()
const data = ref([])

const predefineColors = ref([
'rgba(255, 215, 0, 0)',
'#4169E1', // Royal Blue
'#DC143C', // Crimson
'#228B22', // Forest Green
'#FF8C00', // Dark Orange
'#800080', // Purple
'#FF1493', // Deep Pink
'#40E0D0', // Turquoise
'#FFD700', // Gold
'#8B4513', // Saddle Brown
'#2F4F4F', // Dark Slate Gray
'#1E90FF', // Dodger Blue
'#32CD32', // Lime Green
'#FF6347', // Tomato
'#DA70D6', // Orchid
'#191970', // Midnight Blue
'#FA8072', // Salmon
'#6B8E23', // Olive Drab
'#6A5ACD', // Slate Blue
'#FF7F50', // Coral
'#4682B4'  // Steel Blue
]);


onMounted(async () => {
  // 判断 store 中的 StructTree 是否已经存在
  if (!store.getters.getStructTree) {
      // 如果不存在，则通过 action 从服务器获取数据
      await store.dispatch('fetchStructTree')
  }
  // 从 store 中获取数据
  data.value = store.getters.getStructTree
  updateSelectedChannels() // 直接提交初始化后的通道信息
})

// 确保 formatError 函数在这里定义
const formatError = (name) => {
  if (name.length > 8) {
      return name.slice(0, 8) + '...'
  }
  return name
}

// 设置通道类别的颜色时同步更新所有通道的颜色
const setChannelColor = (item) => {
  if (item && item.channels) {
      item.channels.forEach((channel) => {
          if (channel.channel) {
              channel.channel.color = item.color
          }
      })
      updateSelectedChannels() // 更新选中的通道信息
  } else {
      console.error('Invalid item or channels:', item);
  }
}

// 设置单个通道的颜色
const setSingleChannelColor = (channel) => {
  if (channel && channel.channel) {
      channel.channel.color = channel.channel.color;
      updateSelectedChannels(); // 更新选中的通道信息
  } else {
      console.error('Invalid channel:', channel);
  }
}

// 更新选中通道信息
const updateSelectedChannels = () => {
  const selected = []

  // 遍历数据，找出所有选中的通道及其相关信息
  data.value.forEach(item => {
      item.channels.forEach(channel => {
          if (channel.checked) {
              selected.push({
                  channel_name: channel.channel_name,
                  path: channel.channel.path,
                  color: channel.channel.color,
                  errors: channel.errors.map(error => ({
                      errors_name: error.errors_name,
                      path: error.path,
                      color: error.color
                  }))
              })
          }
      })
  })

  // 提交到 Vuex store
  store.commit('updateSelectedChannels', selected)
}

// 设置通道复选框联动，通道类型的复选框会影响所有通道复选框
const toggleChannelCheckboxes = (item) => {
  item.channels.forEach((channel) => {
      channel.checked = item.checked
  })
  updateSelectedChannels()
}

// 当通道复选框状态变化时，更新通道类型的复选框
const updateChannelTypeCheckbox = (item) => {
  // 如果所有通道都被选中，通道类型复选框选中，否则取消选中
  item.checked = item.channels.every(channel => channel.checked)
  updateSelectedChannels()
}

</script>

<style scoped>
.card {
  border: 1px solid #ddd;
  margin-bottom: 10px;
  border-radius: 5px;
  width: 100%;
}

.header-row {
  display: flex;
  justify-content: space-between;
  font-weight: bold;
  padding: 5px 0;
  width: 100%;
  text-align: center;
}

.header-row span {
  flex: 1;
  text-align: center;
}

.channel-table {
  width: 100%;
  border-collapse: collapse;
}

.channel-table td {
  padding: 8px;
  vertical-align: middle;
  text-align: center;
}

.channel-type {
  width: 30%;
  vertical-align: top;
  text-align: center;
}

.channel-name {
  width: 40%;
  vertical-align: middle;
  text-align: center;
  border-bottom: 0.5px solid #ddd;
}

.name-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.name-right {
  display: flex;
  align-items: center;
}

.error-column {
  width: 30%;
  vertical-align: middle;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-bottom: none;
}

.error-last {
  border-bottom: 0.5px solid #ddd;
}

.checkbox-margin {
  margin-left: 5px;
}

.type-header {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 5px;
}

.channel-name-last {
  border-bottom: none;
}
</style>
