<template>
    <div class="chart-container">
      <div v-if="selectedChannels.length === 0">
        <el-empty description="请选择通道" style="margin-top: 15vh;" />
      </div>
      <div v-else>
        <div class="chart-wrapper">
          <svg id="chart"></svg>
        </div>
        <div class="overview-container">
          <el-divider />
          <span style="position: absolute; top: 10px; left:0px;"><el-tag type="info">总览条</el-tag></span>
          <svg id="overview-chart" class="overview-svg"></svg>
        </div>
      </div>
  
      <!-- 异常信息表单 -->
      <el-dialog v-if="showAnomalyForm" v-model="showAnomalyForm" title="编辑/修改异常信息">
        <el-form :model="currentAnomaly" label-width="auto">
          <el-form-item label="通道名">
            <el-select v-model="currentAnomaly.channelName" placeholder="请选择通道">
              <el-option
                v-for="channel in selectedChannels"
                :key="channel.channel_name"
                :label="channel.channel_name"
                :value="channel.channel_name"
              ></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="异常类别">
            <el-input v-model="currentAnomaly.anomalyCategory" />
          </el-form-item>
          <el-form-item label="异常诊断名称">
            <el-input v-model="currentAnomaly.anomalyDiagnosisName" />
          </el-form-item>
          <el-form-item label="时间轴范围">
            <el-input :value="timeAxisRange" disabled />
          </el-form-item>
          <el-form-item label="异常描述">
            <el-input v-model="currentAnomaly.anomalyDescription" :rows="4" type="textarea" />
          </el-form-item>
        </el-form>
        <span slot="footer" class="dialog-footer">
          <el-button @click="closeAnomalyForm">取消</el-button>
          <el-button type="primary" @click="saveAnomaly">保存</el-button>
        </span>
      </el-dialog>
    </div>
  </template>
  
  <script setup>
  import * as d3 from 'd3';
  import debounce from 'lodash/debounce';
  
  import {
    ref,
    reactive,
    watch,
    computed,
    onMounted,
    nextTick,
  } from 'vue';
  
  import {
    ElDialog,
    ElForm,
    ElFormItem,
    ElInput,
    ElButton,
    ElMessage,
    ElSelect,
    ElOption,
  } from 'element-plus';
  import { useStore } from 'vuex';
  import axios from 'axios';
  
  const currentAnomaly = reactive({});
  const showAnomalyForm = ref(false);
  const overviewData = ref([]);
  const channelDataMap = ref({});
  
  const xDomains = ref({});
  const anomalies = ref([]); // 本地管理的异常数组
  
  const timeAxisRange = computed(() => {
    if (
      currentAnomaly &&
      currentAnomaly.startX !== undefined &&
      currentAnomaly.endX !== undefined
    ) {
      return `${currentAnomaly.startX.toFixed(3)} - ${currentAnomaly.endX.toFixed(
        2
      )}`;
    }
    return '';
  });
  
  // 获取 Vuex 状态
  const store = useStore();
  const selectedChannels = computed(() => store.state.selectedChannels);
  const sampling = computed(() => store.state.sampling);
  const smoothnessValue = computed(() => store.state.smoothness);
  const sampleRate = ref(store.state.sampling); // 采样率
  
  // 获取父容器宽度
  const chartContainerWidth = ref(0);
  const brushSelections = ref({ overview: null });
  
  onMounted(() => {
    const container = document.querySelector('.chart-container');
    chartContainerWidth.value = container.offsetWidth;
  });
  
  // 辅助函数：找到第一个大于或等于 startX 的索引
  const findStartIndex = (array, startX) => {
    let low = 0;
    let high = array.length - 1;
    let result = -1;
    while (low <= high) {
      let mid = Math.floor((low + high) / 2);
      if (array[mid] >= startX) {
        result = mid;
        high = mid - 1;
      } else {
        low = mid + 1;
      }
    }
    return result;
  };
  
  // 辅助函数：找到最后一个小于或等于 endX 的索引
  const findEndIndex = (array, endX) => {
    let low = 0;
    let high = array.length - 1;
    let result = -1;
    while (low <= high) {
      let mid = Math.floor((low + high) / 2);
      if (array[mid] <= endX) {
        result = mid;
        low = mid + 1;
      } else {
        high = mid - 1;
      }
    }
    return result;
  };
  
  // 渲染图表的主函数
  const renderCharts = debounce(async () => {
    overviewData.value = [];
    channelDataMap.value = {};
    for (const channel of selectedChannels.value) {
      await fetchData(channel);
    }
    drawChart();
    drawOverviewChart();
  }, 150);
  
  // 初始化时检查是否有通道数据并渲染
  onMounted(async () => {
    if (selectedChannels.value.length > 0) {
      renderCharts();
      drawOverviewChart();
    }
  });
  
  watch(selectedChannels, async (newChannels, oldChannels) => {
    if (JSON.stringify(newChannels) !== JSON.stringify(oldChannels)) {
      overviewData.value = [];
      channelDataMap.value = {};
      await nextTick();
      renderCharts();
      drawOverviewChart();
    }
  });
  
  watch(sampling, () => {
    sampleRate.value = sampling.value;
    renderCharts();
  });
  
  watch(smoothnessValue, () => {
    renderCharts();
  });
  
  // 获取数据
  const fetchData = async (channel) => {
    try {
      const response = await axios.get(channel.path);
      const data = response.data;
  
      // 采样数据
      const samplingInterval = Math.floor(1 / sampleRate.value);
      const sampledData = {
        X_value: data.X_value.filter(
          (_, i) => i % samplingInterval === 0
        ),
        Y_value: data.Y_value.filter(
          (_, i) => i % samplingInterval === 0
        ),
      };
  
      let errorsData = [];
      // 加载错误数据并进行采样
      for (const error of channel.errors) {
        const errorResponse = await axios.get(error.path);
        const errorData = errorResponse.data;
  
        const processedErrorSegments = errorData.X_value_error.map((errorSegment, idx) => {
          if (errorSegment.length === 0) return { X: [], Y: [] };
  
          const startX = errorSegment[0];
          const endX = errorSegment[errorSegment.length - 1];
  
          // 使用辅助函数确保索引在错误数据范围内
          const startIndex = findStartIndex(sampledData.X_value, startX);
          const endIndex = findEndIndex(sampledData.X_value, endX);
  
          // 如果找不到有效的索引，则返回空数组
          if (startIndex === -1 || endIndex === -1 || startIndex > endIndex) {
            return { X: [], Y: [] };
          }
  
          // 提取并确保在范围内的X和Y值
          const sampledX = sampledData.X_value.slice(startIndex, endIndex + 1).filter(x => x >= startX && x <= endX);
          const sampledY = sampledData.Y_value.slice(startIndex, endIndex + 1).filter((_, i) => sampledX.includes(sampledData.X_value[startIndex + i]));
  
          return { X: sampledX, Y: sampledY };
        });
  
        const sampledErrorData = {
          X_value_error: processedErrorSegments.map(seg => seg.X),
          Y_value_error: processedErrorSegments.map(seg => seg.Y),
          color: error.color,
          person: error.person,
        };
  
        errorsData.push(sampledErrorData);
      }
  
      // 处理后的采样数据
      overviewData.value.push({
        channelName: channel.channel_name,
        X_value: sampledData.X_value,
        Y_value: sampledData.Y_value,
        color: channel.color,
      });
  
      channelDataMap.value[channel.channel_name] = {
        sampledData,
        errorsData,
        color: channel.color,
        xUnit: data.X_unit,
        yUnit: data.Y_unit,
        channelType: data.channel_type,
        channelNumber: data.channel_number,
      };
    } catch (error) {
      console.error('获取通道数据时出错：', error);
    }
  };
  
  // 绘制总览图
  const drawOverviewChart = () => {
    d3.select('#overview-chart').selectAll('*').remove();
  
    const container = d3.select('.overview-container');
    if (!container.node()) {
      return; // 如果元素还没有渲染，直接返回，避免后续的报错
    }
  
    const containerWidth = container.node().getBoundingClientRect().width;
  
    const margin = { top: 15, right: 30, bottom: 30, left: 50 };
    const width = containerWidth - margin.left - margin.right;
    const height = 80 - margin.top - margin.bottom;
  
    const svg = d3
      .select('#overview-chart')
      .attr(
        'viewBox',
        `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`
      )
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .attr('width', '100%');
  
    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);
  
    const xExtent = d3.extent(
      overviewData.value.flatMap((d) => d.X_value)
    );
    const x = d3.scaleLinear().domain(xExtent).range([0, width]);
  
    const yExtent = d3.extent(
      overviewData.value.flatMap((d) => d.Y_value)
    );
    const y = d3.scaleLinear().domain(yExtent).range([height, 0]);
  
    overviewData.value.forEach((data) => {
      g.append('path')
        .datum(data.Y_value)
        .attr('fill', 'none')
        .attr('stroke', data.color || 'steelblue')
        .attr('stroke-width', 1)
        .attr(
          'd',
          d3
            .line()
            .x((d, i) => x(data.X_value[i]))
            .y((d) => y(d))
            .curve(d3.curveMonotoneX)
        );
    });
  
    g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x));
  
    const brush = d3
      .brushX()
      .extent([
        [0, 0],
        [width, height],
      ])
      .on('brush end', debounce(brushed, 150));
  
    const brushG = g.append('g').attr('class', 'brush').call(brush);
  
    if (brushSelections.value.overview) {
      const fullRange = x.range();
      const selection = brushSelections.value.overview;
  
      if (selection[0] === fullRange[0] && selection[1] === fullRange[1]) {
        brushG.call(brush);
      } else {
        brushG.call(brush.move, selection);
      }
    } else {
      brushG.call(brush);
    }
  
    function brushed(event) {
      const selection = event.selection || x.range();
      const newDomain = selection.map(x.invert, x);
  
      brushSelections.value.overview = selection;
  
      selectedChannels.value.forEach((channel) => {
        xDomains.value[channel.channel_name] = newDomain;
      });
  
      drawChart();
    }
  };
  
  // 平滑处理函数：根据 smoothness 计算插值
  const interpolateData = (data, t) => {
    if (t === 0) {
      return data;
    }
  
    const smoothedData = data.slice();
    for (let i = 1; i < data.length - 1; i++) {
      smoothedData[i] =
        (1 - t) * data[i] + (t * (data[i - 1] + data[i + 1])) / 2;
    }
    return smoothedData;
  };
  
  // 绘制图表函数，包含平滑度处理和缩放逻辑
  const drawChart = () => {
    // 获取父容器的宽度
    const container = d3.select('.chart-container');
    const containerWidth = container.node().getBoundingClientRect().width;
  
    const svg = d3.select('#chart');
    const margin = { top: 50, right: 30, bottom: 30, left: 65 };
  
    // 使用容器的宽度来计算图表的宽度
    const width = containerWidth - margin.left - margin.right;
    const height = 500 - margin.top - margin.bottom; // 固定高度可以根据需要调整
  
    svg.selectAll('*').remove(); // 清空之前的绘图
  
    // 设置 viewBox 使得图表响应式
    svg
      .attr(
        'viewBox',
        `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`
      )
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .attr('width', '100%'); // 确保宽度自适应父容器
  
    // 计算所有数据的 X 和 Y 范围
    const allXValues = [];
    const allYValues = [];
  
    selectedChannels.value.forEach((channel) => {
      const { sampledData } = channelDataMap.value[channel.channel_name];
      allXValues.push(...sampledData.X_value);
      allYValues.push(...sampledData.Y_value);
    });
  
    const xExtent = d3.extent(allXValues);
    const yExtent = d3.extent(allYValues);
    const yRangePadding = (yExtent[1] - yExtent[0]) * 0.1;
    const yMin = yExtent[0] - yRangePadding;
    const yMax = yExtent[1] + yRangePadding;
  
    // 比例尺
    const x = d3
      .scaleLinear()
      .domain(xDomains.value[selectedChannels.value[0]?.channel_name] || xExtent)
      .range([0, width]);
  
    const y = d3.scaleLinear().domain([yMin, yMax]).range([height, 0]);
  
    // 定义曲线生成器
    const line = d3
      .line()
      .x((d, i) => x(allXValues[i]))
      .y((d, i) => y(d))
      .curve(d3.curveMonotoneX); // 使用单调性插值方式
  
    // 定义图表主体（使用 clip-path 仅限制曲线）
    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
  
    // 添加剪切路径
    g.append('defs')
      .append('clipPath')
      .attr('id', 'clip')
      .append('rect')
      .attr('width', width)
      .attr('height', height);
  
    const clipGroup = g
      .append('g')
      .attr('clip-path', 'url(#clip)'); // 使用剪切路径
  
    // 添加 X 轴
    g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x));
  
    // 添加 Y 轴
    g.append('g').attr('class', 'y-axis').call(d3.axisLeft(y));
  
    // 添加 Y 轴网格线（横向网格线）
    g.append('g')
      .attr('class', 'grid')
      .call(
        d3
          .axisLeft(y)
          .tickSize(-width)
          .tickFormat('')
      )
      .selectAll('line')
      .style('stroke', '#ccc')
      .style('stroke-dasharray', '3,3'); // 横向虚线
  
    // 添加 X 轴网格线（纵向网格线）
    g.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${height})`) // 放置在 X 轴的位置
      .call(
        d3
          .axisBottom(x)
          .tickSize(-height) // 网格线的长度，即延伸到图表高度
          .tickFormat('')
      ) // 不显示 X 轴的刻度标签
      .selectAll('line')
      .style('stroke', '#ccc')
      .style('stroke-dasharray', '3,3'); // 纵向虚线
  
    // 添加图例
    const legend = svg
      .append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${margin.left},${margin.top - 30})`);
  
    selectedChannels.value.forEach((channel, index) => {
      const { sampledData, color } = channelDataMap.value[channel.channel_name];
      const smoothedYValue = smoothnessValue.value > 0 && smoothnessValue.value <= 1
        ? interpolateData(sampledData.Y_value, smoothnessValue.value)
        : sampledData.Y_value;
  
      // 绘制曲线
      clipGroup
        .append('path')
        .datum(smoothedYValue)
        .attr('class', `line-${channel.channel_name}`)
        .attr('fill', 'none')
        .attr('stroke', color || 'steelblue')
        .attr('stroke-width', 1.5)
        .attr(
          'd',
          d3
            .line()
            .x((d, i) => x(sampledData.X_value[i]))
            .y((d, i) => y(d))
            .curve(d3.curveMonotoneX)
        );
  
      // 添加图例项
      const legendItem = legend
        .append('g')
        .attr('transform', `translate(${index * 150},0)`);
  
      legendItem
        .append('rect')
        .attr('x', 0)
        .attr('y', -10)
        .attr('width', 20)
        .attr('height', 10)
        .attr('fill', color || 'steelblue');
  
      legendItem
        .append('text')
        .attr('x', 25)
        .attr('y', 0)
        .attr('text-anchor', 'start')
        .style('font-size', '14px')
        .text(channel.channel_name);
  
      // 绘制异常数据
      const { errorsData } = channelDataMap.value[channel.channel_name];
      errorsData.forEach((errorData, errorIndex) => {
        errorData.X_value_error.forEach((X_value_error, idx) => {
          const Y_value_error = errorData.Y_value_error[idx];
  
          const errorLine = d3
            .line()
            .x((d, i) => x(X_value_error[i]))
            .y((d, i) => y(Y_value_error[i]))
            .curve(d3.curveMonotoneX);
  
          // yOffset 和线条样式根据 person 是否为 machine 进行设置
          const yOffset = errorData.person === 'machine' ? 6 : -6;
          const isMachine = errorData.person === 'machine';
  
          clipGroup
            .append('path')
            .datum(Y_value_error)
            .attr('class', `error-line-${channel.channel_name}-${idx}`)
            .attr('fill', 'none')
            .attr('stroke', errorData.color || 'gray')
            .attr('stroke-width', 2)
            .attr('opacity', 0.8)
            .attr('transform', `translate(0,${yOffset})`)
            .attr('d', errorLine)
            .attr('stroke-dasharray', isMachine ? '5, 5' : null); // 使用虚线或实线
        });
      });
    });
  
    // 添加X轴图例 (xUnit)
    const firstChannel = selectedChannels.value[0];
    if (firstChannel) {
      const { xUnit } = channelDataMap.value[firstChannel.channel_name];
  
      svg
        .append('text')
        .attr('x', width + margin.left) // 放在X轴末端
        .attr('y', height + margin.top + 30) // 距离X轴一些距离
        .attr('text-anchor', 'end')
        .attr('fill', '#000')
        .text(xUnit); // 使用xUnit作为横轴的单位图例
    }
  
    // 添加Y轴图例 (yUnit) - 居中对齐
    svg
      .append('text')
      .attr('transform', `translate(${margin.left - 50}, ${margin.top + height / 2}) rotate(-90)`)
      .attr('text-anchor', 'middle')
      .attr('alignment-baseline', 'middle') // 确保文本垂直居中
      .attr('fill', '#000')
      .text('数值'); // 使用通用的Y轴单位
  
    // 添加 brush 用于交互缩放（总览条上的 brush）
    const selectionBrush = d3
      .brushX()
      .extent([
        [0, 0],
        [width, height],
      ])
      .on('end', selectionBrushed);
  
    // 添加 brush 到主图层
    g.append('g')
      .attr('class', 'selection-brush')
      .call(selectionBrush);
  
    // 创建 anomaliesGroup，确保它位于 brush 之后（更高层级）
    const anomaliesGroup = g.append('g').attr('class', 'anomalies-group');
  
    // 绘制用户自定义和已保存的异常区域
    // 绘制用户自定义的异常区域
    anomalies.value.forEach((anomaly) => {
      drawAnomalyElements(anomaly, anomaliesGroup);
    });
  
    // 绘制已保存的异常区域
    const storedAnomalies = store.getters.getAllAnomalies();
    storedAnomalies.forEach((anomaly) => {
      drawAnomalyElements(anomaly, anomaliesGroup, true); // The third parameter marks it as stored
    });
  
    // brush 回调函数（主图上的 brush，用于添加异常）
    function selectionBrushed(event) {
      if (!event.sourceEvent) return;
      if (!event.selection) return;
  
      const [x0, x1] = event.selection;
      const [startX, endX] = [x.invert(x0), x.invert(x1)];
  
      // 打开异常表单，用户选择通道名
      currentAnomaly.startX = startX;
      currentAnomaly.endX = endX;
      currentAnomaly.anomalyCategory = '';
      currentAnomaly.anomalyDiagnosisName = '';
      currentAnomaly.anomalyDescription = '';
      showAnomalyForm.value = true;
  
      d3.select(this).call(selectionBrush.move, null);
  
      g.select('.selection-brush .overlay').style(
        'pointer-events',
        'none'
      );
  
      g.select('.selection-brush .selection').style('display', 'none');
    }
  
    // 绘制异常区域函数
    function drawAnomalyElements(anomaly, anomaliesGroup, isStored = false) {
      const channelName = anomaly.channelName;
      const color = channelDataMap.value[channelName]?.color || 'orange';
  
      // 创建一个组来包含所有异常元素
      const anomalyGroup = anomaliesGroup
        .append('g')
        .attr('class', `anomaly-group-${anomaly.id}-${channelName}`);
  
      const anomalyLabelsGroup = g
        .append('g')
        .attr('class', `anomaly-labels-group-${anomaly.id}-${channelName}`);
  
      anomalyLabelsGroup
        .append('text')
        .attr('class', `left-label-${anomaly.id}-${channelName}`)
        .attr('x', x(anomaly.startX))
        .attr('y', -5)
        .attr('text-anchor', 'middle')
        .attr('fill', 'black')
        .text(anomaly.startX.toFixed(3));
  
      anomalyLabelsGroup
        .append('text')
        .attr('class', `right-label-${anomaly.id}-${channelName}`)
        .attr('x', x(anomaly.endX))
        .attr('y', -5)
        .attr('text-anchor', 'middle')
        .attr('fill', 'black')
        .text(anomaly.endX.toFixed(3));
  
      if (!isStored) {
        // 添加选择矩形
        const anomalyRect = anomalyGroup
          .append('rect')
          .attr('class', `anomaly-rect-${anomaly.id}-${channelName}`)
          .attr('x', x(anomaly.startX))
          .attr('y', 0)
          .attr('width', x(anomaly.endX) - x(anomaly.startX))
          .attr('height', height)
          .attr('fill', color)
          .attr('fill-opacity', 0.1)
          .attr('stroke', color)
          .attr('stroke-width', 1)
          .attr('cursor', 'move')
          .style('pointer-events', 'all')
          .call(
            d3
              .drag()
              .on('start', function (event) {
                anomaly.initialX = event.x;
              })
              .on('drag', function (event) {
                const dx = x.invert(event.x) - x.invert(anomaly.initialX);
                anomaly.initialX = event.x;
  
                // 计算新位置
                let newStartX = anomaly.startX + dx;
                let newEndX = anomaly.endX + dx;
  
                // 确保矩形在域内
                const domain = x.domain();
                if (newStartX < domain[0]) {
                  newStartX = domain[0];
                  newEndX = newStartX + (anomaly.endX - anomaly.startX);
                } else if (newEndX > domain[1]) {
                  newEndX = domain[1];
                  newStartX = newEndX - (anomaly.endX - anomaly.startX);
                }
  
                anomaly.startX = newStartX;
                anomaly.endX = newEndX;
  
                updateAnomalyElements(anomaly);
              })
              .on('end', function () {
                // 更新 anomalies 数组中的异常
                const index = anomalies.value.findIndex(
                  (a) => a.id === anomaly.id
                );
                if (index !== -1) {
                  anomalies.value[index] = anomaly;
                }
              })
          );
  
        // 左侧调整手柄
        anomalyGroup
          .append('rect')
          .attr('class', `left-handle-${anomaly.id}-${channelName}`)
          .attr('x', x(anomaly.startX) - 5)
          .attr('y', 0)
          .attr('width', 10)
          .attr('height', height)
          .attr('fill', 'transparent')
          .attr('cursor', 'ew-resize')
          .style('pointer-events', 'all')
          .call(
            d3
              .drag()
              .on('drag', function (event) {
                const newX = x.invert(event.x);
                if (newX < anomaly.endX && newX >= x.domain()[0]) {
                  anomaly.startX = newX;
                  updateAnomalyElements(anomaly);
                }
              })
              .on('end', function () {
                // 更新 anomalies 数组中的异常
                const index = anomalies.value.findIndex(
                  (a) => a.id === anomaly.id
                );
                if (index !== -1) {
                  anomalies.value[index] = anomaly;
                }
              })
          );
  
        // 右侧调整手柄
        anomalyGroup
          .append('rect')
          .attr('class', `right-handle-${anomaly.id}-${channelName}`)
          .attr('x', x(anomaly.endX) - 5)
          .attr('y', 0)
          .attr('width', 10)
          .attr('height', height)
          .attr('fill', 'transparent')
          .attr('cursor', 'ew-resize')
          .style('pointer-events', 'all')
          .call(
            d3
              .drag()
              .on('drag', function (event) {
                const newX = x.invert(event.x);
                if (newX > anomaly.startX && newX <= x.domain()[1]) {
                  anomaly.endX = newX;
                  updateAnomalyElements(anomaly);
                }
              })
              .on('end', function () {
                // 更新 anomalies 数组中的异常
                const index = anomalies.value.findIndex(
                  (a) => a.id === anomaly.id
                );
                if (index !== -1) {
                  anomalies.value[index] = anomaly;
                }
              })
          );
      } else {
        // 对于已保存的异常，仅添加不可交互的矩形
        anomalyGroup
          .append('rect')
          .attr('class', `anomaly-rect-${anomaly.id}-${channelName}`)
          .attr('x', x(anomaly.startX))
          .attr('y', 0)
          .attr('width', x(anomaly.endX) - x(anomaly.startX))
          .attr('height', height)
          .attr('fill', 'red')
          .attr('fill-opacity', 0.1)
          .attr('stroke', 'red')
          .attr('stroke-width', 1)
          .style('pointer-events', 'none');
      }
  
      // 添加按钮组
      const buttonGroup = anomalyGroup
        .append('g')
        .attr(
          'class',
          `anomaly-buttons-${anomaly.id}-${channelName}`
        )
        .attr(
          'transform',
          `translate(${x(anomaly.endX) - 40}, ${height - 20})` // 调整按钮的位置
        )
        .style('pointer-events', 'all');
  
      // 删除按钮
      const deleteButton = buttonGroup
        .append('g')
        .attr('class', 'delete-button')
        .attr('cursor', 'pointer')
        .on('click', () => {
          if (isStored) {
            // 从 Vuex store 中移除
            store.dispatch('deleteAnomaly', {
              channelName: anomaly.channelName,
              anomalyId: anomaly.id,
            });
          } else {
            // 从本地 anomalies 数组中移除
            anomalies.value = anomalies.value.filter(
              (a) => a.id !== anomaly.id
            );
          }
          // 从图表中移除异常元素
          removeAnomalyElements(anomaly.id, channelName);
        });
  
      deleteButton
        .append('rect')
        .attr('width', 16)
        .attr('height', 16)
        .attr('fill', '#f56c6c')
        .attr('rx', 3); // 圆角
  
      deleteButton
        .append('text')
        .attr('x', 8)
        .attr('y', 12)
        .attr('text-anchor', 'middle')
        .attr('fill', 'white')
        .attr('font-size', '12px')
        .attr('font-weight', 'bold')
        .attr('pointer-events', 'none')
        .text('×'); // 垃圾桶 emoji
  
      // 编辑按钮
      const editButton = buttonGroup
        .append('g')
        .attr('class', 'edit-button')
        .attr('transform', 'translate(20, 0)')
        .attr('cursor', 'pointer')
        .on('click', () => {
          // 打开异常表单
          Object.assign(currentAnomaly, anomaly);
          currentAnomaly.isStored = isStored; // 添加这一行
          showAnomalyForm.value = true;
        });
  
      editButton
        .append('rect')
        .attr('width', 16)
        .attr('height', 16)
        .attr('fill', '#409eff')
        .attr('rx', 3); // 圆角
  
      editButton
        .append('text')
        .attr('x', 8)
        .attr('y', 12)
        .attr('text-anchor', 'middle')
        .attr('fill', 'white')
        .attr('font-size', '12px')
        .attr('font-weight', 'bold')
        .attr('pointer-events', 'none')
        .text('✒️'); // 铅笔 emoji
  
      // 绘制高亮线段
      const { sampledData } = channelDataMap.value[channelName];
  
      const startIndex = sampledData.X_value.findIndex(
        (xVal) => xVal >= anomaly.startX
      );
      const endIndex = sampledData.X_value.findIndex(
        (xVal) => xVal >= anomaly.endX
      );
      const anomalyXValues = sampledData.X_value.slice(
        startIndex,
        endIndex + 1
      );
      const anomalyYValues = sampledData.Y_value.slice(
        startIndex,
        endIndex + 1
      );
  
      anomalyGroup
        .append('path')
        .datum(anomalyYValues)
        .attr('class', `anomaly-line-${anomaly.id}-${channelName}`)
        .attr('fill', 'none')
        .attr('stroke', isStored ? 'red' : color)
        .attr('stroke-width', 3)
        .attr(
          'd',
          d3
            .line()
            .x((d, i) => x(anomalyXValues[i]))
            .y((d, i) => y(d))
        );
  
      if (isStored) {
        // 禁用矩形和手柄的指针事件
        anomalyGroup
          .select(`.anomaly-rect-${anomaly.id}-${channelName}`)
          .style('pointer-events', 'none');
  
        // 移除手柄
        anomalyGroup
          .selectAll(
            `.left-handle-${anomaly.id}-${channelName}, .right-handle-${anomaly.id}-${channelName}`
          )
          .remove();
      }
    }
  
    function updateAnomalyElements(anomaly, isStored = false) {
      const channelName = anomaly.channelName;
      const { sampledData } = channelDataMap.value[channelName];
  
      // 更新元素位置
      const anomalyGroup = svg
        .select('.anomalies-group')
        .select(`.anomaly-group-${anomaly.id}-${channelName}`);
  
      anomalyGroup
        .select(`.anomaly-rect-${anomaly.id}-${channelName}`)
        .attr('x', x(anomaly.startX))
        .attr('width', x(anomaly.endX) - x(anomaly.startX));
  
      anomalyGroup
        .select(`.left-handle-${anomaly.id}-${channelName}`)
        .attr('x', x(anomaly.startX) - 5);
  
      anomalyGroup
        .select(`.right-handle-${anomaly.id}-${channelName}`)
        .attr('x', x(anomaly.endX) - 5);
  
      anomalyGroup
        .select(`.anomaly-buttons-${anomaly.id}-${channelName}`)
        .attr(
          'transform',
          `translate(${x(anomaly.endX) - 40}, ${height - 20})`
        );
  
      // 更新边界标签
      g.select(
        `.anomaly-labels-group-${anomaly.id}-${channelName} .left-label-${anomaly.id}-${channelName}`
      )
        .attr('x', x(anomaly.startX))
        .text(anomaly.startX.toFixed(3));
  
      g.select(
        `.anomaly-labels-group-${anomaly.id}-${channelName} .right-label-${anomaly.id}-${channelName}`
      )
        .attr('x', x(anomaly.endX))
        .text(anomaly.endX.toFixed(3));
  
      // 更新高亮线段
      const startIndex = sampledData.X_value.findIndex(
        (xVal) => xVal >= anomaly.startX
      );
      const endIndex = sampledData.X_value.findIndex(
        (xVal) => xVal >= anomaly.endX
      );
      const anomalyXValues = sampledData.X_value.slice(
        startIndex,
        endIndex + 1
      );
      const anomalyYValues = sampledData.Y_value.slice(
        startIndex,
        endIndex + 1
      );
  
      anomalyGroup
        .select(`.anomaly-line-${anomaly.id}-${channelName}`)
        .datum(anomalyYValues)
        .attr(
          'd',
          d3
            .line()
            .x((d, i) => x(anomalyXValues[i]))
            .y((d, i) => y(d))
        );
    }
  
    function removeAnomalyElements(anomalyId, channelName) {
      const anomaliesGroup = svg.select('.anomalies-group');
  
      anomaliesGroup
        .select(`.anomaly-group-${anomalyId}-${channelName}`)
        .remove();
      g.select(
        `.anomaly-labels-group-${anomalyId}-${channelName}`
      ).remove();
  
      // 重新启用 brush 覆盖层的指针事件
      g.select('.selection-brush .overlay').style(
        'pointer-events',
        'all'
      );
  
      // 确保 brush 的选择区域再次可见
      g.select('.selection-brush .selection').style('display', null);
    }
  
    function updateAnomaliesOnZoom() {
      anomalies.value.forEach((anomaly) => {
        updateAnomalyElements(anomaly);
      });
  
      // 更新已保存的异常
      const storedAnomalies = store.getters.getAllAnomalies();
      storedAnomalies.forEach((anomaly) => {
        updateAnomalyElements(anomaly, true);
      });
    }
  };
  
  // 保存异常信息
  const saveAnomaly = () => {
    if (currentAnomaly) {
      const payload = {
        channelName: currentAnomaly.channelName,
        anomaly: { ...currentAnomaly, id: Date.now() },
      };
  
      if (currentAnomaly.isStored) {
        // 更新已存在的异常
        store.dispatch('updateAnomaly', payload);
      } else {
        // 将异常添加到 Vuex store
        store.dispatch('addAnomaly', payload);
  
        // 从本地 anomalies 数组中移除
        anomalies.value = anomalies.value.filter(
          (a) => a.id !== currentAnomaly.id
        );
      }
  
      showAnomalyForm.value = false;
      ElMessage.success('异常标注信息已保存');
  
      // 清空 currentAnomaly
      Object.keys(currentAnomaly).forEach((key) => {
        delete currentAnomaly[key];
      });
  
      // 重新绘制图表，包含已保存的异常
      drawChart();
    }
  };
  
  // 关闭异常表单
  const closeAnomalyForm = () => {
    showAnomalyForm.value = false;
    Object.keys(currentAnomaly).forEach((key) => {
      delete currentAnomaly[key];
    });
  };
  </script>
  
  <style scoped>
  .el-divider--horizontal {
    margin: 0px !important;
    border-top: 3px var(--el-border-color) var(--el-border-style);
  }
  
  .chart-container {
    display: flex;
    flex-direction: column;
    padding-bottom: 10vh;
  }
  
  .chart-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
    width: 100%;
    margin-bottom: -10px;
  }
  
  svg {
    width: 100%;
    position: relative;
  }
  
  .divider {
    width: 100%;
    height: 10px;
  }
  
  .overview-container {
    width: 100%;
    position: absolute;
    top: 87%;
    background-color: white;
  }
  </style>
  