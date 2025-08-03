// 键盘控制
const keys = {
    'w': 'forward',
    's': 'backward', 
    'a': 'left',
    'd': 'right',
    'h': 'rotate_left',
    'j': 'rotate_right',
    'r': 'speed_up',
    'f': 'speed_down',
    ' ': 'stop'
};

const pressedKeys = new Set();
let activeButtons = new Set();
let isConnected = false;

// 连接模态框控制
function showConnectionModal() {
    document.getElementById('connectionModal').classList.remove('hidden');
}

function closeConnectionModal() {
    document.getElementById('connectionModal').classList.add('hidden');
}

// 连接机器人
async function connectRobot() {
    const remoteIp = document.getElementById('remoteIp').value;
    const armPort = document.getElementById('armPort').value;
    const calibrateArm = document.getElementById('calibrateArm').checked;
    
    // 更新状态为连接中
    updateStatusIndicators('connecting');
    
    try {
        const response = await fetch('/connect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                remote_ip: remoteIp,
                arm_port: armPort,
                calibrate_arm: calibrateArm
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            isConnected = true;
            closeConnectionModal();
            document.getElementById('disconnectBtn').classList.remove('hidden');
            updateStatusIndicators('connected');
            
            // 显示连接成功消息
            if (calibrateArm) {
                alert('连接成功！机械臂校准已完成。');
            } else {
                alert('连接成功！机器人已连接，机械臂状态请查看状态栏。');
            }
        } else {
            updateStatusIndicators('disconnected');
            alert('连接失败，请检查参数或尝试勾选校准选项');
        }
    } catch (error) {
        console.error('连接错误:', error);
        updateStatusIndicators('disconnected');
        alert('连接错误: ' + error.message);
    }
}

// 断开连接
async function disconnectRobot() {
    try {
        const response = await fetch('/disconnect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            isConnected = false;
            document.getElementById('disconnectBtn').classList.add('hidden');
            updateStatusIndicators('disconnected');
            pressedKeys.clear();
            activeButtons.forEach(id => {
                document.getElementById(id)?.classList.remove('active');
            });
            activeButtons.clear();
        }
    } catch (error) {
        console.error('断开连接错误:', error);
    }
}

// 更新状态指示器
function updateStatusIndicators(status) {
    const robotStatus = document.getElementById('robot-status');
    const armStatus = document.getElementById('arm-status');
    
    const statusClasses = {
        'connected': 'status-connected',
        'disconnected': 'status-disconnected',
        'connecting': 'status-connecting'
    };
    
    const statusTexts = {
        'connected': '已连接',
        'disconnected': '未连接',
        'connecting': '连接中...'
    };
    
    robotStatus.className = `status-indicator px-3 py-2 rounded ${statusClasses[status]}`;
    armStatus.className = `status-indicator px-3 py-2 rounded ${statusClasses[status]}`;
    
    robotStatus.textContent = `机器人: ${statusTexts[status]}`;
    armStatus.textContent = `机械臂: ${statusTexts[status]}`;
}

// 键盘事件监听
document.addEventListener('keydown', (e) => {
    if (!isConnected) return;
    
    const key = e.key.toLowerCase();
    if (keys[key] && !pressedKeys.has(key)) {
        console.log('键盘按下:', key);
        pressedKeys.add(key);
        const buttonId = keys[key];
        document.getElementById(buttonId)?.classList.add('active');
        activeButtons.add(buttonId);
        sendAction();
    }
});

document.addEventListener('keyup', (e) => {
if (!isConnected) return;

const key = e.key.toLowerCase();
if (keys[key]) {
    console.log('键盘释放:', key);
    pressedKeys.delete(key);
    const buttonId = keys[key];
    document.getElementById(buttonId)?.classList.remove('active');
    activeButtons.delete(buttonId);

    // 检查是否还有方向键被按下
    const directionKeys = ['w', 'a', 's', 'd', 'h', 'j'];
    const stillPressed = Array.from(pressedKeys).some(k => directionKeys.includes(k));
    if (!stillPressed) {
        // 没有方向键被按下，发送stop
        fetch('/send_action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ keys: ['stop'] })
        }).catch(error => {
            console.error('发送停止动作错误:', error);
        });
    } else {
        sendAction();
    }
}
});

// 鼠标/触摸控制
function setupButtonControl(buttonId, key) {
    const button = document.getElementById(buttonId);
    if (!button) return;

    // 鼠标事件
    button.addEventListener('mousedown', () => {
        if (!isConnected) return;
        console.log('鼠标按下:', buttonId, key);
        pressedKeys.clear(); // 清除之前按下的键
        pressedKeys.add(key);
        // 移除所有按钮的active状态
        activeButtons.forEach(id => {
            document.getElementById(id)?.classList.remove('active');
        });
        activeButtons.clear();
        // 添加当前按钮的active状态
        button.classList.add('active');
        activeButtons.add(buttonId);
        sendAction();
    });

    const stopMovement = () => {
        if (!isConnected) return;
        console.log('停止运动');
        pressedKeys.clear();
        activeButtons.forEach(id => {
            document.getElementById(id)?.classList.remove('active');
        });
        activeButtons.clear();
        sendStopAction();
    };

    button.addEventListener('mouseup', stopMovement);
    button.addEventListener('mouseleave', stopMovement);

    // 触摸事件
    button.addEventListener('touchstart', (e) => {
        e.preventDefault();
        if (!isConnected) return;
        console.log('触摸开始:', buttonId, key);
        pressedKeys.clear(); // 清除之前按下的键
        pressedKeys.add(key);
        // 移除所有按钮的active状态
        activeButtons.forEach(id => {
            document.getElementById(id)?.classList.remove('active');
        });
        activeButtons.clear();
        // 添加当前按钮的active状态
        button.classList.add('active');
        activeButtons.add(buttonId);
        sendAction();
    });

    const stopTouchMovement = (e) => {
        e.preventDefault();
        if (!isConnected) return;
        console.log('触摸结束:', buttonId, key);
        pressedKeys.clear();
        activeButtons.forEach(id => {
            document.getElementById(id)?.classList.remove('active');
        });
        activeButtons.clear();
        sendStopAction();
    };

    button.addEventListener('touchend', stopTouchMovement);
    button.addEventListener('touchcancel', stopTouchMovement);
}

// 设置所有按钮控制
Object.entries(keys).forEach(([key, buttonId]) => {
    // 只为方向控制按钮设置按住运动的功能，排除速度控制和停止按钮
    if (['w', 's', 'a', 'd', 'h', 'j'].includes(key)) {
        setupButtonControl(buttonId, key);
    }
});

// 停止按钮 - 点击立即停止
document.getElementById('stop').addEventListener('click', () => {
    if (!isConnected) return;
    console.log('停止按钮被点击');
    pressedKeys.clear();
    activeButtons.forEach(id => {
        document.getElementById(id)?.classList.remove('active');
    });
    activeButtons.clear();
    sendStopAction();
});

// 发送停止动作到服务器
async function sendStopAction() {
    console.log('发送停止动作');
    try {
        await fetch('/send_action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ keys: ['stop'] })
        });
    } catch (error) {
        console.error('发送停止动作错误:', error);
    }
}

// 发送动作到服务器
async function sendAction() {
    if (!isConnected) return;
    
    // 将按键名称转换为动作名称
    const actionKeys = Array.from(pressedKeys).map(key => keys[key] || key);
    
    const action = {
        keys: actionKeys
    };
    
    // 只有当有按键时才发送动作
    if (action.keys.length > 0) {
        console.log('发送动作:', action.keys);
        try {
            await fetch('/send_action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(action)
            });
        } catch (error) {
            console.error('发送动作错误:', error);
        }
    }
}

// 更新状态显示
async function updateStatus() {
    try {
        const response = await fetch('/get_status');
        const data = await response.json();
        
        const speedDisplay = document.getElementById('speed-display');
        const xVel = document.getElementById('x-vel');
        const yVel = document.getElementById('y-vel');
        const thetaVel = document.getElementById('theta-vel');
        
        if (speedDisplay) speedDisplay.textContent = data.speed_level;
        if (xVel) xVel.textContent = data.x_vel.toFixed(2) + ' m/s';
        if (yVel) yVel.textContent = data.y_vel.toFixed(2) + ' m/s';
        if (thetaVel) thetaVel.textContent = data.theta_vel.toFixed(2) + ' deg/s';
        
        // 更新连接状态
        const wasConnected = isConnected;
        if (data.robot_connected && data.arm_connected) {
            if (!isConnected) {
                isConnected = true;
                const disconnectBtn = document.getElementById('disconnectBtn');
                if (disconnectBtn) disconnectBtn.classList.remove('hidden');
                updateStatusIndicators('connected');
                console.log('连接状态: 已连接');
            }
        } else {
            if (isConnected) {
                isConnected = false;
                const disconnectBtn = document.getElementById('disconnectBtn');
                if (disconnectBtn) disconnectBtn.classList.add('hidden');
                updateStatusIndicators('disconnected');
                console.log('连接状态: 已断开');
            }
        }
    } catch (error) {
        console.error('获取状态错误:', error);
    }
}

// 表单提交处理
document.getElementById('connectionForm').addEventListener('submit', (e) => {
    e.preventDefault();
    connectRobot();
});

// 定期更新状态
setInterval(updateStatus, 1000);

// 初始化
updateStatus();

// 显示连接模态框
showConnectionModal();

// 调试信息
console.log('页面初始化完成');
console.log('当前按键状态:', pressedKeys);
console.log('当前连接状态:', isConnected);