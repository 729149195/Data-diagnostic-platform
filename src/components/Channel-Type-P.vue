<template>
    <!-- 全局表头 -->
    <el-input v-model="search" placeholder="请输入内容" :prefix-icon="Search" />
    <div class="header-row">
        <span>通道类别</span>
        <span>通道名</span>
        <span>频率</span>
    </div>

    <!-- 渲染每个 channel_type 卡片 -->
    <div v-for="(item, index) in data" :key="index" class="card">
        <!-- 通道类别行 -->
        <table class="channel-table">
            <tbody>
                <!-- 渲染每个通道名及其对应的异常类别 -->
                <template v-for="(channel, cIndex) in item.channels" v-if="item.channels && item.channels.length">
                    <tr v-for="(error, eIndex) in channel.errors" :key="`${cIndex}-${eIndex}`"
                        v-if="channel.errors && channel.errors.length">
                        <!-- 通道类别：合并属于该通道类别的所有通道名的行，并且内容上对齐 -->
                        <td v-if="eIndex === 0 && cIndex === 0"
                            :rowspan="item.channels.reduce((total, c) => total + c.errors.length, 0)"
                            class="channel-type">
                            <span>{{ item.channel_type }}</span>
                            <div class="type-header">
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
                                <span class="channel-name-text">{{ channel.channel_name }}</span>
                                <div class="name-right">
                                    <el-checkbox v-model="channel.checked" @change="updateChannelTypeCheckbox(item)"
                                        class="checkbox-margin"></el-checkbox>
                                </div>
                                <span><el-input style="width:7em" placeholder="KHz" /></span>
                            </div>
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
import { Search } from '@element-plus/icons-vue'


const store = useStore()
const data = ref([])
const search = ref()


const dataLoaded = ref(false);


onMounted(async () => {
    try {
        if (!store.getters.getStructTree) {
            await store.dispatch('fetchStructTree');
        }
        data.value = store.getters.getStructTree;
        dataLoaded.value = true; // 标记数据已经加载完成
        updateSelectedChannels();
    } catch (error) {
        console.error('获取 StructTree 数据时发生错误:', error);
    }
});


// 确保 formatError 函数在这里定义
const formatError = (name) => {
    if (name.length > 8) {
        return name.slice(0, 8) + '...'
    }
    return name
}


// 更新选中通道信息
const updateSelectedChannels = () => {
    if (!dataLoaded.value) {
        console.warn('数据尚未加载，无法更新选中通道信息');
        return;
    }

    const selected = [];

    data.value.forEach(item => {
        if (item && item.channels) {
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
                    });
                }
            });
        }
    });

    store.commit('updateSelectedChannels', selected);
};


// 设置通道复选框联动，通道类型的复选框会影响所有通道复选框
const toggleChannelCheckboxes = (item) => {
    item.channels.forEach((channel) => {
        channel.checked = item.checked
    })
    updateSelectedChannels()
}

// 当通道复选框状态变化时，更新通道类型的复选框
const updateChannelTypeCheckbox = (item) => {
    if (!item || !item.channels) {
        console.error('Invalid item or channels:', item);
        return;
    }

    // 如果所有通道都被选中，通道类型复选框选中，否则取消选中
    item.checked = item.channels.every(channel => channel.checked);
    updateSelectedChannels();
};


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
    vertical-align: top;
    /* 上对齐 */
    text-align: center;
}

.channel-type {
    width: 30%;
    vertical-align: top;
    /* 通道类别列的内容上对齐 */
    text-align: center;
}

.channel-name {
    width: 65%;
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
    width: 35%;
    text-align: center;
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
    margin-right: 15px;
}

.channel-name-last {
    border-bottom: none;
}

.channel-name-text {
  display: flex;
  justify-content: center; 
  width: 30%;
  overflow: hidden;
  text-overflow: ellipsis; 
  white-space: nowrap;
}

</style>