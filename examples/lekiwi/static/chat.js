// 音频通话功能
const chat = {
    // DOM元素
    els: {
        deviceList: null,
        togglePlay: null,
        toggleCall: null,
        remoteAudio: null,
        debugInfo: null,
        micWarning: null,
        callPanel: null
    },
    
    // 配置和状态
    config: {
        sampleRate: 48000,
        channels: 1,
        audioBufferSize: 2
    },
    
    state: {
        socket: null,
        selectedDevice: null,
        audioContext: null,
        localStream: null,
        isPlaying: false,
        isRecording: false,
        micPermissionGranted: false,
        audioBufferQueue: [],
        gainNode: null,
        isAudioPlaying: false,
        counters: {
            send: 0,
            receive: 0,
            play: 0
        }
    },
    
    // 初始化
    init() {
        // 初始化WebSocket连接
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname;
        // const port = window.location.port ? `:${window.location.port}` : '';
        const port =  ':7777';

        const wsUrl = `${protocol}//${host}${port}`;
        
        this.state.socket = new WebSocket(wsUrl, ['binary']);
        
        // 绑定DOM元素
        this.els.deviceList = document.getElementById('deviceList');
        this.els.togglePlay = document.getElementById('togglePlay');
        this.els.toggleCall = document.getElementById('toggleCall');
        this.els.remoteAudio = document.getElementById('remoteAudio');
        this.els.debugInfo = document.getElementById('debugInfo');
        this.els.micWarning = document.getElementById('micPermissionWarning');
        
        // 设置事件监听器
        this.setupEventListeners();
        
        // 请求麦克风权限
        this.permissions.requestMicrophone();
        
        this.utils.log('音频通话模块初始化完成');
    },
    
    // 设置事件监听器
    setupEventListeners() {
        // WebSocket事件处理
        this.state.socket.onopen = () => this.utils.log('连接到音频服务器');
        this.state.socket.onerror = () => this.utils.log('WebSocket连接错误');
        this.state.socket.onclose = (event) => this.utils.log('WebSocket连接关闭: ' + event.code);
        
        this.state.socket.onmessage = (event) => {
            try {
                if (typeof event.data === 'string') {
                    const data = JSON.parse(event.data);
                    if (data.type === 'deviceList') {
                        this.utils.log('更新设备列表');
                        this.devices.update(data.devices);
                    }
                } else if (event.data instanceof ArrayBuffer || event.data instanceof Blob) {
                    if (event.data instanceof Blob) {
                        const reader = new FileReader();
                        reader.onload = () => {
                            this.audio.processData(reader.result);
                        };
                        reader.readAsArrayBuffer(event.data);
                    } else {
                        this.audio.processData(event.data);
                    }
                }
            } catch (error) {
                this.utils.log('消息处理失败: ' + error.message);
            }
        };
        
        // 按钮事件
        if (this.els.togglePlay) {
            this.els.togglePlay.onclick = () => this.play.toggle();
        }
        if (this.els.toggleCall) {
            this.els.toggleCall.onclick = () => this.record.toggle();
        }
        
        // 页面卸载时停止播放和录制
        window.addEventListener('beforeunload', () => {
            if (this.state.isPlaying) {
                this.play.stop();
            }
            if (this.state.isRecording) {
                this.record.stop();
            }
        });
    },
    
    // 工具函数
    utils: {
        log(message) {
            if (!chat.els.debugInfo) return;
            
            const time = new Date().toLocaleTimeString();
            chat.els.debugInfo.innerHTML += `<div class="mb-1"><span class="text-yellow-400">${time}</span>: ${message}</div>`;
            chat.els.debugInfo.scrollTop = chat.els.debugInfo.scrollHeight;
            console.log('[Chat] ' + message);
        },
        
        // 初始化或获取音频上下文
        getAudioContext() {
            if (!chat.state.audioContext) {
                chat.state.audioContext = new (window.AudioContext || window.webkitAudioContext)({sampleRate: chat.config.sampleRate});
                chat.utils.log('音频上下文已初始化');
            }
            return chat.state.audioContext;
        },
        
        // 确保音频上下文处于运行状态
        async ensureAudioContextRunning() {
            const ctx = chat.utils.getAudioContext();
            if (ctx.state === 'suspended') {
                try {
                    await ctx.resume();
                    chat.utils.log('音频上下文已恢复');
                } catch (err) {
                    chat.utils.log('音频上下文恢复失败: ' + err);
                }
            }
            return ctx;
        },
        
        // 获取增益节点
        getGainNode() {
            if (!chat.state.gainNode && chat.state.audioContext) {
                chat.state.gainNode = chat.state.audioContext.createGain();
                chat.state.gainNode.gain.value = 1.5;
                chat.state.gainNode.connect(chat.state.audioContext.destination);
            }
            return chat.state.gainNode;
        },
        
        // 发送WebSocket消息
        sendMessage(data) {
            if (chat.state.socket && chat.state.socket.readyState === WebSocket.OPEN) {
                chat.state.socket.send(data);
                return true;
            }
            return false;
        }
    },
    
    // 音频处理
    audio: {
        // 处理接收到的音频数据
        processData(arrayBuffer) {
            chat.state.counters.receive++;
            if (chat.state.counters.receive % 100 === 0) {
                chat.utils.log('处理音频数据，总计: ' + chat.state.counters.receive);
            }
            
            chat.utils.ensureAudioContextRunning().then(() => {
                chat.audio.playBuffer(arrayBuffer);
            });
        },
        
        // 播放音频数据
        playBuffer(data) {
            chat.state.counters.play++;
            
            try {
                const audioData = new Int16Array(data);
                chat.state.audioBufferQueue.push(audioData);
                
                if (chat.state.audioBufferQueue.length >= chat.config.audioBufferSize || 
                    (!chat.state.isAudioPlaying && chat.state.audioBufferQueue.length > 0)) {
                    chat.audio.processQueue();
                }
            } catch (e) {
                console.error('处理音频数据时发生错误:', e);
            }
        },
        
        // 处理音频队列
        processQueue() {
            if (chat.state.audioBufferQueue.length === 0) return;
            
            chat.state.isAudioPlaying = true;
            
            try {
                // 合并缓冲区
                const maxBuffers = Math.min(chat.state.audioBufferQueue.length, 3);
                let totalLength = 0;
                
                for (let i = 0; i < maxBuffers; i++) {
                    totalLength += chat.state.audioBufferQueue[i].length;
                }
                
                const mergedData = new Int16Array(totalLength);
                let offset = 0;
                
                for (let i = 0; i < maxBuffers; i++) {
                    const buffer = chat.state.audioBufferQueue.shift();
                    mergedData.set(buffer, offset);
                    offset += buffer.length;
                }
                
                // 创建音频缓冲区
                const audioBuffer = chat.state.audioContext.createBuffer(1, mergedData.length, chat.config.sampleRate);
                const channelData = audioBuffer.getChannelData(0);
                
                // 转换数据
                for (let i = 0; i < mergedData.length; i++) {
                    channelData[i] = Math.max(-1, Math.min(1, mergedData[i] / 32768));
                }
                
                // 播放
                const source = chat.state.audioContext.createBufferSource();
                source.buffer = audioBuffer;
                source.connect(chat.utils.getGainNode());
                
                source.onended = () => {
                    chat.state.isAudioPlaying = false;
                    if (chat.state.audioBufferQueue.length > 0) {
                        requestAnimationFrame(() => chat.audio.processQueue());
                    }
                };
                
                source.start();
            } catch (e) {
                console.error('播放音频时发生错误:', e);
                chat.state.isAudioPlaying = false;
                
                if (chat.state.audioBufferQueue.length > 0) {
                    requestAnimationFrame(() => chat.audio.processQueue());
                }
            }
        }
    },
    
    // 设备管理
    devices: {
        update(deviceList) {
            if (!chat.els.deviceList) return;
            
            chat.els.deviceList.innerHTML = '';
            
            if (deviceList.length === 0) {
                chat.els.deviceList.innerHTML = '<div class="text-center py-2 text-gray-500 text-xs">暂无可用设备</div>';
                return;
            }
            
            deviceList.forEach((device, index) => {
                // 处理设备可能是对象的情况
                const deviceId = typeof device === 'object' && device !== null ? device.id : device;
                const isActive = typeof device === 'object' && device !== null ? device.active : false;
                
                const li = document.createElement('li');
                li.className = 'p-1 hover:bg-gray-100 cursor-pointer transition duration-150 device-item text-xs';
                li.textContent = deviceId + (isActive ? ' (通话中)' : '');
                li.onclick = () => chat.devices.select(deviceId, li);
                chat.els.deviceList.appendChild(li);
                
                // 自动选择最新出现的设备（第一个设备）
                if (index === 0 && !chat.state.selectedDevice) {
                    chat.devices.select(deviceId, li);
                }
            });
        },
        
        select(deviceId, element) {
            chat.state.selectedDevice = deviceId;
            
            document.querySelectorAll('.device-item').forEach(item => {
                item.classList.remove('bg-blue-100', 'font-bold');
            });
            
            element.classList.add('bg-blue-100', 'font-bold');
            
            if (chat.els.togglePlay) {
                chat.els.togglePlay.disabled = false;
            }
            if (chat.els.toggleCall) {
                chat.els.toggleCall.disabled = false;
            }
            
            chat.utils.log('已选择设备: ' + deviceId);
        }
    },
    
    // 播放控制
    play: {
        start() {
            if (!chat.state.selectedDevice) {
                chat.utils.log('未选择设备');
                return;
            }
            
            chat.utils.sendMessage(JSON.stringify({
                type: 'startlistening',
                targetDevice: chat.state.selectedDevice
            }));
            
            chat.state.isPlaying = true;
            if (chat.els.togglePlay) {
                chat.els.togglePlay.textContent = '停止播放';
                chat.els.togglePlay.classList.remove('bg-blue-500', 'hover:bg-blue-600');
                chat.els.togglePlay.classList.add('bg-red-500', 'hover:bg-red-600');
            }
            chat.utils.log('开始播放Pi的声音');
        },
        
        stop() {
            chat.utils.sendMessage(JSON.stringify({
                type: 'stoplistening',
                targetDevice: chat.state.selectedDevice
            }));
            
            chat.state.isPlaying = false;
            if (chat.els.togglePlay) {
                chat.els.togglePlay.textContent = '播放声音';
                chat.els.togglePlay.classList.remove('bg-red-500', 'hover:bg-red-600');
                chat.els.togglePlay.classList.add('bg-blue-500', 'hover:bg-blue-600');
            }
            
            // 清空音频缓冲区
            chat.state.audioBufferQueue = [];
            chat.state.isAudioPlaying = false;
            
            // 清理播放相关的资源
            if (chat.state.gainNode) {
                try {
                    chat.state.gainNode.disconnect();
                    chat.state.gainNode = null;
                } catch (err) {
                    console.error('断开增益节点失败: ' + err);
                }
            }
            
            chat.utils.log('停止播放Pi的声音');
        },
        
        toggle() {
            if (chat.state.isPlaying) {
                this.stop();
            } else {
                this.start();
            }
        }
    },
    
    // 录制控制
    record: {
        async start() {
            if (!chat.state.selectedDevice) {
                chat.utils.log('未选择设备');
                return;
            }
            
            if (!chat.state.micPermissionGranted) {
                chat.utils.log('麦克风权限未授予，没有授予麦克风权限');
                await chat.permissions.requestMicrophone();
                
                if (!chat.state.micPermissionGranted) {
                    chat.utils.log('重新获取麦克风权限失败');
                    alert('无法获取麦克风权限，请检查浏览器设置并刷新页面重试');
                    return;
                }
            }
            
            try {
                chat.utils.log('初始化音频通话');
                
                if (!chat.utils.sendMessage(JSON.stringify({
                    type: 'startCall',
                    targetDevice: chat.state.selectedDevice
                }))) {
                    chat.utils.log('WebSocket未连接，无法发送开始录音消息');
                    return;
                }
                
                // 获取麦克风流
                chat.state.localStream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        sampleRate: chat.config.sampleRate,
                        autoGainControl: false
                    }, 
                    video: false 
                });
                
                await chat.utils.ensureAudioContextRunning();
                
                // 重置计数器
                chat.state.counters.send = 0;
                chat.state.counters.receive = 0;
                
                // 创建音频处理节点，使用更大的缓冲区以降低发送频率
                const source = chat.state.audioContext.createMediaStreamSource(chat.state.localStream);
                const processor = chat.state.audioContext.createScriptProcessor(4096, 1, 1);
                
                processor.onaudioprocess = function(e) {
                    if (!chat.state.isRecording) return;
                    
                    const inputData = e.inputBuffer.getChannelData(0);
                    const pcmData = new Int16Array(inputData.length);
                    
                    for (let i = 0; i < inputData.length; i++) {
                        const s = Math.max(-1, Math.min(1, inputData[i]));
                        pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                    }
                    
                    if (chat.utils.sendMessage(pcmData.buffer)) {
                        chat.state.counters.send++;
                        if (chat.state.counters.send % 10 === 0) {  // 更频繁地显示日志
                            chat.utils.log('音频发送统计 - 总计发送: ' + chat.state.counters.send + ' 个包');
                        }
                    }
                };
                
                source.connect(processor);
                processor.connect(chat.state.audioContext.destination);
                
                chat.state.isRecording = true;
                if (chat.els.toggleCall) {
                    chat.els.toggleCall.textContent = '结束通话';
                    chat.els.toggleCall.classList.remove('bg-green-500', 'hover:bg-green-600');
                    chat.els.toggleCall.classList.add('bg-red-500', 'hover:bg-red-600');
                }
                
                chat.utils.log('开始录制并发送给设备: ' + chat.state.selectedDevice);
            } catch (error) {
                chat.utils.log('初始化音频录制失败: ' + error.message);
                
                let errorMessage = '无法开始录制，请检查以下事项：\n\n';
                if (error.name === 'NotAllowedError') {
                    errorMessage += '1. 您拒绝了麦克风访问权限，请刷新页面并允许访问\n';
                } else if (error.name === 'NotFoundError') {
                    errorMessage += '1. 未检测到可用的麦克风设备\n';
                } else if (error.name === 'SecurityError') {
                    errorMessage += '1. 当前页面不支持麦克风访问（可能需要HTTPS）\n';
                } else {
                    errorMessage += '1. 请检查麦克风是否被其他应用占用\n';
                    errorMessage += '2. 检查浏览器设置中的麦克风权限\n';
                }
                
                alert(errorMessage);
            }
        },
        
        stop() {
            // 停止本地音频流
            if (chat.state.localStream) {
                chat.state.localStream.getTracks().forEach(track => track.stop());
                chat.state.localStream = null;
                chat.utils.log('本地音频流已停止');
            }
            
            // 只重置与通话相关的状态和按钮
            chat.state.isRecording = false;
            if (chat.els.toggleCall) {
                chat.els.toggleCall.textContent = '点击通话';
                chat.els.toggleCall.classList.remove('bg-red-500', 'hover:bg-red-600');
                chat.els.toggleCall.classList.add('bg-green-500', 'hover:bg-green-600');
            }
            chat.utils.log('停止通话');
            
            // 发送停止通话消息
            chat.utils.sendMessage(JSON.stringify({
                type: 'stopCall'
            }));
            
            // 清空音频缓冲区
            chat.state.audioBufferQueue = [];
            chat.state.counters.send = 0;
            chat.state.counters.receive = 0;
            chat.state.isAudioPlaying = false;
            
            // 清理通话相关的音频资源
            // 只有在没有播放功能在使用时才关闭音频上下文
            if (!chat.state.isPlaying && chat.state.audioContext) {
                chat.state.audioContext.close().then(() => {
                    chat.state.audioContext = null;
                    chat.state.gainNode = null;
                    chat.utils.log('音频上下文已关闭并重置');
                }).catch(err => {
                    chat.utils.log('关闭音频上下文失败: ' + err);
                });
            }
            
            chat.utils.log('停止通话');
        },
        
        toggle() {
            if (chat.state.isRecording) {
                this.stop();
            } else {
                this.start();
            }
        }
    },
    
    // 权限管理
    permissions: {
        async requestMicrophone() {
            try {
                chat.utils.log('检查浏览器支持情况');
                if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                    throw new Error('浏览器不支持getUserMedia API');
                }
                
                chat.utils.log('请求麦克风权限');
                chat.state.localStream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        sampleRate: chat.config.sampleRate,
                        autoGainControl: true
                    }, 
                    video: false 
                });
                
                chat.state.micPermissionGranted = true;
                chat.utils.log('麦克风权限已获取');
                
                // 立即停止轨道以避免持续录制
                chat.state.localStream.getTracks().forEach(track => track.stop());
                chat.state.localStream = null;
                
                // 隐藏警告信息
                if (chat.els.micWarning) {
                    chat.els.micWarning.classList.add('hidden');
                }
            } catch (error) {
                chat.utils.log('获取麦克风权限失败: ' + error.message);
                if (chat.els.micWarning) {
                    chat.els.micWarning.classList.remove('hidden');
                }
            }
        }
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    chat.init();
});