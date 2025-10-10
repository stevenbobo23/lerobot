function updateStatus() {
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            const statusDiv = document.getElementById('status');
            if (data.connected) {
                statusDiv.textContent = '状态: 已连接 - 可以控制';
                statusDiv.className = 'status connected';
            } else {
                statusDiv.textContent = '状态: 未连接 - 需要重启服务';
                statusDiv.className = 'status disconnected';
            }
        })
        .catch(error => {
            console.error('获取状态失败:', error);
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = '状态: 连接错误 - 需要重启服务';
            statusDiv.className = 'status disconnected';
        });
}

function sendCommand(command) {
    const durationInput = document.getElementById('durationInput');
    const duration = parseFloat(durationInput.value) || 0;
    
    const requestBody = {command: command};
    if (duration > 0) {
        requestBody.duration = duration;
    }
    
    fetch('/control', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
    })
    .then(response => response.json())
    .then(data => {
        console.log('命令执行结果:', data);
        if (data.success) {
            if (duration > 0) {
                console.log(`机器人将${command}移动${duration}秒`);
                showNotification(`机器人${command}移动${duration}秒`, 'success');
            } else {
                showNotification(`机器人开始${command}`, 'success');
            }
        } else {
            alert('命令执行失败: ' + data.message);
            showNotification('命令执行失败: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('发送命令失败:', error);
        alert('发送命令失败: ' + error.message);
        showNotification('发送命令失败: ' + error.message, 'error');
    });
}

function showNotification(message, type) {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // 设置样式
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 10px 20px;
        border-radius: 5px;
        color: white;
        font-weight: bold;
        z-index: 1000;
        transition: all 0.3s ease;
        ${type === 'success' ? 'background-color: #28a745;' : 'background-color: #dc3545;'}
    `;
    
    document.body.appendChild(notification);
    
    // 3秒后自动移除
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// 键盘控制支持
document.addEventListener('keydown', (e) => {
    const key = e.key.toLowerCase();
    const keyMap = {
        'w': 'forward',
        's': 'backward',
        'a': 'left',
        'd': 'right',
        'q': 'rotate_left',
        'e': 'rotate_right',
        ' ': 'stop'
    };
    
    if (keyMap[key]) {
        e.preventDefault();
        sendCommand(keyMap[key]);
    }
});

// 防止空格键滚动页面
document.addEventListener('keydown', (e) => {
    if (e.key === ' ') {
        e.preventDefault();
    }
});

// 定期更新状态
setInterval(updateStatus, 1000);

// 机械臂当前位置
let currentArmPosition = {
    'arm_shoulder_pan.pos': 0,
    'arm_shoulder_lift.pos': 0,
    'arm_elbow_flex.pos': 0,
    'arm_wrist_flex.pos': 0,
    'arm_wrist_roll.pos': 0,
    'arm_gripper.pos': 0
};

// 发送机械臂位置命令
function sendArmPosition(positions) {
    fetch('/control', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(positions)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('机械臂位置已更新', 'success');
        } else {
            showNotification('机械臂控制失败: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('发送机械臂命令失败:', error);
        showNotification('发送机械臂命令失败: ' + error.message, 'error');
    });
}

// 更新滑块值显示
function updateSliderValue(sliderId, value) {
    const valueSpan = document.getElementById(sliderId + '-value');
    if (valueSpan) {
        valueSpan.textContent = value;
    }
}

// 复位机械臂到初始位置
function resetArmToHome() {
    const homePosition = {
        'arm_shoulder_pan.pos': 0,
        'arm_shoulder_lift.pos': 0,
        'arm_elbow_flex.pos': 0,
        'arm_wrist_flex.pos': 0,
        'arm_wrist_roll.pos': 0,
        'arm_gripper.pos': 0
    };
    
    // 更新滑块位置
    document.getElementById('shoulder-pan').value = 0;
    document.getElementById('shoulder-lift').value = 0;
    document.getElementById('elbow-flex').value = 0;
    document.getElementById('wrist-flex').value = 0;
    document.getElementById('wrist-roll').value = 0;
    document.getElementById('gripper').value = 0;
    
    // 更新显示值
    updateSliderValue('shoulder-pan', 0);
    updateSliderValue('shoulder-lift', 0);
    updateSliderValue('elbow-flex', 0);
    updateSliderValue('wrist-flex', 0);
    updateSliderValue('wrist-roll', 0);
    updateSliderValue('gripper', 0);
    
    // 发送命令
    sendArmPosition(homePosition);
    currentArmPosition = {...homePosition};
}

// 获取当前机械臂位置
function getCurrentArmPosition() {
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.current_action) {
                const action = data.current_action;
                
                // 更新滑块和显示值
                if (action['arm_shoulder_pan.pos'] !== undefined) {
                    const value = Math.round(action['arm_shoulder_pan.pos']);
                    document.getElementById('shoulder-pan').value = value;
                    updateSliderValue('shoulder-pan', value);
                }
                if (action['arm_shoulder_lift.pos'] !== undefined) {
                    const value = Math.round(action['arm_shoulder_lift.pos']);
                    document.getElementById('shoulder-lift').value = value;
                    updateSliderValue('shoulder-lift', value);
                }
                if (action['arm_elbow_flex.pos'] !== undefined) {
                    const value = Math.round(action['arm_elbow_flex.pos']);
                    document.getElementById('elbow-flex').value = value;
                    updateSliderValue('elbow-flex', value);
                }
                if (action['arm_wrist_flex.pos'] !== undefined) {
                    const value = Math.round(action['arm_wrist_flex.pos']);
                    document.getElementById('wrist-flex').value = value;
                    updateSliderValue('wrist-flex', value);
                }
                if (action['arm_wrist_roll.pos'] !== undefined) {
                    const value = Math.round(action['arm_wrist_roll.pos']);
                    document.getElementById('wrist-roll').value = value;
                    updateSliderValue('wrist-roll', value);
                }
                if (action['arm_gripper.pos'] !== undefined) {
                    const value = Math.round(action['arm_gripper.pos']);
                    document.getElementById('gripper').value = value;
                    updateSliderValue('gripper', value);
                }
                
                showNotification('已获取当前机械臂位置', 'success');
            } else {
                showNotification('获取机械臂位置失败', 'error');
            }
        })
        .catch(error => {
            console.error('获取机械臂位置失败:', error);
            showNotification('获取机械臂位置失败: ' + error.message, 'error');
        });
}

// 初始化机械臂滑块事件监听
function initArmSliders() {
    const sliders = document.querySelectorAll('.arm-slider');
    
    sliders.forEach(slider => {
        // 更新显示值
        slider.addEventListener('input', function() {
            const value = this.value;
            const sliderId = this.id;
            updateSliderValue(sliderId, value);
        });
        
        // 发送位置命令（当用户释放滑块时）
        slider.addEventListener('change', function() {
            const value = parseFloat(this.value);
            const joint = this.getAttribute('data-joint');
            
            if (joint) {
                const position = {};
                position[joint] = value;
                
                // 更新当前位置
                currentArmPosition[joint] = value;
                
                // 发送完整的机械臂位置（保持其他关节不变）
                sendArmPosition(currentArmPosition);
            }
        });
        
        // 初始化显示值
        updateSliderValue(slider.id, slider.value);
    });
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    updateStatus();
    initArmSliders();
    console.log('LeKiwi HTTP Controller 已加载');
    console.log('键盘控制: W(前进) S(后退) A(左转) D(右转) Q(左旋转) E(右旋转) 空格(停止)');
    console.log('机械臂控制: 使用滑块调节各关节位置');
});