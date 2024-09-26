<template>
  <div v-show="selectedChannels.length === 0" >
    <el-empty :image-size="80" description="请选择通道"/>
        </div>
  <!-- 热力图组件 -->
  <div v-show="selectedChannels.length != 0">
    <svg id="heatmap"></svg>

    <!-- 异常信息对话框 -->
    <el-dialog v-model="showAnomalyDialog" title="异常信息" width="50%" :modal="true" :close-on-click-modal="true"
       @close="handleDialogClose">
      <div v-for="(anomaly, index) in anomalyDialogData" :key="index">
        <div v-for="(value, key) in anomaly" :key="key">
          <p><strong>{{ formatKey(key) }}:</strong> {{ value }}</p>
        </div>
        <hr v-if="index < anomalyDialogData.length - 1">
      </div>

      <template #footer>
        <el-button @click="showAnomalyDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import * as d3 from 'd3';
import { onMounted, onBeforeUnmount, watch, computed, ref } from 'vue';
import { useStore } from 'vuex';
import { ElDialog, ElButton } from 'element-plus';

const store = useStore();
const selectedChannels = computed(() => store.state.selectedChannels);
const storePerson = computed(() => store.state.person);
const anomaliesByChannel = computed(() => store.state.anomalies);

const anomalyDialogData = ref([]);
const showAnomalyDialog = ref(false);

// 辅助函数：判断给定的 errorIdx 是否为异常
function isAnomaly(idx) {
  const result = errorResults.find(r => r.errorIdx === idx);
  return result && result.isAnomaly;
}

let errorResults = []; // 全局存储所有错误和异常的数据

onMounted(() => {
  // 监听 selectedChannels 和 anomaliesByChannel 的变化
  watch(
    [selectedChannels, anomaliesByChannel],
    ([newChannels, newAnomalies]) => {
      renderHeatmap(newChannels);
    },
    { immediate: true, deep: true }
  );

  // 添加全局点击事件监听器，用于在点击其他地方时关闭对话框
  document.addEventListener('click', handleDocumentClick);
});

onBeforeUnmount(() => {
  // 移除全局点击事件监听器
  document.removeEventListener('click', handleDocumentClick);
});

function handleDocumentClick(event) {
  if (!event.target.closest('#heatmap')) {
    // 如果点击的位置不在热力图内，关闭对话框
    showAnomalyDialog.value = false;
  }
}

async function renderHeatmap(channels) {
  const heatmap = d3.select('#heatmap');

  // 清空之前的内容
  heatmap.selectAll('*').remove();

  // 只有在有通道时才进行渲染
  if (channels.length === 0) {
    return;
  }

  // 设置常量
  let Domain = [-2, 6];
  let step = 0.5;
  let rectNum = Math.round((Domain[1] - Domain[0]) / step);

  let visData = {}; // { [channel_name]: data array }
  let errorColors = {}; // { [errorIdx]: color }
  let errorIdxCounter = 1;

  let errorPromises = [];

  errorResults = []; // 重置 errorResults

  // 对于每个通道
  for (let channel of channels) {
    let channel_name = channel.channel_name;
    visData[channel_name] = [];
    for (let i = 0; i < rectNum; i++) {
      visData[channel_name][i] = []; // 初始化为数组
    }

    // 对于每个错误
    for (let error of channel.errors) {
      let errorIdxCurrent = errorIdxCounter++;
      errorColors[errorIdxCurrent] = error.color;

      let errorPromise = d3
        .json(error.path)
        .then((errorData) => {
          // 存储带有 errorIdx 的错误数据
          errorResults.push({
            channel_name,
            errorIdx: errorIdxCurrent,
            errorData: errorData,
            isAnomaly: false
          });
          return { channel_name, errorIdx: errorIdxCurrent, errorData };
        })
        .catch((err) => {
          console.error(`Failed to fetch error data from ${error.path}:`, err);
          return null;
        });

      errorPromises.push(errorPromise);
    }
  }

  // 等待所有错误数据加载完成
  await Promise.all(errorPromises);

  // 处理错误数据
  for (let result of errorResults) {
    if (!result) continue;
    const { channel_name, errorIdx, errorData } = result;
    const X_value_error = errorData['X_value_error'];

    // 对于每个错误区间
    for (let idxList of X_value_error) {
      let left = Math.floor((idxList[0] - Domain[0]) / step);
      let right = Math.floor((idxList[idxList.length - 1] - Domain[0]) / step);
      for (let i = left; i <= right; i++) {
        if (i >= 0 && i < rectNum) {
          visData[channel_name][i].push(errorIdx); // 将错误索引加入数组
        }
      }
    }
  }

  // 处理异常数据
  for (let channel of channels) {
    let channel_name = channel.channel_name;
    const channelAnomalies = anomaliesByChannel.value[channel_name] || [];

    for (let anomaly of channelAnomalies) {
      let anomalyErrorIdxCurrent = errorIdxCounter++;
      errorColors[anomalyErrorIdxCurrent] = 'orange';

      // 将异常数据添加到 errorResults
      errorResults.push({
        channel_name,
        errorIdx: anomalyErrorIdxCurrent,
        errorData: anomaly,
        isAnomaly: true
      });

      let left = Math.floor((anomaly.startX - Domain[0]) / step);
      let right = Math.floor((anomaly.endX - Domain[0]) / step);
      for (let i = left; i <= right; i++) {
        if (i >= 0 && i < rectNum) {
          visData[channel_name][i].push(anomalyErrorIdxCurrent);
        }
      }
    }
  }

  // 准备绘图数据
  let channelNames = channels.map((channel) => channel.channel_name);
  let visDataArrays = channelNames.map((name) => visData[name]);

  // 准备X轴刻度
  let xAxisTick = [];
  for (let i = Domain[0]; i <= Domain[1]; i += step) {
    xAxisTick.push(i.toFixed(1)); // 保留一位小数
  }

  // 设置绘图尺寸
  let margin = { top: 8, right: 10, bottom: 10, left: 5 };
  let width = 960 - margin.left - margin.right;
  let rectH = 25; // 固定每个矩形的高度
  let XaxisH = 20;
  let YaxisW = 100;
  let height = rectH * channelNames.length + margin.top + margin.bottom + XaxisH;
  let rectW = (width - YaxisW - margin.left) / rectNum - margin.left;

  // 设置SVG属性
  heatmap
    .attr(
      'viewBox',
      `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`
    )
    .attr('preserveAspectRatio', 'xMidYMid meet')
    .attr('width', '100%'); // 确保宽度自适应父容器

  // 绘制Y轴通道名称
  heatmap
    .selectAll('.channelName')
    .data(channelNames)
    .join('text')
    .attr('class', 'channelName')
    .attr('x', YaxisW - margin.left - 5)
    .attr(
      'y',
      (d, i) => rectH * 0.5 + 5 + XaxisH + i * (rectH + margin.top)
    )
    .style('text-anchor', 'end')
    .text((d) => d);

  // 绘制X轴刻度
  heatmap
    .selectAll('.xTick')
    .data(xAxisTick)
    .join('text')
    .attr('class', 'xTick')
    .attr('x', (d, i) => YaxisW + i * (rectW + margin.left))
    .attr('y', XaxisH - 5)
    .style('text-anchor', 'middle')
    .style('font-size', '10px')
    .text((d) => d);

  // 绘制热力图矩形
  heatmap
    .selectAll('.heatmapRectG')
    .data(visDataArrays)
    .join('g')
    .attr('class', 'heatmapRectG')
    .attr(
      'transform',
      (d, i) => `translate(${YaxisW}, ${XaxisH + i * (rectH + margin.top)})`
    )
    .each(function (d, i) {
      const channel = channels[i]; // 获取当前通道

      // 在该通道的 g 元素中绘制 rect
      d3.select(this)
        .selectAll('.heatmapRect')
        .data(d)
        .join('rect')
        .attr('class', 'heatmapRect')
        .attr('x', (d, j) => j * (rectW + margin.left))
        .attr('y', 0)
        .attr('width', rectW)
        .attr('height', rectH)
        .attr('rx', 3) // 设置圆角半径
        .attr('ry', 3) // 设置圆角半径
        .attr('fill', (d) => {
          if (d.length > 0) {
            // 存在错误或异常
            if (channel.errors.length > 1) {
              return '#999999'; // 多个错误，使用灰色
            } else {
              // 单个错误
              const nonAnomalyIdx = d.find(idx => !isAnomaly(idx));
              const errorData = errorResults.find(
                (result) => result && result.errorIdx === nonAnomalyIdx
              );
              if (errorData && errorData.errorData.person === 'machine') {
                return errorColors[nonAnomalyIdx];
              } else {
                return '#f5f5f5';
              }
            }
          } else {
            return '#f5f5f5'; // 正常数据颜色
          }
        })
        .attr('stroke', (d) => {
          if (d.length > 0) {
            if (channel.errors.length > 1) {
              return '#ccc'; // 多个错误，灰色边框
            } else {
              const nonAnomalyIdx = d.find(idx => !isAnomaly(idx));
              const errorData = errorResults.find(
                (result) => result && result.errorIdx === nonAnomalyIdx
              );
              if (errorData && errorData.errorData.person !== storePerson.value) {
                return errorColors[nonAnomalyIdx];
              } else if (d.some(idx => isAnomaly(idx))) {
                // 如果包含异常，使用橙色边框
                return 'orange';
              } else {
                return 'none';
              }
            }
          } else {
            return 'none'; // 正常数据无边框
          }
        })
        .attr('stroke-width', (d) => {
          if (d.length > 0) {
            return 1;
          } else {
            return 0;
          }
        })
        .attr('stroke-dasharray', (d) => {
          if (d.length > 0) {
            if (channel.errors.length > 1) {
              return '4 2'; // 多个错误，虚线边框
            } else {
              const nonAnomalyIdx = d.find(idx => !isAnomaly(idx));
              const errorData = errorResults.find(
                (result) => result && result.errorIdx === nonAnomalyIdx
              );
              if (errorData && errorData.errorData.person !== storePerson.value) {
                return '4 2'; // person 不同，虚线边框
              } else if (d.some(idx => isAnomaly(idx))) {
                // 如果包含异常，使用实线边框
                return '0';
              } else {
                return '0'; // person 相同，实线边框
              }
            }
          } else {
            return '0'; // 正常数据，实线边框（不可见）
          }
        })
        .attr('cursor', 'pointer')
        .on('click', function (event, dRect) {
          event.stopPropagation();

          const errorIdxs = dRect;
          const errorsInRect = errorIdxs.map(idx => {
            return errorResults.find(result => result && result.errorIdx === idx && result.channel_name === channel.channel_name);
          }).filter(e => e);

          // 提取并过滤所有错误信息
          const filteredErrorsInRect = errorsInRect.map(e => {
            const errorData = e.errorData;
            const { X_value_error, Y_value_error, ...filteredData } = errorData;
            // 将不存在的字段设置为 'unknown'
            Object.keys(filteredData).forEach(key => {
              if (filteredData[key] === undefined || filteredData[key] === null) {
                filteredData[key] = 'unknown';
              }
            });
            return filteredData;
          });

          // console.log('Clicked Rect ErrorIdxs:', errorIdxs);
          // console.log('Errors in Rect:', errorsInRect);
          // console.log('Filtered Errors in Rect:', filteredErrorsInRect);

          if (filteredErrorsInRect.length > 0) {
            anomalyDialogData.value = filteredErrorsInRect;
            showAnomalyDialog.value = true;
          } else {
            showAnomalyDialog.value = false;
          }
        });
      // 关闭 renderHeatmap 函数
    })

}
function formatKey(key) {
  // 将 snake_case 转换为 Title Case，例如 'diagnostic_name' -> 'Diagnostic Name'
  return key
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function handleDialogClose() {
  anomalyDialogData.value = [];
}
</script>

<style scoped>
#heatmap {
  margin-top: 10px;
  width: 100%;
  height: auto;
}
</style>
