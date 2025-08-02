#!/usr/bin/env python

# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess
import sys
import time
import argparse
import signal
import os

def signal_handler(sig, frame):
    print('Stopping both processes...')
    if 'lekiwi_process' in globals():
        lekiwi_process.terminate()
    if 'audio_process' in globals():
        audio_process.terminate()
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Start LeKiwi robot host with audio support")
    parser.add_argument("--robot-id", type=str, default="my_awesome_kiwi", help="Robot ID")
    parser.add_argument("--no-audio", action="store_true", help="Start without audio support")
    args = parser.parse_args()

    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start LeKiwi host
    lekiwi_cmd = [
        sys.executable, "-m", "lerobot.robots.lekiwi.lekiwi_host",
        f"--robot.id={args.robot_id}"
    ]
    
    print(f"Starting LeKiwi host with command: {' '.join(lekiwi_cmd)}")
    global lekiwi_process
    lekiwi_process = subprocess.Popen(lekiwi_cmd)
    
    # Give the host a moment to start
    time.sleep(2)
    
    if not args.no_audio:
        # Start audio program
        audio_cmd = [
            sys.executable, "-m", "lerobot.robots.lekiwi.lekiwi_audio"
        ]
        
        print(f"Starting LeKiwi audio with command: {' '.join(audio_cmd)}")
        global audio_process
        audio_process = subprocess.Popen(audio_cmd)
    
    try:
        # Wait for either process to complete
        while True:
            if lekiwi_process.poll() is not None:
                print("LeKiwi host process has terminated")
                if not args.no_audio:
                    audio_process.terminate()
                break
                
            if not args.no_audio and audio_process.poll() is not None:
                print("Audio process has terminated")
                lekiwi_process.terminate()
                break
                
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()