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

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    updateStatus();
    console.log('LeKiwi HTTP Controller 已加载');
    console.log('键盘控制: W(前进) S(后退) A(左转) D(右转) Q(左旋转) E(右旋转) 空格(停止)');
});