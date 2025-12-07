#!/usr/bin/env python

import websocket
import json
import uuid
import pyaudio
import numpy as np
import threading
import time
import struct
import sys

# 配置部分
SERVER_URL = "ws://192.168.101.68:7777"  # 修改为实际服务器地址
DEVICE_ID = str(uuid.uuid4())[:8]

# 音频设备配置
INPUT_DEVICE_INDEX = 4   # T1 Webcam (card 1) 用于录音
OUTPUT_DEVICE_INDEX = 1  # 根据arecord -l输出，使用card 1设备

# 音频参数
SAMPLE_RATE = 48000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = 2048
BYTES_PER_SAMPLE = 2  # 16位音频

# 初始化音频播放
audio_playback = pyaudio.PyAudio()
playback_stream = None

# 状态变量
received_audio_counter = 0
sent_audio_counter = 0
is_recording = False  # 录音状态标志
is_in_call_mode = False  # 是否处于通话模式（只发送不播放）

def on_message(ws, message):
    global received_audio_counter, is_recording, is_in_call_mode
    
    # 处理文本消息（控制信号）
    if isinstance(message, str):
        try:
            data = json.loads(message)
            if data.get('type') == 'startlistening' :
                is_recording = True
                print(f"[INFO] 收到开始录音指令，开始录音 - {time.strftime('%H:%M:%S')}")
            elif data.get('type') == 'stoplistening' :
                is_recording = False
                print(f"[INFO] 收到停止录音指令，停止录音 - {time.strftime('%H:%M:%S')}")
            elif data.get('type') == 'startCall':
                is_in_call_mode = True  
                print("开始通话")
            elif data.get('type') == 'stopCall':
                is_recording = False
                is_in_call_mode = False
                print("停止通话")
        except json.JSONDecodeError:
            pass
    
    elif isinstance(message, bytes):
        # 这是音频数据，尝试播放（仅在监听模式下）
        received_audio_counter += 1
        if received_audio_counter % 100 == 0:
            print(f"已接收音频数据包: {received_audio_counter}")
        # 只有在监听模式下才播放音频（startlistening模式）
        if is_recording or is_in_call_mode:
            play_audio(message)

def send_audio(data):
    global sent_audio_counter
    # 仅在录音状态下发送音频数据
    if is_recording and ws.sock and ws.sock.connected:
        try:
            ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)
            sent_audio_counter += 1
            if sent_audio_counter % 100 == 0:
                print(f"已发送音频数据包: {sent_audio_counter} (大小: {len(data)}字节)")
        except Exception as e:
            print(f"发送音频数据时出错: {e}")

def play_audio(data):
    global playback_stream
    try:
        if playback_stream is None:
            playback_stream = audio_playback.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                output=True,
                output_device_index=OUTPUT_DEVICE_INDEX,
                frames_per_buffer=CHUNK
            )
        
        # 数据完整性检查
        if len(data) % BYTES_PER_SAMPLE != 0:
            return
            
        # 检查数据长度是否为偶数（16位音频数据）
        if len(data) % 2 != 0:
            data = data[:-1]
        
        # 大小端转换（如果需要）
        if sys.byteorder != 'little':
            num_samples = len(data) // BYTES_PER_SAMPLE
            try:
                samples = struct.unpack(f'>{num_samples}h', data)
                processed_data = struct.pack(f'<{num_samples}h', *samples)
            except struct.error:
                processed_data = data
        else:
            processed_data = data
        
        # 应用音量降低以减少回声
        try:
            audio_array = np.frombuffer(processed_data, dtype=np.int16)
            audio_array = (audio_array * 0.8).astype(np.int16)
            processed_data = audio_array.tobytes()
        except Exception:
            pass
        
        # 播放音频数据
        if playback_stream.is_active():
            playback_stream.write(processed_data)
    except Exception as e:
        print(f"播放音频时出错: {e}\n设备支持信息: {audio_playback.get_device_info_by_index(OUTPUT_DEVICE_INDEX)}")
        # 重置播放流以便下次重新初始化
        if playback_stream:
            try:
                playback_stream.stop_stream()
                playback_stream.close()
            except:
                pass
            playback_stream = None

def stop_playback():
    global playback_stream
    if playback_stream:
        try:
            playback_stream.stop_stream()
            playback_stream.close()
            playback_stream = None
        except Exception:
            pass

def on_error(ws, error):
    print("WebSocket错误")

def on_close(ws, close_status_code, close_msg):
    print("连接关闭")
    stop_playback()

def on_open(ws):
    print("连接成功")
    # 注册设备
    register_device()

def register_device():
    message = {
        'type': 'register',
        'deviceId': DEVICE_ID
    }
    ws.send(json.dumps(message))
    print(f"设备已注册: {DEVICE_ID}")

def start_audio_stream():
    p = pyaudio.PyAudio()
    
    def callback(in_data, frame_count, time_info, status):
        # 发送音频数据
        send_audio(in_data)
        return (in_data, pyaudio.paContinue)
    
    print(f"初始化音频录制流，使用输入设备索引: {INPUT_DEVICE_INDEX}")
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        input_device_index=INPUT_DEVICE_INDEX,
        frames_per_buffer=CHUNK,
        stream_callback=callback
    )
    
    stream.start_stream()
    print("音频流已启动，按 Ctrl+C 停止")
    
    try:
        while stream.is_active():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("停止音频流")
    
    stream.stop_stream()
    stream.close()
    p.terminate()

def main():
    global ws
    
    # 重置计数器
    received_audio_counter = 0
    sent_audio_counter = 0
    
    # 设置WebSocket调试 - 关闭调试追踪
    websocket.enableTrace(False)
    
    # 连接WebSocket服务器
    ws = websocket.WebSocketApp(SERVER_URL,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close,
                              subprotocols=["binary"])
    
    # 在单独的线程中运行WebSocket
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    
    # 等待连接建立
    time.sleep(1)
    
    # 启动音频流
    start_audio_stream()
    
    # 清理资源
    stop_playback()
    audio_playback.terminate()

if __name__ == "__main__":
    main()