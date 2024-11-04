<template>
    <span style="display: flex; justify-content: center; align-items: center; width: 85%;">
        <el-button type="primary" plain size="large" @click="appendToClickedChannelNames('+')">加</el-button>
        <el-button type="primary" plain size="large" @click="appendToClickedChannelNames('-')">减</el-button>
        <el-button type="primary" plain size="large" @click="appendToClickedChannelNames('*')">乘</el-button>
        <el-button type="primary" plain size="large" @click="appendToClickedChannelNames('/')">除</el-button>
        <el-button type="primary" plain size="large" @click="appendToClickedChannelNames('(')">(</el-button>
        <el-button type="primary" plain size="large" @click="appendToClickedChannelNames(')')">)</el-button>
        <el-button type="primary" plain size="large" @click="appendToClickedChannelNames('>')">></el-button>
        <el-button type="primary" plain size="large" @click="appendToClickedChannelNames('<')"><</el-button>
        <el-button type="primary" plain size="large" @click="appendToClickedChannelNames('=')">=</el-button>
        <el-button type="primary" plain size="large" @click="appendToClickedChannelNames('FFT(')">傅里叶变换 FFT</el-button>
        <el-button type="info" plain size="large">自定义算法</el-button>
        <el-button type="success" plain size="large">算法导入</el-button>
    </span>
</template>

<script setup>
import { useStore } from 'vuex';

const store = useStore();

const appendToClickedChannelNames = (content) => {
    store.commit('appendChannelName', content);
};
</script>

<style scoped lang="scss"></style>
