<template>
    <!-- 热力图组件 -->
    <svg id="heatmap"></svg>
</template>

<script setup>
import * as d3 from 'd3';
import { onMounted, watch, computed } from 'vue';
import { useStore } from 'vuex';


const store = useStore();
const selectedChannels = computed(() => store.state.selectedChannels);

const storePerson = computed(store.state.person);

onMounted(() => {
    watch(
        selectedChannels,
        (newChannels) => {
            renderHeatmap(newChannels);
        },
        { immediate: true }
    );
});

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
    let errorIdx = 1;

    let errorPromises = [];

    // 对于每个通道
    for (let channel of channels) {
        let channel_name = channel.channel_name;
        visData[channel_name] = [];
        for (let i = 0; i < rectNum; i++) {
            visData[channel_name][i] = []; // 初始化为数组
        }

        // 对于每个错误
        for (let error of channel.errors) {
            let errorIdxCurrent = errorIdx;
            errorColors[errorIdxCurrent] = error.color;

            let errorPromise = d3
                .json(error.path)
                .then((errorData) => {
                    return { channel_name, errorIdx: errorIdxCurrent, errorData };
                })
                .catch((err) => {
                    console.error(`Failed to fetch error data from ${error.path}:`, err);
                    return null;
                });

            errorPromises.push(errorPromise);

            errorIdx += 1;
        }
    }

    // 等待所有错误数据加载完成
    let errorResults = await Promise.all(errorPromises);

    // 处理错误数据
    for (let result of errorResults) {
        if (result === null) continue; // 跳过失败的请求
        const { channel_name, errorIdx, errorData } = result;
        const X_value_error = errorData['X_value_error'];

        // 对于每个错误区间
        for (let idxList of X_value_error) {
            let left = Math.trunc((idxList[0] - Domain[0]) / step);
            let right = Math.trunc((idxList[idxList.length - 1] - Domain[0]) / step);
            for (let i = left; i <= right; i++) {
                if (i >= 0 && i < rectNum) {
                    visData[channel_name][i].push(errorIdx); // 将错误索引加入数组
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
            `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom
            }`
        )
        .attr('preserveAspectRatio', 'xMidYMid meet')
        .attr('width', '100%') // 确保宽度自适应父容器

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
                    if (channel.errors.length > 1) {
                        // 如果该通道包含多个 error 对象，使用灰色
                        return '#999999';
                    } else if (channel.errors.length === 1) {
                        // 如果是单个异常，不论有多少异常段，只算一个异常
                        const errorIdx = d[0];
                        const errorData = errorResults.find(
                            (result) => result && result.errorIdx === errorIdx
                        );
                        if (errorData && errorData.errorData.person === 'machine') {
                            // person 为 machine 时，填充颜色
                            return errorColors[errorIdx];
                        } else {
                            // person 不是 machine 时，不填充颜色（返回正常颜色）
                            return '#f5f5f5';
                        }
                    } else {
                        return '#f5f5f5'; // 正常数据颜色
                    }
                })
                .attr('stroke', (d) => {
                    if (channel.errors.length > 1) {
                        // 如果该通道包含多个 error 对象，使用灰色边框
                        return '#ccc';
                    } else if (channel.errors.length === 1) {
                        // 单个异常时，根据 person 字段来设置是否显示边框
                        const errorIdx = d[0];
                        const errorData = errorResults.find(
                            (result) => result && result.errorIdx === errorIdx
                        );
                        if (errorData && errorData.errorData.person !== 'machine') {
                            // person 不是 machine 时，加边框
                            return errorColors[errorIdx];
                        } else {
                            return 'none'; // person 为 machine 时，不加边框
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
                    if (channel.errors.length > 1) {
                        // 多个 error 对象时，使用虚线框
                        return '4 2';
                    } else if (channel.errors.length === 1) {
                        // 单个异常时，检查 person 字段是否与 store 中的 person 相同
                        const errorIdx = d[0];
                        const errorData = errorResults.find(
                            (result) => result && result.errorIdx === errorIdx
                        );
                        if (errorData && errorData.errorData.person !== storePerson) {
                            // 如果 person 值不相同，使用虚线框
                            return '4 2';
                        } else {
                            // 如果 person 值相同，使用实线框
                            return '0';
                        }
                    } else {
                        return '0'; // 正常数据或没有异常时，使用实线框
                    }
                });
        });



}
</script>

<style scoped>
#heatmap {
    margin-top: 10px;
    width: 100%;
    height: auto;
}
</style>