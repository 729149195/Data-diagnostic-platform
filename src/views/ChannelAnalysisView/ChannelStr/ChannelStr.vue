<template>
    <div>
        <div
            class="editable-div"
            contenteditable="true"
            @input="onInput"
            @keydown="onKeyDown"
        ></div>
        <span style="position: absolute; bottom: 8px; right: 8px;">
            <el-button type="primary" :icon="FolderChecked">记录公式</el-button>
            <el-button type="primary" :icon="Cpu" @click="sendClickedChannelNames">计算</el-button>
            <el-button type="danger" :icon="CloseBold" @click="clearFormulas">清空</el-button>
        </span>
    </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';
import { useStore } from 'vuex';
import { FolderChecked, Cpu, CloseBold } from '@element-plus/icons-vue';
import axios from 'axios';


const store = useStore();

const formulasarea = ref('');

const selectedChannels = computed(() => store.state.selectedChannels);

const clickedChannelNames = computed({
    get: () => store.state.clickedChannelNames,
    set: (value) => store.commit('setClickedChannelNames', value),
});

const highlightChannels = (caretOffset = null) => {
    const content = formulasarea.value;
    const channelNames = selectedChannels.value.map((channel) => channel.channel_name);
    const colors = selectedChannels.value.reduce((acc, channel) => {
        acc[channel.channel_name] = channel.color;
        return acc;
    }, {});

    const tokens = tokenizeContent(content, channelNames);

    const highlightedContent = tokens
        .map((token) => {
            if (channelNames.includes(token)) {
                const color = colors[token] || '#409EFF';
                return `<span class="tag" style="background-color: ${color};">${token}</span>`;
            } else {
                return token.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            }
        })
        .join('');

    const editableDiv = document.querySelector('.editable-div');
    if (editableDiv) {
        const cursorPosition = content.length; // 将光标位置设置为内容长度，即末尾

        editableDiv.innerHTML = highlightedContent;

        // 恢复光标位置到文本末尾
        setCaretPosition(editableDiv, cursorPosition);
    }
};

const sendClickedChannelNames = async () => {
    try {
        const response = await axios.post('http://localhost:5000/api/operator-strs', {
            clickedChannelNames: clickedChannelNames.value
        });
        console.log('Response from backend:', response.data);
    } catch (error) {
        console.error('Error sending data to backend:', error);
    }
};

// 将内容按照 channel_name 进行分割
const tokenizeContent = (content, channelNames) => {
    const tokens = [];
    let index = 0;

    while (index < content.length) {
        let matched = false;

        // 尝试匹配最长的 channel_name
        for (const name of channelNames.sort((a, b) => b.length - a.length)) {
            if (content.substr(index, name.length) === name) {
                tokens.push(name);
                index += name.length;
                matched = true;
                break;
            }
        }

        // 如果没有匹配到 channel_name，则按字符添加
        if (!matched) {
            tokens.push(content[index]);
            index++;
        }
    }

    return tokens;
};

// 获取光标在元素中的位置
const getCaretCharacterOffsetWithin = (element) => {
    let caretOffset = 0;
    const selection = window.getSelection();
    if (selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        const preCaretRange = range.cloneRange();
        preCaretRange.selectNodeContents(element);
        preCaretRange.setEnd(range.endContainer, range.endOffset);
        caretOffset = preCaretRange.toString().length;
    }
    return caretOffset;
};

// 设置光标位置
const setCaretPosition = (element, offset) => {
    const range = document.createRange();
    const selection = window.getSelection();

    let charCount = 0;
    let nodeStack = [element];
    let node, foundStart = false;

    while ((node = nodeStack.pop())) {
        if (node.nodeType === 3) {
            const nextCharCount = charCount + node.textContent.length;

            if (!foundStart && offset >= charCount && offset <= nextCharCount) {
                range.setStart(node, offset - charCount);
                foundStart = true;
                break;
            }

            charCount = nextCharCount;
        } else {
            let i = node.childNodes.length;
            while (i--) {
                nodeStack.push(node.childNodes[i]);
            }
        }
    }

    if (!foundStart) {
        range.setStart(element, element.childNodes.length);
    }

    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
};

// 监听 clickedChannelNames 的变化并更新显示内容
watch(
    clickedChannelNames,
    async (newVal, oldVal) => {
        // 检查是插入还是删除
        const diff = newVal.length - oldVal.length;
        if (diff !== 0) {
            // 有新增或删除字符，更新 formulasarea
            formulasarea.value = newVal;
            await nextTick();
            // 计算新的光标位置
            const editableDiv = document.querySelector('.editable-div');
            const selection = window.getSelection();
            let cursorPosition = getCaretCharacterOffsetWithin(editableDiv);

            // 如果是插入操作，移动光标到新插入文本的末尾
            if (diff > 0) {
                cursorPosition = cursorPosition + diff;
            }

            highlightChannels(cursorPosition);
        }
    },
    { immediate: true }
);

// 监听输入框变化
const onInput = (event) => {
    const textContent = getPlainText(event.target);
    formulasarea.value = textContent;
    clickedChannelNames.value = formulasarea.value;
    highlightChannels();
};

// 获取纯文本内容
const getPlainText = (element) => {
    let text = '';
    element.childNodes.forEach((node) => {
        if (node.nodeType === Node.TEXT_NODE) {
            text += node.textContent;
        } else if (node.nodeType === Node.ELEMENT_NODE && node.classList.contains('tag')) {
            text += node.textContent;
        } else {
            text += node.innerText;
        }
    });
    return text;
};

// 清空 formulasarea 和 clickedChannelNames
const clearFormulas = () => {
    formulasarea.value = '';
    clickedChannelNames.value = '';
    const editableDiv = document.querySelector('.editable-div');
    if (editableDiv) {
        editableDiv.innerHTML = '';
    }
};

// 处理键盘事件，防止用户删除部分高亮内容
const onKeyDown = (event) => {
    const selection = window.getSelection();
    const anchorNode = selection.anchorNode;

    if (event.key === 'Backspace' || event.key === 'Delete') {
        if (anchorNode && anchorNode.parentNode && anchorNode.parentNode.classList.contains('tag')) {
            event.preventDefault();
            const parent = anchorNode.parentNode;
            const offset = getCaretCharacterOffsetWithin(parent);

            // 删除整个高亮的节点
            parent.remove();

            // 更新内容
            onInput({ target: document.querySelector('.editable-div') });

            // 将光标设置到被删除的 tag 开始位置
            const editableDiv = document.querySelector('.editable-div');
            setCaretPosition(editableDiv, offset);
        }
    }
};

// 添加字符到光标位置
const insertAtCursor = (text) => {
    const editableDiv = document.querySelector('.editable-div');
    const selection = window.getSelection();
    const range = selection.getRangeAt(0);

    // 获取光标在纯文本中的位置
    const cursorPosition = getCaretCharacterOffsetWithin(editableDiv);

    // 创建文本节点
    const textNode = document.createTextNode(text);

    // 插入文本节点
    range.deleteContents();
    range.insertNode(textNode);

    // 更新 formulasarea 和 clickedChannelNames
    formulasarea.value = getPlainText(editableDiv);
    clickedChannelNames.value = formulasarea.value;

    // 高亮更新，传递新的光标位置（插入文本后的位置）
    const newCursorPosition = cursorPosition + text.length;
    highlightChannels(newCursorPosition);
};

// 处理卡片点击和按钮点击事件
const appendToClickedChannelNames = (content) => {
    insertAtCursor(content);
};
</script>

<style scoped lang="scss">
.editable-div {
    width: 100%;
    min-height: 85%;
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    padding: 10px;
    overflow: auto;
    line-height: 1.5;
    cursor: text;
    outline: none; /* 去除默认focus时的外边框 */
}

.editable-div:focus {
    border: 1px solid #dcdfe6; /* 保持原样或更改为您想要的颜色 */
    box-shadow: none; /* 移除默认阴影效果 */
}

.editable-div:empty::before {
    content: attr(placeholder);
    color: #c0c4cc;
}

:deep(.tag) {
    display: inline-block;
    padding: 0 8px;
    font-size: 12px;
    border-radius: 4px;
    color: #fff;
    background-color: #409EFF;
    margin: 0 2px;
    vertical-align: middle;
    overflow: hidden;
    white-space: nowrap;
}

</style>
