<template>
    <div class="chart-container">
        <div v-if="selectedChannels.length === 0">
            <el-empty description="请选择通道" />
        </div>
        <div v-else>
            <div class="chart-wrapper" v-for="channel in selectedChannels" :key="channel.channel_name">
                <svg :id="'chart-' + channel.channel_name" class="chart-svg"></svg>
                <svg :id="'overview-' + channel.channel_name" class="overview-svg"></svg>
            </div>
        </div>

        <!-- Anomaly Form -->
        <el-dialog v-if="showAnomalyForm && currentAnomaly.value" v-model="showAnomalyForm" title="编辑异常信息">
            <el-form :model="currentAnomaly.value">
                <el-form-item label="通道名">
                    <el-input v-model="currentAnomaly.value.channelName" disabled></el-input>
                </el-form-item>
                <el-form-item label="异常类别">
                    <el-input v-model="currentAnomaly.value.anomalyCategory"></el-input>
                </el-form-item>
                <el-form-item label="异常诊断名称">
                    <el-input v-model="currentAnomaly.value.anomalyDiagnosisName"></el-input>
                </el-form-item>
                <el-form-item label="时间轴范围">
                    <el-input :value="timeAxisRange" disabled></el-input>
                </el-form-item>
                <el-form-item label="异常描述">
                    <el-input v-model="currentAnomaly.value.anomalyDescription"></el-input>
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
import { ref, watch, computed, onMounted, nextTick } from 'vue';
import { ElDialog, ElForm, ElFormItem, ElInput, ElButton, ElMessage } from 'element-plus';
import { useStore } from 'vuex';
import axios from 'axios';

const currentAnomaly = ref(null);
const showAnomalyForm = ref(false);

const xDomains = ref({});
const anomalies = ref([]); // 本地管理的异常数组

const timeAxisRange = computed(() => {
    if (
        currentAnomaly.value &&
        currentAnomaly.value.startX !== undefined &&
        currentAnomaly.value.endX !== undefined
    ) {
        return `${currentAnomaly.value.startX.toFixed(2)} - ${currentAnomaly.value.endX.toFixed(2)}`;
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
const brushSelections = ref({});

onMounted(() => {
    const container = document.querySelector('.chart-container');
    chartContainerWidth.value = container.offsetWidth;
});

// 渲染图表的主函数
const renderCharts = () => {
    selectedChannels.value.forEach((channel) => {
        fetchDataAndDrawChart(channel);
    });
};

// 初始化时检查是否有通道数据并渲染
onMounted(() => {
    if (selectedChannels.value.length > 0) {
        renderCharts();
    }
});

watch(selectedChannels, (newChannels) => {
    newChannels.forEach((channel) => {
        fetchDataAndDrawChart(channel);
    });
});

watch(sampling, () => {
    sampleRate.value = sampling.value;
    if (selectedChannels.value.length > 0) {
        renderCharts();
    }
});

watch(smoothnessValue, () => {
    if (selectedChannels.value.length > 0) {
        renderCharts();
    }
});

// 获取数据并绘制图表
const fetchDataAndDrawChart = async (channel) => {
    try {
        const response = await axios.get(channel.path);
        const data = response.data;

        // 采样数据
        const sampledData = {
            X_value: data.X_value.filter((_, i) => i % Math.floor(1 / sampleRate.value) === 0),
            Y_value: data.Y_value.filter((_, i) => i % Math.floor(1 / sampleRate.value) === 0),
        };

        let errorsData = [];
        // 加载错误数据并进行采样
        for (const error of channel.errors) {
            const errorResponse = await axios.get(error.path);
            const errorData = errorResponse.data;

            const sampledErrorData = {
                X_value_error: errorData.X_value_error.map(arr => arr.filter((_, i) => i % Math.floor(1 / sampleRate.value) === 0)),
                Y_value_error: errorData.Y_value_error.map(arr => arr.filter((_, i) => i % Math.floor(1 / sampleRate.value) === 0)),
                color: error.color,
                person: errorData.person,
            };

            errorsData.push(sampledErrorData);
        }

        // 确保DOM已更新，然后绘制图表
        await nextTick();
        drawChart(sampledData, errorsData, channel.channel_name, channel.color, data.X_unit, data.Y_unit, data.channel_type, data.channel_number);
    } catch (error) {
        console.error('获取通道数据时出错：', error);
    }
};

// 平滑处理函数：根据 smoothness 计算插值
const interpolateData = (data, t) => {
    if (t === 0) {
        return data;
    }

    const smoothedData = data.slice();
    for (let i = 1; i < data.length - 1; i++) {
        smoothedData[i] = (1 - t) * data[i] + (t * (data[i - 1] + data[i + 1])) / 2;
    }
    return smoothedData;
};

// 绘制图表函数，包含平滑度处理和缩放逻辑
const drawChart = (data, errorsData, channelName, color, xUnit, yUnit, channelType, channelNumber) => {
    // 获取父容器的宽度
    const container = d3.select('.chart-container');
    const containerWidth = container.node().getBoundingClientRect().width;

    const svg = d3.select(`#chart-${channelName}`);
    const overviewSvg = d3.select(`#overview-${channelName}`);
    const margin = { top: 20, right: 30, bottom: 30, left: 50 };

    // 使用容器的宽度来计算图表的宽度
    const width = containerWidth - margin.left - margin.right;
    const height = 350 - margin.top - margin.bottom;  // 固定高度可以根据需要调整
    const overviewHeight = 30;  // 总览图的高度

    svg.selectAll('*').remove(); // 清空之前的绘图
    overviewSvg.selectAll('*').remove(); // 清空总览条

    // 设置 viewBox 使得图表响应式
    svg.attr('viewBox', `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`)
        .attr('preserveAspectRatio', 'xMidYMid meet')
        .attr('width', '100%');  // 确保宽度自适应父容器

    overviewSvg.attr('viewBox', `0 0 ${width + margin.left + margin.right} ${overviewHeight + margin.top + margin.bottom}`)
        .attr('preserveAspectRatio', 'xMidYMid meet')
        .attr('width', '100%');  // 确保宽度自适应父容器

    // Y 轴范围
    const yExtent = d3.extent(data.Y_value);
    const yRangePadding = (yExtent[1] - yExtent[0]) * 0.1;
    const yMin = yExtent[0] - yRangePadding;
    const yMax = yExtent[1] + yRangePadding;

    // 比例尺
    const x = d3.scaleLinear()
        .domain(xDomains.value[channelName] || [-2, 6])
        .range([0, width]);

    const y = d3.scaleLinear()
        .domain([yMin, yMax])
        .range([height, 0]);

    // 判断是否需要平滑处理
    let smoothedYValue = data.Y_value;
    if (smoothnessValue.value > 0 && smoothnessValue.value <= 1) {
        smoothedYValue = interpolateData(data.Y_value, smoothnessValue.value);
    }

    // 定义曲线生成器
    const line = d3.line()
        .x((d, i) => x(data.X_value[i]))
        .y((d, i) => y(d))
        .curve(d3.curveMonotoneX);  // 使用单调性插值方式

    // 定义图表主体（使用 clip-path 仅限制曲线）
    const g = svg
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    const clipGroup = g.append('g')
        .attr('clip-path', `url(#clip-${channelName})`);  // 使用剪切路径

    svg.append('defs').append('clipPath')
        .attr('id', `clip-${channelName}`)
        .append('rect')
        .attr('width', width)
        .attr('height', height);

    // 添加 X 轴
    g.append('g')
        .attr('class', 'x-axis')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x));

    // 添加 Y 轴
    g.append('g')
        .attr('class', 'y-axis')
        .call(d3.axisLeft(y));

    // 添加 Y 轴网格线（横向网格线）
    g.append('g')
        .attr('class', 'grid')
        .call(d3.axisLeft(y)
            .tickSize(-width)
            .tickFormat(''))
        .selectAll('line')
        .style('stroke', '#ccc')
        .style('stroke-dasharray', '3,3');  // 横向虚线

    // 添加 X 轴网格线（纵向网格线）
    g.append('g')
        .attr('class', 'grid')
        .attr('transform', `translate(0,${height})`)  // 放置在 X 轴的位置
        .call(d3.axisBottom(x)
            .tickSize(-height)  // 网格线的长度，即延伸到图表高度
            .tickFormat(''))  // 不显示 X 轴的刻度标签
        .selectAll('line')
        .style('stroke', '#ccc')
        .style('stroke-dasharray', '3,3');  // 纵向虚线

    // 在左上角添加 channel_type 和 channel_number
    g.append('text')
        .attr('x', 0)
        .attr('y', -margin.top / 5)
        .attr('text-anchor', 'start')
        .style('font-size', '12px')
        .style('font-weight', 'bold')
        .style('fill', color)
        .text(`${channelType} - ${channelNumber}`);

    // 添加X轴图例 (xUnit)
    svg.append('text')
        .attr('x', width + margin.left) // 放在X轴末端
        .attr('y', height + margin.top + 30) // 距离X轴一些距离
        .attr('text-anchor', 'end')
        .attr('fill', '#000')
        .text(xUnit);  // 使用xUnit作为横轴的单位图例

    // 添加Y轴图例 (yUnit)
    svg.append('text')
        .attr('transform', 'rotate(-90)')  // 旋转Y轴单位使其竖直显示
        .attr('y', -margin.left + 65)  // 位置调整到Y轴的左边
        .attr('x', -margin.top * 5)  // 与Y轴对齐
        .attr('text-anchor', 'end')
        .attr('fill', '#000')
        .text(yUnit);  // 使用yUnit作为纵轴的单位图例

    // 绘制原始折线图
    clipGroup.append('path')
        .datum(data.Y_value)
        .attr('class', 'original-line')  // 给原始线条添加 class
        .attr('fill', 'none')
        .attr('stroke', color || 'steelblue')
        .attr('stroke-width', 1.5)
        .attr('opacity', smoothnessValue.value > 0 ? 0.3 : 1)  // 如果平滑曲线存在，原始线条透明度为0.5
        .attr('d', line);

    // 绘制异常数据
    errorsData.forEach((errorData, errorIndex) => {
        errorData.X_value_error.forEach((X_value_error, index) => {
            const Y_value_error = errorData.Y_value_error[index];

            const errorLine = d3.line()
                .x((d, i) => x(X_value_error[i]))
                .y((d, i) => y(Y_value_error[i]))
                .curve(d3.curveMonotoneX);

            // yOffset 和线条样式根据 person 是否为 machine 进行设置
            const yOffset = errorData.person === 'machine' ? 10 : -10;
            const isMachine = errorData.person === 'machine';

            clipGroup.append('path')
                .datum(Y_value_error)
                .attr('class', `error-line-${index}-${channelName}`)  // 给每条异常线段一个唯一的 class
                .attr('fill', 'none')
                .attr('stroke', errorData.color || 'red')
                .attr('stroke-width', 5)
                .attr('opacity', 0.8)
                .attr('transform', `translate(0,${yOffset})`)
                .attr('d', errorLine)
                .attr('stroke-dasharray', isMachine ? '5, 5' : null); // 使用虚线或实线
        });
    });

    // 如果 smoothnessValue 在 0 到 1 之间，则绘制平滑曲线
    if (smoothnessValue.value > 0 && smoothnessValue.value <= 1) {
        clipGroup.append('path')
            .datum(smoothedYValue)  // 使用平滑后的数据
            .attr('class', 'smoothed-line')  // 给平滑线条添加 class
            .attr('fill', 'none')
            .attr('stroke', color || 'steelblue')  // 确保平滑线条颜色和原始线条一致
            .attr('stroke-width', 1.5)
            .attr('d', line);
    }

    // 总览条的缩放比例尺
    const xOverview = d3.scaleLinear()
        .domain([-2, 6])
        .range([0, width]);

    const yOverview = d3.scaleLinear()
        .domain([yMin, yMax])
        .range([overviewHeight, 0]);

    // 在总览条中绘制简化版曲线
    const overviewG = overviewSvg
        .attr('width', width + margin.left + margin.right)
        .attr('height', overviewHeight + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    overviewG.append('path')
        .datum(data.Y_value)
        .attr('fill', 'none')
        .attr('stroke', color || 'steelblue')
        .attr('stroke-width', 1)
        .attr('d', d3.line()
            .x((d, i) => xOverview(data.X_value[i]))
            .y((d, i) => yOverview(d))
            .curve(d3.curveBasis));

    // 添加异常数据到总览条中
    errorsData.forEach((errorData, errorIndex) => {
        errorData.X_value_error.forEach((X_value_error, index) => {
            const Y_value_error = errorData.Y_value_error[index];

            const errorOverviewLine = d3.line()
                .x((d, i) => xOverview(X_value_error[i]))
                .y((d, i) => yOverview(Y_value_error[i]))
                .curve(d3.curveMonotoneX);

            overviewG.append('path')
                .datum(Y_value_error)
                .attr('class', `error-overview-line-${index}-${channelName}`)  // 给每条异常线段一个唯一的 class
                .attr('fill', 'none')
                .attr('stroke', errorData.color || 'red')
                .attr('stroke-width', 4)
                .attr('opacity', 0.5)
                .attr('d', errorOverviewLine)
                .attr('stroke-dasharray', errorData.person === 'machine' ? '5, 5' : null);
        });
    });

    // 添加 X 轴到总览条
    overviewG.append('g')
        .attr('transform', `translate(0,${overviewHeight})`)
        .call(d3.axisBottom(xOverview));

    // brush 回调函数
    function brushed(event) {
        const selection = event.selection || xOverview.range();
        const newDomain = selection.map(xOverview.invert, xOverview);
        x.domain(newDomain);

        // 存储新的域和刷子选择
        xDomains.value[channelName] = x.domain();
        brushSelections.value[channelName] = selection;

        // 更新主图的 X 轴
        g.selectAll('g.x-axis').call(d3.axisBottom(x));

        // 更新主图中的原始线条
        g.selectAll('path.original-line')
            .attr('d', d3.line()
                .x((d, i) => x(data.X_value[i]))
                .y((d, i) => y(data.Y_value[i]))
            );

        // 更新平滑线条（如果存在）
        if (smoothnessValue.value > 0 && smoothnessValue.value <= 1) {
            g.selectAll('path.smoothed-line')
                .attr('d', d3.line()
                    .x((d, i) => x(data.X_value[i]))
                    .y((d, i) => y(smoothedYValue[i]))
                );
        }

        // 更新异常线条
        errorsData.forEach(errorData => {
            errorData.X_value_error.forEach((X_value_error, index) => {
                const Y_value_error = errorData.Y_value_error[index];

                // 更新异常线条的路径
                g.selectAll(`.error-line-${index}-${channelName}`)
                    .attr('d', d3.line()
                        .x((d, i) => x(X_value_error[i]))
                        .y((d, i) => y(Y_value_error[i]))
                    );
            });
        });

        // 更新自定义的异常区域
        updateAnomaliesOnZoom();
    }

    // 绘制用户自定义的异常区域
    const channelAnomalies = anomalies.value.filter(a => a.channelName === channelName);

    channelAnomalies.forEach((anomaly, index) => {
        drawAnomalyElements(anomaly, index);
    });

    // 从 Vuex store 中获取已保存的异常，并绘制
    const storedAnomalies = store.getters.getAnomaliesByChannel(channelName);
    storedAnomalies.forEach((anomaly, index) => {
        drawAnomalyElements(anomaly, index, true); // 第三个参数标记为已保存
    });

    function drawAnomalyElements(anomaly, index, isStored = false) {
        // 创建一个组，将异常的所有元素添加到该组中，方便管理层级
        const anomalyGroup = clipGroup.append('g')
            .attr('class', `anomaly-group-${index}-${channelName}`);

        if (!isStored) {
            // 添加手柄和按钮（先添加，这样它们在上层）
            // Left handle
            anomalyGroup.append('rect')
                .attr('class', `left-handle-${index}-${channelName}`)
                .attr('x', x(anomaly.startX) - 5)
                .attr('y', 0)
                .attr('width', 10)
                .attr('height', height)
                .attr('fill', 'transparent')
                .attr('cursor', 'ew-resize')
                .style('pointer-events', 'all')
                .call(
                    d3.drag()
                        .on('drag', function (event) {
                            const newX = x.invert(event.x);
                            if (newX < anomaly.endX && newX >= x.domain()[0]) {
                                anomaly.startX = newX;
                                updateAnomalyElements(anomaly, index);
                            }
                        })
                        .on('end', function () {
                            anomalies.value[index] = anomaly;
                        })
                );

            // Right handle
            anomalyGroup.append('rect')
                .attr('class', `right-handle-${index}-${channelName}`)
                .attr('x', x(anomaly.endX) - 5)
                .attr('y', 0)
                .attr('width', 10)
                .attr('height', height)
                .attr('fill', 'transparent')
                .attr('cursor', 'ew-resize')
                .style('pointer-events', 'all')
                .call(
                    d3.drag()
                        .on('drag', function (event) {
                            const newX = x.invert(event.x);
                            if (newX > anomaly.startX && newX <= x.domain()[1]) {
                                anomaly.endX = newX;
                                updateAnomalyElements(anomaly, index);
                            }
                        })
                        .on('end', function () {
                            anomalies.value[index] = anomaly;
                        })
                );

            // 添加按钮
            const buttonGroup = anomalyGroup.append('g')
                .attr('class', `anomaly-buttons-${index}-${channelName}`)
                .attr('transform', `translate(${x(anomaly.endX) - 40}, ${height - 20})`)
                .style('pointer-events', 'all');

            // 删除按钮
            buttonGroup.append('rect')
                .attr('width', 16)
                .attr('height', 16)
                .attr('fill', 'red')
                .attr('cursor', 'pointer')
                .on('click', () => {
                    // 从本地 anomalies 数组中移除
                    anomalies.value.splice(index, 1);
                    // 从图表中移除对应元素
                    removeAnomalyElements(index, channelName);
                });

            buttonGroup.append('text')
                .attr('x', 8)
                .attr('y', 12)
                .attr('text-anchor', 'middle')
                .attr('fill', 'white')
                .attr('pointer-events', 'none')
                .text('删');

            // 编辑按钮
            buttonGroup.append('rect')
                .attr('x', 20) // 相对于删除按钮
                .attr('width', 16)
                .attr('height', 16)
                .attr('fill', 'blue')
                .attr('cursor', 'pointer')
                .on('click', () => {
                    // 编辑异常
                    currentAnomaly.value = anomaly;
                    showAnomalyForm.value = true;
                });

            buttonGroup.append('text')
                .attr('x', 28)
                .attr('y', 12)
                .attr('text-anchor', 'middle')
                .attr('fill', 'white')
                .attr('pointer-events', 'none')
                .text('编');

            // 添加选框矩形
            const anomalyRect = anomalyGroup.append('rect')
                .attr('class', `anomaly-rect-${index}-${channelName}`)
                .attr('x', x(anomaly.startX))
                .attr('y', 0)
                .attr('width', x(anomaly.endX) - x(anomaly.startX))
                .attr('height', height)
                .attr('fill', 'orange')
                .attr('fill-opacity', 0.1)
                .attr('stroke', 'orange')
                .attr('stroke-width', 1)
                .attr('cursor', 'move')
                .style('pointer-events', 'all')
                .call(
                    d3.drag()
                        .on('start', function (event) {
                            anomaly.initialX = event.x;
                        })
                        .on('drag', function (event) {
                            const dx = x.invert(event.x) - x.invert(anomaly.initialX);
                            anomaly.initialX = event.x;

                            // 计算新的位置
                            let newStartX = anomaly.startX + dx;
                            let newEndX = anomaly.endX + dx;

                            // 确保矩形不超出范围
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

                            updateAnomalyElements(anomaly, index);
                        })
                        .on('end', function () {
                            anomalies.value[index] = anomaly;
                        })
                );
        } else {
            // 已保存的异常，仅添加矩形，无交互
            const anomalyRect = anomalyGroup.append('rect')
                .attr('class', `anomaly-rect-${index}-${channelName}`)
                .attr('x', x(anomaly.startX))
                .attr('y', 0)
                .attr('width', x(anomaly.endX) - x(anomaly.startX))
                .attr('height', height)
                .attr('fill', 'green')
                .attr('fill-opacity', 0.1)
                .attr('stroke', 'green')
                .attr('stroke-width', 1)
                .style('pointer-events', 'none');
        }

        // 绘制高亮线段
        const startIndex = data.X_value.findIndex(xVal => xVal >= anomaly.startX);
        const endIndex = data.X_value.findIndex(xVal => xVal >= anomaly.endX);
        const anomalyXValues = data.X_value.slice(startIndex, endIndex + 1);
        const anomalyYValues = data.Y_value.slice(startIndex, endIndex + 1);

        anomalyGroup.append('path')
            .datum(anomalyYValues)
            .attr('class', `anomaly-line-${index}-${channelName}`)
            .attr('fill', 'none')
            .attr('stroke', isStored ? 'green' : 'orange')
            .attr('stroke-width', 3)
            .attr('d', d3.line()
                .x((d, i) => x(anomalyXValues[i]))
                .y((d, i) => y(d))
            );
    }

    function updateAnomalyElements(anomaly, index, isStored = false) {
        // 更新元素位置
        const anomalyGroup = clipGroup.select(`.anomaly-group-${index}-${channelName}`);

        anomalyGroup.select(`.anomaly-rect-${index}-${channelName}`)
            .attr('x', x(anomaly.startX))
            .attr('width', x(anomaly.endX) - x(anomaly.startX));

        anomalyGroup.select(`.left-handle-${index}-${channelName}`)
            .attr('x', x(anomaly.startX) - 5);

        anomalyGroup.select(`.right-handle-${index}-${channelName}`)
            .attr('x', x(anomaly.endX) - 5);

        anomalyGroup.select(`.anomaly-buttons-${index}-${channelName}`)
            .attr('transform', `translate(${x(anomaly.endX) - 40}, ${height - 20})`);

        // 更新高亮线段
        const startIndex = data.X_value.findIndex((xVal) => xVal >= anomaly.startX);
        const endIndex = data.X_value.findIndex((xVal) => xVal >= anomaly.endX);
        const anomalyXValues = data.X_value.slice(startIndex, endIndex + 1);
        const anomalyYValues = data.Y_value.slice(startIndex, endIndex + 1);

        anomalyGroup.select(`.anomaly-line-${index}-${channelName}`)
            .datum(anomalyYValues)
            .attr(
                'd',
                d3
                    .line()
                    .x((d, i) => x(anomalyXValues[i]))
                    .y((d, i) => y(d))
            );
    }

    function removeAnomalyElements(index, channelName) {
        clipGroup.select(`.anomaly-group-${index}-${channelName}`).remove();
    }

    function updateAnomaliesOnZoom() {
        anomalies.value.filter(a => a.channelName === channelName).forEach((anomaly, index) => {
            updateAnomalyElements(anomaly, index);
        });

        // 更新已保存的异常
        const storedAnomalies = store.getters.getAnomaliesByChannel(channelName);
        storedAnomalies.forEach((anomaly, index) => {
            updateAnomalyElements(anomaly, index, true);
        });
    }

    // 添加 brush 用于交互缩放
    const brush = d3.brushX()
        .extent([[0, 0], [width, overviewHeight]])
        .on('brush end', brushed);

    const brushG = overviewG.append('g')
        .attr('class', 'brush')
        .call(brush);

    // 如果存在存储的滑块选区
    if (brushSelections.value[channelName]) {
        const fullRange = xOverview.range();
        const selection = brushSelections.value[channelName];

        // 检查滑块选区是否等于全选范围
        if (selection[0] === fullRange[0] && selection[1] === fullRange[1]) {
            brushG.call(brush);  // 仅初始化，不移动
        } else {
            brushG.call(brush.move, selection);
        }
    } else {
        brushG.call(brush);  // 仅初始化，不移动
    }

    // 添加主图区域的选择 brush
    const selectionBrush = d3.brushX()
        .extent([[0, 0], [width, height]])
        .on('end', selectionBrushed);

    g.append('g')
        .attr('class', 'selection-brush')
        .call(selectionBrush);

    function selectionBrushed(event) {
        if (!event.sourceEvent) return;
        if (!event.selection) return;

        const [x0, x1] = event.selection;
        const [startX, endX] = [x.invert(x0), x.invert(x1)];

        const anomaly = {
            channelName: channelName,
            startX: startX,
            endX: endX,
            anomalyCategory: '',
            anomalyDiagnosisName: '',
            anomalyDescription: ''
        };

        // 移除选择框
        d3.select(this).call(selectionBrush.move, null);

        // 添加到本地 anomalies 数组
        anomalies.value.push(anomaly);

        // 绘制异常元素
        drawAnomalyElements(anomaly, anomalies.value.length - 1);
    }
};

// 保存异常信息
const saveAnomaly = () => {
    if (currentAnomaly.value) {
        // 将异常添加到 Vuex store
        const payload = {
            channelName: currentAnomaly.value.channelName,
            anomaly: { ...currentAnomaly.value }
        };
        store.dispatch('addAnomaly', payload);

        // 从本地 anomalies 数组中移除
        const index = anomalies.value.findIndex(a => a === currentAnomaly.value);
        if (index !== -1) {
            anomalies.value.splice(index, 1);
        }

        showAnomalyForm.value = false;
        currentAnomaly.value = null;
        ElMessage.success('异常信息已保存');

        // 重新绘制图表，包含已保存的异常
        fetchDataAndDrawChart(
            selectedChannels.value.find((ch) => ch.channel_name === payload.channelName)
        );
    }
};

// 关闭异常表单
const closeAnomalyForm = () => {
    showAnomalyForm.value = false;
    currentAnomaly.value = null;
};
</script>

<style scoped>
.chart-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    width: 100%;
}

.chart-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
    width: 100%;
    margin-bottom: 20px;
}

svg {
    width: 100%;
    position: relative;
}

.divider {
    width: 100%;
    height: 10px;
}
</style>
