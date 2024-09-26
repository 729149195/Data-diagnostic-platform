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
                                  <!-- 通道的复选框 -->
                                  <el-checkbox v-model="channel.checked" @change="clearChannelTypeCheckbox(item)"
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
                          <div class="error-container">
                              <span :title="error.errors_name">
                                  {{ formatError(error.errors_name) }}
                              </span>
                              <!-- 颜色选择器移到每个异常类别后面 -->
                              <el-color-picker v-model="error.color" @change="setErrorColor(channel, error)"
                                  class="error-color-picker" size="small" show-alpha
                                  :predefine="predefineColors"/>
                          </div>
                      </td>
                  </tr>
              </template>
          </tbody>
      </table>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useStore } from 'vuex'

const store = useStore()
const data = ref([])

// 用于保存通道的原始颜色
const originalColors = ref({})

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
  if (!store.getters.getStructTree) {
      await store.dispatch('fetchStructTree')
  }
  data.value = store.getters.getStructTree

  // 保存每个通道的原始颜色
  data.value.forEach(item => {
      item.channels.forEach(channel => {
          originalColors.value[channel.channel_name] = channel.channel.color
          // 将所有通道颜色设置为灰色
          channel.channel.color = '#D3D3D3' // 灰色
      })
  })

  updateSelectedChannels() // 初始化时更新选中的通道信息
})

onBeforeUnmount(() => {
  // 在组件卸载前恢复所有通道的原始颜色
  data.value.forEach(item => {
      item.channels.forEach(channel => {
          const originalColor = originalColors.value[channel.channel_name]
          if (originalColor) {
              channel.channel.color = originalColor
          }
      })
  })
})

// 设置通道类别的颜色时同步更新所有通道的颜色
const setChannelColor = (item) => {
  item.channels.forEach((channel) => {
      channel.channel.color = item.color
  })
  updateSelectedChannels()
}

// 设置单个错误类别的颜色
const setErrorColor = (channel, error) => {
  const errorToUpdate = channel.errors.find(e => e.errors_name === error.errors_name)
  if (errorToUpdate) {
      errorToUpdate.color = error.color
  }
  updateSelectedChannels()
}

// 切换通道类型复选框时，影响所有通道复选框
const toggleChannelCheckboxes = (item) => {
  item.channels.forEach((channel) => {
      channel.checked = item.checked
  })
  updateSelectedChannels()
}

// 当任何通道复选框发生变化时，清除通道类型复选框的选中状态
const clearChannelTypeCheckbox = (item) => {
  const allChecked = item.channels.every((channel) => channel.checked)
  item.checked = allChecked
  updateSelectedChannels()
}

// 更新选中通道信息并提交到 Vuex store
const updateSelectedChannels = () => {
  const selected = []

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

  store.commit('updateSelectedChannels', selected)
}

// 格式化错误信息，超过10个字符时截断
const formatError = (name) => {
  if (name.length > 9) {
      return name.slice(0, 9) + '...'
  }
  return name
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
  /* 默认垂直居中 */
  text-align: center;
  /* 水平居中对齐 */
}

.channel-type {
  width: 30%;
  vertical-align: top;
  /* 通道类别列的内容上对齐 */
  text-align: center;
}

.channel-name {
  width: 30%;
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
  width: 40%;
  vertical-align: middle;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-bottom: none;
}

.error-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
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