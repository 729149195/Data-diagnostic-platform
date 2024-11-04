<template>
    <div class="cards">
        <el-card v-for="(channel, index) in selectedChannels" :key="channel.channel_name" class="channel-card"
            style="width: 19%" shadow="hover">
            <div class="channel-content">
                <div style="display: flex; align-items: center;">
                    {{ channel.channel_name }}
                    <el-input style="width:4em; margin-left: 5px;" placeholder="KHz" size="small" />
                </div>
                <el-color-picker v-model="channel.color" @change="setSingleChannelColor(channel)"
                    class="channel-color-picker" show-alpha :predefine="predefineColors" size="small" />
            </div>
            <div :id="'chart-' + sanitizeChannelName(channel.channel_name)" class="chart-container"
                @click="handleCardClick(channel.channel_name)"></div>
        </el-card>
    </div>
</template>

<script setup>
import { computed, ref, onMounted, watch, nextTick } from 'vue';
import { useStore } from 'vuex';
import axios from 'axios';
import debounce from 'lodash/debounce';
import * as d3 from 'd3';

const store = useStore();

const handleCardClick = (channelName) => {
    store.dispatch("appendChannelNameToClicked", channelName);
};



const predefineColors = ref([
    'rgba(255, 215, 0, 0)',
    '#4169E1',
    '#DC143C',
    '#228B22',
    '#FF8C00',
    '#800080',
    '#FF1493',
    '#40E0D0',
    '#FFD700',
    '#8B4513',
    '#2F4F4F',
    '#1E90FF',
    '#32CD32',
    '#FF6347',
    '#DA70D6',
    '#191970',
    '#FA8072',
    '#6B8E23',
    '#6A5ACD',
    '#FF7F50',
    '#4682B4',
]);

const selectedChannels = computed(() => store.getters.getSelectedChannels);

const sanitizeChannelName = (name) => {
    return name.replace(/[^a-zA-Z0-9]/g, '');
};

const setSingleChannelColor = (channel) => {
    if (channel) {
        channel.color = channel.color;
        updateSelectedChannels();
        fetchChannelData(channel);
    } else {
        console.error('Invalid channel:', channel);
    }
};

const updateSelectedChannels = () => {
    const selected = selectedChannels.value.map((item) => ({
        channel_name: item.channel_name,
        path: item.path,
        color: item.color,
        errors: item.errors.map((error) => ({
            errors_name: error.errors_name,
            path: error.path,
            color: error.color,
        })),
    }));

    store.commit('updateSelectedChannels', selected);
};

// Cache to store fetched data
const dataCache = {};

// Efficient sampling function
const sampleData = (data, numSamples) => {
    const sampledData = [];
    const dataLength = data.length;
    if (dataLength <= numSamples) {
        return data.slice();
    }
    const samplingInterval = dataLength / numSamples;
    for (let i = 0; i < numSamples; i++) {
        sampledData.push(data[Math.floor(i * samplingInterval)]);
    }
    return sampledData;
};

const fetchChannelData = async (channel) => {
    try {
        // Use cached data if available
        let xValues, yValues;

        if (dataCache[channel.path]) {
            ({ xValues, yValues } = dataCache[channel.path]);
        } else {
            const response = await axios.get(channel.path);
            xValues = response.data.X_value;
            yValues = response.data.Y_value;
            dataCache[channel.path] = { xValues, yValues };
        }

        // Efficient sampling to reduce data size
        const numSamples = 100; // Adjust this value as needed
        const sampledXValues = sampleData(xValues, numSamples);
        const sampledYValues = sampleData(yValues, numSamples);

        // Draw the chart
        renderChart(sampledXValues, sampledYValues, channel);
    } catch (error) {
        console.error('Error fetching channel data:', error);
    }
};

const renderChart = (xValues, yValues, channel) => {
    const containerId = 'chart-' + sanitizeChannelName(channel.channel_name);
    const container = d3.select('#' + containerId);

    // Clear any existing content
    container.selectAll('*').remove();

    const containerWidth = container.node().clientWidth;
    const containerHeight = 50; // Adjust as needed

    const margin = { top: 5, right: 5, bottom: 5, left: 5 };
    const width = containerWidth - margin.left - margin.right;
    const height = containerHeight - margin.top - margin.bottom;

    const svg = container
        .append('svg')
        .attr('width', containerWidth)
        .attr('height', containerHeight)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    const xScale = d3
        .scaleLinear()
        .domain(d3.extent(xValues))
        .range([0, width]);

    const yScale = d3
        .scaleLinear()
        .domain(d3.extent(yValues))
        .range([height, 0]);

    const line = d3
        .line()
        .x((d, i) => xScale(xValues[i]))
        .y((d, i) => yScale(yValues[i]));

    svg
        .append('path')
        .datum(yValues)
        .attr('fill', 'none')
        .attr('stroke', channel.color || 'steelblue')
        .attr('stroke-width', 1.5)
        .attr('d', line);
};

// Fetch data and render charts in parallel
const renderCharts = debounce(async () => {
    await Promise.all(
        selectedChannels.value.map((channel) => fetchChannelData(channel))
    );
}, 150);

watch(
    selectedChannels,
    async (newChannels, oldChannels) => {
        if (JSON.stringify(newChannels) !== JSON.stringify(oldChannels)) {
            await nextTick();
            renderCharts();
        }
    },
    { deep: true }
);

onMounted(() => {
    renderCharts();
});
</script>

<style scoped lang="scss">
.channel-card {
    margin: 5px;
}

.channel-content {
    display: flex;
    justify-content: space-between;
}

.cards {
    display: flex;
    flex-wrap: wrap;
    justify-content: start;
    width: 100%;
    height: 100%;
    max-height: 21vh;
    overflow-y: auto;
    margin-top: 10px;

    .el-card {
        --el-card-padding: 8px;
        cursor: pointer;
    }
}

.chart-container {
    width: 100%;
    height: 50px;
}
</style>
