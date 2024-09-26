<template>
<!-- 热力图组件 -->
  <svg id="heatmap"></svg>
</template>

<script setup>
import * as d3 from 'd3';
import {onMounted} from "vue";

onMounted(async () => {
    const headmap = d3.select('#heatmap')

// 从 public 中读数据

    // 从 StructTree 中读目录结构
    const readStructTree = new Promise(resolve => {
        d3.json('public/dataset/StructTree.json').then(data => resolve(data));
    })
    let channelTypeMap = {};
    let channelTypeRMap = {};

    let channelErrorMap = {};
    await readStructTree.then(data => {
        data.forEach(d => {
            channelTypeMap[d['channel_type']] = Object.keys(d['channels']);
            for (let channel of Object.keys(d['channels'])) {
                channelTypeRMap[channel] = d['channel_type'];
            }

            for (let [channel, value] of Object.entries(d['channels'])) {
                channelErrorMap[channel] = [];
                for (let error in value['errors']) {
                    channelErrorMap[channel].push(error);
                }
            }
        })
    })





    // 读取每个通道的异常数据
    console.log(channelErrorMap);
    let PromiseList = [];
    let channelErrorDatasetMap = {};
    for(let [channel, errorList] of Object.entries(channelErrorMap)) {
        for(let error of errorList) {
            PromiseList.push(new Promise(resolve => {
                // console.log(`public/dataset/${channelTypeRMap[channel]}/error/${error}.json`);
                d3.json(`public/dataset/${channelTypeRMap[channel]}/error/${error}.json`).then(data => resolve([channel, data]));
            }));
        }
    }
    await Promise.all(PromiseList).then(rets => {
        for(let ret of rets) {
            channelErrorDatasetMap[ret[0]] ? '' : channelErrorDatasetMap[ret[0]] = [];
            channelErrorDatasetMap[ret[0]].push(ret[1])
        }
    })

    // 统计每个通道的异常数据
// 0-正常  -1-多异常  12345-多种异常
    let Domain = [-2, 6];
    let step = 0.5;
    let rectNum = Math.round((Domain[1]-Domain[0]) / step);
    console.log(rectNum)
    let errorIdx = 1;
    let visData = {};


    for(let [channel, errorDataset] of Object.entries(channelErrorDatasetMap)) {
        visData[channel] = new Array(16).fill(0);
        for(let errorData of errorDataset) {
            let X_value_error = errorData['X_value_error'];
            for(let idxList of X_value_error) {
                let left = Math.trunc((idxList[0] - Domain[0]) / step);
                let right = Math.trunc((idxList[idxList.length-1] - Domain[0]) / step);
                for(let i = left;i<=right;i++) {
                    let now = visData[channel][i];
                    if(now > 0) visData[channel][i] = -1;
                    if(now === -1) '';
                    if(now === 0) visData[channel][i] = errorIdx++;
                }
            }
        }
    }
    console.log(visData)
    let channels = Object.keys(visData);

// 绘图
    let width = 960;
    let height = 200;
    let margin = 5
    let XaxisH = 20;
    let YaxisW = 100;
    let rectW = (width-YaxisW-margin) / rectNum - margin;
    let rectH = (height-XaxisH-margin) / channels.length - margin;

    let xAxisTick = [];

    let colorMap = ['#f42717', '#ff543d', '#4480e2', '#57ce7d'];


    for(let i=Domain[0];i<=Domain[1];i+=step) {
        xAxisTick.push(i);
    }
    console.log(xAxisTick)


    headmap.selectAll('.channelName')
        .data(channels)
        .join('text')
        .attr('class', 'channelName')
        .attr('x', YaxisW - margin)
        .attr('y', (d, i) => rectH * 0.5 + 5 + XaxisH+i*(rectH+margin))
        .style('text-anchor', 'end')
        .text(d => d)

    headmap.selectAll('.xTick')
        .data(xAxisTick)
        .join('text')
        .attr('class', 'xTick')
        .attr('x', (d, i) => YaxisW + i*(rectW+margin) + 5)
        .attr('y', (d, i) => XaxisH/2 + 3)
        .style('text-anchor', 'end')
        .text(d => d)

    headmap.selectAll('.channelName')
        .data(channels)
        .join('text')
        .attr('x', YaxisW - margin)
        .attr('y', (d, i) => rectH * 0.5 + 5 + XaxisH+i*(rectH+margin))
        .style('text-anchor', 'end')
        .text(d => d)


    headmap.selectAll('.heatmapRectG')
        .data(Object.values(visData))
        .join('g')
        .attr('class', 'heatmapRectG')
        .attr('transform', (d, i) => `translate(${YaxisW}, ${XaxisH+i*(rectH+margin)})`)
        .selectAll('.heatmapRect')
        .data(d => d)
        .join('rect')
        .attr('class', 'heatmapRect')
        .attr('x', (d, i) => i*(rectW+margin))
        .attr('y', 0)
        .attr('width', rectW)
        .attr('height', rectH)
        .attr('fill', d => {
            if(d > 0) {
                return colorMap[d-1];
            }
            else if(d < 0) {
                return '#999999';
            }
            else {
                return '#f5f5f5'
            }
        })
        .attr('stroke', (d, i) => {
            if(d > 0) {
                return colorMap[d-1];
            }
            else if(d < 0) {
                return '#999999';
            }
            else {
                if(i === 10) return '#ff543d'
                if(i === 12) return '#4480e2'
                return '#f5f5f5'
            }
        })
        .attr('stroke-dasharray', (d, i) => {
            if(d > 0) {
                return '';
            }
            else if(d < 0) {
                return '';
            }
            else {
                if(i === 10) return '5, 4'
                return ''
            }
        })
})




</script>

<style scoped>
  #heatmap {
    margin-top: 10px;
    width: 960px;
    height: 200px;
  }
</style>