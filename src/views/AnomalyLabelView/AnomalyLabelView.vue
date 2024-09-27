<template>
  <div class="all-layout">
    <el-container>
      <el-header class="header">
        <el-dropdown trigger="click">
          <el-avatar :style="avatarStyle" size="medium">{{ avatarText }}</el-avatar>
          <template #dropdown>
            <el-dropdown-menu class="user-dropdown">
              <div class="user-info">
                <p><span>用户:</span> {{ person }}</p>
                <p><span>权限: </span>{{ authorityLabel }}</p>
              </div>
              <el-dropdown-item divided @click="logout">退出</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-container>
        <el-aside class="aside">
          <div class="aside-content">
            <el-card class="jump_switch" shadow="never">
              <el-button class="test" :class="{ selected: selectedButton === 'test' }"
                :type="selectedButton === 'test' ? 'primary' : 'default'" size="large" @click="selectButton('test')">
                <el-icon :size="20">
                  <DataAnalysis />
                </el-icon>
                <span v-if="selectedButton === 'test'">实验数据分析</span>
              </el-button>
              <el-button class="channel" :class="{ selected: selectedButton === 'channel' }"
                :type="selectedButton === 'channel' ? 'primary' : 'default'" size="large"
                @click="selectButton('channel')">
                <el-icon :size="20">
                  <Odometer />
                </el-icon>
                <span v-if="selectedButton === 'channel'">通道分析模块</span>
              </el-button>
            </el-card>
            <el-card class="table" shadow="never" v-if="selectedButton === 'test'">
              <span style="display: flex; align-items: center; margin-bottom: 5px;">
                <span class="title">可视化配置</span>
                <el-switch class="color_table_switch" v-model="color_table_value"
                  style="--el-switch-on-color: #409EFF; --el-switch-off-color: #409EFF" active-text="通道颜色"
                  inactive-text="异常颜色" />
              </span>
              <el-input v-model="table_search" placeholder="请输入内容" :prefix-icon="Search" />
              <div>
                <div v-if="color_table_value === true">
                  <ChannelType />
                </div>
                <div v-if="color_table_value === false">
                  <ExceptionType />
                </div>
              </div>
            </el-card>
            <el-card class="table" shadow="never" v-if="selectedButton === 'channel'">
              <span style="display: flex;margin-bottom: 5px; justify-content: space-between;">
                <span class="title">可视化配置</span>
                <span><el-input v-model="table_search" style="width: 200px;" placeholder="请输入内容"
                    :prefix-icon="Search" />
                </span>
              </span>
              <div style="display: flex; justify-content: center; align-items: center;">
                <ChannelTypeP />
              </div>
            </el-card>
          </div>
        </el-aside>
        <el-container>
          <el-main class="test_main" v-if="selectedButton === 'test'">
            <el-card class="data_exploration" shadow="never">
              <span style="display: flex; align-items: center; justify-content: space-between;">
                <span class="title">实验数据探索</span>
                <span>采样率 <el-input-number v-model="sampling" :precision="2" :step="0.1" :max="1" :min="0.0001"
                    @change="updateSampling" /></span>
                <span>平滑度 <el-input-number v-model="smoothness" :precision="2" :step="0.1" :max="1" :min="0.0"
                    @change="updateSmoothness" /></span>
                <el-switch v-model="test_channel_number"
                  style="--el-switch-on-color: #409EFF; --el-switch-off-color: #409EFF" active-text="单通道多行"
                  inactive-text="多通道单行" />
                <img src="/image1.png" style="height: 30px;" alt="图例">
                <el-button type="primary">
                  导出<el-icon class="el-icon--right">
                    <Upload />
                  </el-icon>
                </el-button>
              </span>
              <el-scrollbar height="62vh" :always="true">
                <div style="display: flex; justify-content: center; align-items: center;">
                  <div v-if="test_channel_number === true" style="width: 100%;">
                    <SingleChannelMultiRow />
                  </div>
                  <div v-if="test_channel_number === false" style="width: 100%;">
                    <MultiChannelSingleRow />
                  </div>

                </div>
              </el-scrollbar>
            </el-card>
            <div class="two">
              <el-card class="two_left" shadow="never">
                <span style="display: flex; align-items: center; justify-content: space-between;">
                  <span class="title">查询</span>
                  <el-switch v-model="test_search_switch"
                    style="--el-switch-on-color: #409EFF; --el-switch-off-color: #409EFF" active-text="绘制查询"
                    inactive-text="范围值查询" />
                  <span>
                    <el-button type="primary" :icon="EditPen" />
                    <el-button type="primary"><svg t="1726831993817" class="icon" viewBox="0 0 1024 1024" version="1.1"
                        xmlns="http://www.w3.org/2000/svg" p-id="1708" width="15" height="15">
                        <path
                          d="M118.272 93.044364c2.792727-0.232727 5.678545 0 8.610909 0.698181l568.459636 137.216a27.461818 27.461818 0 0 1 20.48 21.317819l48.733091 243.712 2.978909-2.885819a27.461818 27.461818 0 0 1 38.81891 0l117.620363 117.620364a27.461818 27.461818 0 0 1 0 38.772364l-274.478545 274.478545a27.461818 27.461818 0 0 1-38.772364 0l-117.620364-117.620363a27.461818 27.461818 0 0 1 0-38.81891l2.885819-2.978909L252.276364 715.869091a27.461818 27.461818 0 0 1-19.874909-16.151273l-1.396364-4.328727L93.696 126.882909A27.648 27.648 0 0 1 93.090909 118.225455L93.090909 117.527273a22.202182 22.202182 0 0 1 0.558546-3.444364l0.372363-1.303273a21.317818 21.317818 0 0 1 0.930909-2.792727l0.651637-1.396364a25.460364 25.460364 0 0 1 1.908363-3.397818l0.279273-0.372363 0.698182-0.930909a27.927273 27.927273 0 0 1 10.053818-8.238546 22.574545 22.574545 0 0 1 4.189091-1.582545l1.349818-0.372364A21.922909 21.922909 0 0 1 117.480727 93.090909h0.605091z m668.672 458.24l-235.659636 235.659636 78.848 78.801455 235.613091-235.613091-78.801455-78.848zM208.756364 169.937455l211.595636 211.642181a105.844364 105.844364 0 1 1-38.772364 38.772364L169.937455 208.756364l110.312727 456.704 262.423273 52.456727 175.243636-175.243636-52.456727-262.469819-456.704-110.266181z m264.517818 252.369454a50.967273 50.967273 0 1 0 0 101.934546 50.967273 50.967273 0 0 0 0-101.934546z"
                          fill="#fff" p-id="1709"></path>
                      </svg></el-button> |
                    <el-select v-model="templatavalue" placeholder="模板" style="width: 80px">
                      <el-option v-for="item in templates" :key="item.value" :label="item.label" :value="item.value" />
                    </el-select>
                    •
                    <el-select v-model="historyvalue" placeholder="历史" style="width: 80px">
                      <el-option v-for="item in historys" :key="item.value" :label="item.label" :value="item.value" />
                    </el-select>
                  </span>
                </span>
                <span style="position: absolute; bottom: 8px; right: 8px;">
                  <el-button type="success" :icon="Search">查询</el-button>
                </span>
                <span style="position: absolute; bottom: 8px; left: 8px;">
                  <el-input v-model="time_begin" style="width: 70px; margin-right: 8px;" placeholder="起始 / s" />
                  <el-input v-model="time_during" style="width: 70px; margin-right: 8px;" placeholder="时长 / s" />
                  <el-input v-model="time_end" style="width: 70px" placeholder="终止 / s" />
                </span>
                <span style="position: absolute; bottom: 30%; left: 8px;">
                  <el-input v-model="time_begin" style="width: 70px; display: block; margin-bottom: 8px;"
                    placeholder="上界" />
                  <el-input v-model="time_during" style="width: 70px; display: block; margin-bottom: 8px;"
                    placeholder="幅度" />
                  <el-input v-model="time_end" style="width: 70px; display: block" placeholder="下界" />
                </span>
                <div style="display: flex; justify-content: center; align-items: center;" v-bind="$attrs">
                  <div v-if="test_search_switch === true">
                    <!-- 预留SearchSketch的使用问题 -->
                  </div>
                  <Sketch />
                </div>
              </el-card>
              <el-card class="two_right" shadow="never">
                <span style="display: flex; align-items: center; justify-content: space-between;">
                  <span class="title">自动识别和人工标注结果</span>
                  <el-switch v-model="test_result_switch"
                    style="--el-switch-on-color: #409EFF; --el-switch-off-color: #409EFF" active-text="热力图模式"
                    inactive-text="列表模式" />
                  <img src="/image2.png" style="height: 20px;" alt="图例">
                  <el-button type="primary">
                    导出<el-icon class="el-icon--right">
                      <Upload />
                    </el-icon>
                  </el-button>
                </span>
                <el-scrollbar height="24h" :always="true">
                  <div style="display: flex; justify-content: center; align-items: center;">
                    <div v-if="test_result_switch === true" style="width: 100%;">
                      <HeatMap />
                    </div>
                    <div v-if="test_result_switch === false" style="width: 100%;">
                      <ListResult />
                    </div>
                  </div>
                </el-scrollbar>
              </el-card>
            </div>
          </el-main>
          <el-main class="channel_main" v-if="selectedButton === 'channel'">
            <el-card class="operator">
              <span style="display: flex;">
                <span class="title">运算符列表</span>
                <span style="display: flex; justify-content: center; align-items: center; width: 85%;">
                  <el-button type="primary" plain size="large">加</el-button>
                  <el-button type="primary" plain size="large">减</el-button>
                  <el-button type="primary" plain size="large">乘</el-button>
                  <el-button type="primary" plain size="large">除</el-button>
                  <el-button type="primary" plain size="large">( )</el-button>
                  <el-button type="primary" plain size="large">傅里叶变换 FFT</el-button>
                  <el-button type="info" plain size="large">自定义算法</el-button>
                  <el-button type="success" plain size="large">算法导入</el-button>
                </span>
              </span>
            </el-card>
            <div class="two">
              <el-card class="two_left" shadow="never">
                <span style="display: flex; justify-content: space-between;">
                  <span class="title">待选择通道</span>
                  <span>统一采样率 <el-input-number v-model="unit_sampling" :precision="2" :step="0.1" :max="10" /></span>
                </span>
                <div style="display: flex; justify-content: center; align-items: center;">
                  <ChannelCards />
                </div>
              </el-card>
              <el-card class="two_right" shadow="never">
                <span class="title">通道分析公式</span>
                <div style="display: flex; justify-content: center; align-items: center; margin-top: 5px;">
                  <el-input v-model="formulasarea" style="width: 100%; height: 85%;" type="textarea"
                    :autosize="{ minRows: 2, maxRows: 9 }" placeholder="运算公式" />
                </div>
                <span style="position: absolute; bottom: 8px; right: 8px;">
                  <el-button type="primary" :icon="FolderChecked">记录公式</el-button>
                  <el-button type="primary" :icon="Cpu">计算</el-button>
                </span>
              </el-card>
            </div>
            <el-card class="data_exploration" shadow="never">
              <span style="display: flex; justify-content: space-between;">
                <span class="title">通道分析结果</span>
                <span>
                  <el-button type="primary" :icon="FolderChecked">另存为新通道</el-button>
                  <el-button type="primary" :icon="Upload">导出</el-button>
                </span>
              </span>
              <div style="display: flex; justify-content: center; align-items: center;">
                <ChannelCalculationResults />
              </div>
            </el-card>
          </el-main>
        </el-container>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useStore } from 'vuex';
import { Search, EditPen, FolderChecked, Cpu, Upload } from '@element-plus/icons-vue'
// 颜色配置及通道选取组件
import ChannelType from '@/components/Channel-Type.vue';
import ExceptionType from '@/components/Exception-Type.vue';
import ChannelTypeP from '@/components/Channel-Type-P.vue';


import MultiChannelSingleRow from '@/views/AnomalyLabelView/DataExploration/MultiChannelSingleRow.vue';
import SingleChannelMultiRow from '@/views/AnomalyLabelView/DataExploration/SingleChannelMultiRow.vue';

import HeatMap from '@/views/AnomalyLabelView/LabelResult/HeatMapResult.vue';
import ListResult from '@/views/AnomalyLabelView/LabelResult/ListResult.vue';

import Sketch from '@/views/AnomalyLabelView/Sketch/Sketch.vue';


import ChannelCards from '@/views/ChannelAnalysisView/ChannelList/ChannelCards.vue';
import ChannelCalculationResults from '@/views/ChannelAnalysisView/ChannelCalculation/ChannelCalculationResults.vue';

const store = useStore()
const sampling = ref(0.1)
const smoothness = ref(0)

// 获取 person 和 authority
const person = computed(() => store.state.person);
const authority = computed(() => store.state.authority);

// 根据 person 的第一个字符或汉字生成头像文本
const avatarText = computed(() => person.value ? person.value.charAt(0) : 'U');

// 权限标签
const authorityLabel = computed(() => authority.value === 0 ? '普通用户' : '管理员');

// 头像样式
const avatarStyle = computed(() => {
  const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399'];
  // 根据 authority 选择颜色
  const color = colors[authority.value % colors.length];
  return {
    backgroundColor: color,
    color: '#fff',
    cursor: 'pointer',
    border: '2px solid #fff',
    boxShadow: '0 2px 12px 0 rgba(0, 0, 0, 0.1)',
  };
});

// 退出方法
const logout = () => {
  console.log('用户已退出');
  // 在这里处理实际的退出逻辑，比如调用 store 的 logout action
};

// 实时更新 Vuex 状态的函数
const updateSampling = (value) => {
  store.dispatch('updateSampling', value)
}

const updateSmoothness = (value) => {
  store.dispatch('updateSmoothness', value)
}

const color_table_value = ref(true)
const test_channel_number = ref(true)
const test_result_switch = ref(true)
const test_search_switch = ref(true)
const unit_sampling = ref(0.1)
const selectedButton = ref('test');
const templatavalue = ref('')
const historyvalue = ref('')
const table_search = ref('')
const formulasarea = ref('')

const time_begin = ref()
const time_during = ref()
const time_end = ref()

const historys = [
  {
    value: 'Option1',
    label: '历史1',
  },
  {
    value: 'Option2',
    label: '历史2',
  }
]

const templates = [
  {
    value: 'Option1',
    label: '模板1',
  },
  {
    value: 'Option2',
    label: '模板2',
  }
]

const selectButton = (button) => {
  selectedButton.value = button;
};
</script>


<style scoped lang="scss">
.title {
  color: #999;
}

.el-card {
  --el-card-padding: 8px;
}

.el-main {
  padding: 5px 5px 5px 0 !important;
}

.all-layout {
  width: 100vw;
  height: 100vh;
  background-color: #e2e2e2;
  overflow: hidden;
}

.header {
  display: flex;
  justify-content: end;
  align-items: center;
  background-color: #ffffff;
  width: 100vw;
  height: 5vh;
}

.user-dropdown {
  padding: 10px 0;
  min-width: 150px;
}

.user-info {
  flex-direction: column;
  padding: 10px 20px;
}

.user-info p {
  color: #303133;
  line-height: 1.5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.el-dropdown-menu {
  min-width: 150px;
}

.el-avatar {
  transition: all 0.2s;
}

.el-avatar:hover {
  transform: scale(1.1);
}

.aside {
  width: 18vw;
  background-color: #e9e9e9;
  height: 95vh;
  padding: 5px;
  box-sizing: border-box;
  display: flex;
}

.aside-content,
.main {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

.jump_switch {
  margin-bottom: 5px;
  display: flex;
  justify-content: center;
}

.test,
.channel {
  transition: all 0.2s;
}

.selected {
  font-weight: bold;
}

.table {
  flex-grow: 1;
  position: relative;

  .color_table_switch {
    position: absolute;
    right: 10px;
  }
}

.el-switch {
  height: auto !important;
}

.test_main {
  background-color: #e9e9e9;
  display: flex;
  flex-direction: column;
  justify-content: space-between;

  .data_exploration {
    height: 70%;
    margin-bottom: 5px;
  }

  .two {
    display: flex;
    flex-grow: 1;
    gap: 5px;
  }

  .two_left {
    flex: 1.2;
    position: relative;
  }

  .two_right {
    flex: 2;
    position: relative;
  }

}

.channel_main {
  background-color: #e9e9e9;
  display: flex;
  flex-direction: column;
  justify-content: space-between;

  .operator {
    margin-bottom: 5px;
  }

  .data_exploration {
    height: 65%;
  }

  .two {
    display: flex;
    flex-grow: 1;
    gap: 5px;
    margin-bottom: 5px;
  }

  .two_left {
    flex: 2;
    position: relative;
  }

  .two_right {
    flex: 1;
    position: relative;
  }
}
</style>
