// Roulette游戏前端逻辑
// 负责与后端Socket.IO通信，处理用户输入和显示输出

// 初始化Socket.IO连接
const socket = io();
var token = localStorage.getItem('session_token');

// 获取DOM元素
const inputField = document.getElementById('input');
const sendBtn = document.getElementById('sendBtn');
const outputElement = document.getElementById('output');
const statusElement = document.getElementById('status');

// 连接状态管理
socket.on('connect', () => {
    console.log('Socket连接成功');
    statusElement.textContent = '连接状态: 已连接';
    statusElement.className = 'status connected';
    outputElement.textContent = '已连接到服务器，可以开始测试...';
});

socket.on('disconnect', () => {
    console.log('Socket连接断开');
    statusElement.textContent = '连接状态: 已断开';
    statusElement.className = 'status disconnected';
    outputElement.textContent = '连接已断开，请刷新页面重新连接...';
});

// 发送消息函数
function sendMessage() {
    const inputValue = inputField.value.trim();
    
    if (!inputValue) {
        outputElement.textContent = '请输入内容后再发送！';
        return;
    }
    
    // 显示发送中状态
    outputElement.textContent = '发送中...';
    
    // 构造游戏事件数据
    const eventData = {
        token: token,
        event_name: 'test_input',
        event_data: {
            input: inputValue,
            timestamp: new Date().toISOString()
        }
    };
    
    console.log('发送游戏事件:', eventData);
    
    // 发送到后端
    socket.emit('game_event', eventData);
}

// 监听游戏事件结果
socket.on('game_event_result', (response) => {
    console.log('收到游戏事件结果:', response);
    
    if (response.ok) {
        outputElement.textContent = `✓ ${response.msg}\n\n` +
            `回显内容: ${response.echo}\n` +
            `时间戳: ${response.timestamp}`;
        inputField.value = '';
    } else {
        outputElement.textContent = `✗ 错误: ${response.msg}`;
    }
});

// 监听游戏状态更新
socket.on('game_state_updated', (data) => {
    console.log('游戏状态更新:', data);
});

// 按钮点击事件
sendBtn.addEventListener('click', sendMessage);

// 回车发送
inputField.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// 页面加载完成后自动聚焦输入框
window.addEventListener('load', () => {
    inputField.focus();
});
