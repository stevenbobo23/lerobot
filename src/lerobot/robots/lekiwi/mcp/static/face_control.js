// 人脸控制逻辑

let faceControlEnabled = false;
let faceMesh = null;
let faceCamera = null;
let lastFaceSentTime = 0;
const FACE_SEND_INTERVAL = 100; // 发送指令间隔 (ms)

// 阈值设置
const MOUTH_OPEN_THRESHOLD = 0.05; // 嘴巴张开阈值 (归一化后)

// 位置控制阈值
const CENTER_ZONE_WIDTH = 0.3; // 中间区域宽度 (0.35 - 0.65)

// 按键状态追踪
let lastFaceKey = null;

async function initFaceControl() {
    console.log("初始化人脸控制...");
    
    const videoElement = document.getElementById('gesture-video'); // 复用手势控制的video
    const canvasElement = document.getElementById('gesture-canvas'); // 复用手势控制的canvas
    const canvasCtx = canvasElement.getContext('2d');

    // 初始化拖拽 (如果还没初始化)
    const container = document.getElementById('gesture-preview-container');
    const handle = document.getElementById('gesture-drag-handle');
    if (container && handle && !container.onmousedown) {
        makeDraggable(container, handle);
    }

    if (!videoElement || !canvasElement) {
        console.error("未找到人脸控制所需的 video 或 canvas 元素");
        return;
    }

    // Chrome 兼容设置
    videoElement.setAttribute('autoplay', '');
    videoElement.setAttribute('playsinline', '');
    videoElement.setAttribute('muted', '');
    videoElement.autoplay = true;
    videoElement.playsInline = true;
    videoElement.muted = true;

    faceMesh = new FaceMesh({locateFile: (file) => {
        return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`;
    }});

    faceMesh.setOptions({
        maxNumFaces: 1,
        refineLandmarks: true,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
    });

    faceMesh.onResults((results) => {
        onFaceResults(results, canvasCtx, canvasElement);
    });

    // 使用 MediaPipe Camera Utils
    faceCamera = new Camera(videoElement, {
        onFrame: async () => {
            if (faceControlEnabled) {
                await faceMesh.send({image: videoElement});
            }
        },
        width: 320,
        height: 240
    });
}

async function toggleFaceControl() {
    // 如果手势控制开启中，先关闭它
    if (typeof gestureControlEnabled !== 'undefined' && gestureControlEnabled) {
        await toggleGestureControl();
    }

    faceControlEnabled = !faceControlEnabled;
    const btn = document.getElementById('face-control-btn');
    const previewContainer = document.getElementById('gesture-preview-container'); // 复用容器
    const previewTitle = previewContainer.querySelector('span'); // 修改标题
    const videoElement = document.getElementById('gesture-video');
    
    if (faceControlEnabled) {
        console.log("开启人脸控制");
        btn.classList.add('bg-tech-600', 'text-white', 'border-tech-500');
        btn.classList.remove('bg-gray-800', 'text-gray-400', 'border-gray-700');
        btn.innerHTML = '<span class="text-2xl">☺</span> <span>正在控制</span>';
        
        if (previewTitle) previewTitle.textContent = 'FACE CONTROL';

        // 显示预览窗口
        previewContainer.classList.remove('hidden');
        if (videoElement) {
            videoElement.classList.remove('hidden');
            videoElement.setAttribute('autoplay', '');
            videoElement.setAttribute('playsinline', '');
            videoElement.setAttribute('muted', '');
        }
        
        try {
            if (!faceCamera) {
                await initFaceControl();
            }
            
            await faceCamera.start();
            
            // 等待视频流
            await new Promise((resolve, reject) => {
                if (!videoElement) { resolve(); return; }
                const timeout = setTimeout(() => reject(new Error('摄像头启动超时')), 5000);
                
                const onLoadedMetadata = () => {
                    clearTimeout(timeout);
                    setTimeout(() => {
                        if (videoElement && videoElement.readyState >= 2) {
                            videoElement.classList.add('hidden'); // 隐藏原始视频，显示canvas
                        }
                    }, 300);
                    resolve();
                };
                
                if (videoElement.readyState >= 2) {
                    onLoadedMetadata();
                } else {
                    videoElement.addEventListener('loadedmetadata', onLoadedMetadata, { once: true });
                }
            });
            
            showNotification('人脸控制已开启 - 张嘴移动，头部位置控制方向', 'success');
        } catch (error) {
            console.error("启动人脸控制失败:", error);
            showNotification('启动失败: ' + error.message, 'error');
            faceControlEnabled = false;
            // 恢复按钮状态
            updateFaceButtonState(btn, false);
            previewContainer.classList.add('hidden');
        }
    } else {
        console.log("关闭人脸控制");
        if (faceCamera) {
            try {
                await faceCamera.stop();
            } catch (e) {
                console.error("停止人脸摄像头失败:", e);
            }
        }
        
        // 清除高亮
        if (lastFaceKey) {
            unhighlightButton(lastFaceKey);
            lastFaceKey = null;
        }
        
        updateFaceButtonState(btn, false);
        if (previewTitle) previewTitle.textContent = 'Live Input';
        previewContainer.classList.add('hidden');
        // 发送停止命令
        sendCommand('stop');
    }
}

function updateFaceButtonState(btn, isActive) {
    if (isActive) {
        btn.classList.add('bg-tech-600', 'text-white', 'border-tech-500');
        btn.classList.remove('bg-gray-800', 'text-gray-400', 'border-gray-700');
        btn.innerHTML = '<span class="text-2xl">☺</span> <span>正在控制</span>';
    } else {
        btn.classList.remove('bg-tech-600', 'text-white', 'border-tech-500');
        btn.classList.add('bg-gray-800', 'text-gray-400', 'border-gray-700');
        btn.innerHTML = '<span class="text-2xl">☺</span> <span>人脸控制</span>';
    }
}

function onFaceResults(results, canvasCtx, canvasElement) {
    if (!faceControlEnabled) return;

    // 绘制
    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);

    if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
        const landmarks = results.multiFaceLandmarks[0];
        
        // 绘制网格
        drawConnectors(canvasCtx, landmarks, FACEMESH_TESSELATION, {color: '#C0C0C070', lineWidth: 1});
        drawConnectors(canvasCtx, landmarks, FACEMESH_RIGHT_EYE, {color: '#FF3030', lineWidth: 2});
        drawConnectors(canvasCtx, landmarks, FACEMESH_LEFT_EYE, {color: '#30FF30', lineWidth: 2});
        drawConnectors(canvasCtx, landmarks, FACEMESH_FACE_OVAL, {color: '#E0E0E0', lineWidth: 2});
        drawConnectors(canvasCtx, landmarks, FACEMESH_LIPS, {color: '#E0E0E0', lineWidth: 2});

        processFaceControl(landmarks);
    }
    canvasCtx.restore();
}

function processFaceControl(landmarks) {
    const now = Date.now();
    if (now - lastFaceSentTime < FACE_SEND_INTERVAL) return;

    // 关键点索引
    // 1: 鼻尖
    // 13: 上嘴唇
    // 14: 下嘴唇
    // 10: 额头顶
    // 152: 下巴

    // 1. 检测嘴巴开合 (Enable Switch)
    const upperLip = landmarks[13];
    const lowerLip = landmarks[14];
    const forehead = landmarks[10];
    const chin = landmarks[152];
    
    const faceHeight = Math.sqrt(Math.pow(forehead.x - chin.x, 2) + Math.pow(forehead.y - chin.y, 2));
    const mouthOpenDist = Math.sqrt(Math.pow(upperLip.x - lowerLip.x, 2) + Math.pow(upperLip.y - lowerLip.y, 2));
    
    // 归一化嘴巴开度
    const mouthRatio = mouthOpenDist / faceHeight;
    
    // 按键映射
    const keyMap = {
        'forward': 'w', 'backward': 's', 'left': 'a', 'right': 'd',
        'rotate_left': 'q', 'rotate_right': 'e', 'stop': ' '
    };

    // 如果嘴巴没张开，停止
    if (mouthRatio < MOUTH_OPEN_THRESHOLD) {
        // 停止逻辑
        if (lastFaceKey && lastFaceKey !== ' ') {
             // 只有之前是在移动状态才发送停止
             sendCommand('stop', true); // Silent mode
             unhighlightButton(lastFaceKey);
             // 稍微高亮一下停止键
             highlightButton(' ');
             setTimeout(() => unhighlightButton(' '), 200);
             lastFaceKey = ' ';
             lastFaceSentTime = now;
        }
        return;
    }

    // 2. 位置控制 (Position Control)
    // 鼻尖位置 landmarks[1].x
    // 注意：canvas CSS 是镜像的 (transform: scaleX(-1))
    // MediaPipe 输出是原始坐标 (0在左, 1在右)
    // 视觉上:
    // - 屏幕左边 (Visual Left) = 原始数据右边 (x > 0.5)
    // - 屏幕右边 (Visual Right) = 原始数据左边 (x < 0.5)
    
    const noseX = landmarks[1].x;
    const centerMin = 0.5 - CENTER_ZONE_WIDTH / 2; // e.g., 0.35
    const centerMax = 0.5 + CENTER_ZONE_WIDTH / 2; // e.g., 0.65

    let command = 'stop';

    // 逻辑判断
    if (noseX < centerMin) {
        // 原始左边 -> 视觉右边 -> 向右旋转
        command = 'rotate_right';
    } else if (noseX > centerMax) {
        // 原始右边 -> 视觉左边 -> 向左旋转
        command = 'rotate_left';
    } else {
        // 中间 -> 向前移动
        command = 'forward';
    }

    // 发送命令
    if (command !== 'stop') {
        console.log(`Face Command: ${command} (Mouth: ${mouthRatio.toFixed(2)}, NoseX: ${noseX.toFixed(2)})`);
        
        sendCommand(command, true); // Silent mode to prevent spam
        lastFaceSentTime = now;
        
        // 高亮逻辑
        const currentKey = keyMap[command];
        if (currentKey !== lastFaceKey) {
            if (lastFaceKey) unhighlightButton(lastFaceKey);
            if (currentKey) highlightButton(currentKey);
            lastFaceKey = currentKey;
        }
    } else {
        // 应该不会走到这里，除非 command 被逻辑置为 stop
        if (lastFaceKey && lastFaceKey !== ' ') {
            sendCommand('stop', true);
            unhighlightButton(lastFaceKey);
            highlightButton(' ');
            setTimeout(() => unhighlightButton(' '), 200);
            lastFaceKey = ' ';
            lastFaceSentTime = now;
        }
    }
}
