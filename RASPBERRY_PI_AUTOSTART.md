# 树莓派开机自动启动 Tuya MCP 服务配置指南

## 概述

本指南说明如何配置树莓派在开机时自动激活 conda lerobot 环境并启动 Tuya MCP HTTP 服务。

## 文件说明

1. **auto_start_tuya_mcp.sh** - 自动启动脚本
   - 初始化 conda 环境
   - 激活 lerobot 环境
   - 切换到 ~/lerobot 目录
   - 运行 start_tuya_mcp_http_8000.sh

2. **tuya-mcp.service** - systemd 服务配置文件
   - 定义服务启动行为
   - 配置重启策略
   - 设置日志输出

## 安装步骤

### 1. 将文件复制到树莓派

```bash
# 在你的开发机器上，将文件复制到树莓派
scp auto_start_tuya_mcp.sh bobo@树莓派IP:/home/bobo/lerobot/
scp start_tuya_mcp_http_8000.sh bobo@树莓派IP:/home/bobo/lerobot/
scp tuya-mcp.service bobo@树莓派IP:/home/bobo/
```

### 2. 在树莓派上配置自动启动

SSH 登录到树莓派后执行以下命令：

```bash
# 确保脚本有执行权限
cd /home/bobo/lerobot
chmod +x auto_start_tuya_mcp.sh
chmod +x start_tuya_mcp_http_8000.sh

# 检查并调整 conda 路径（如果需要）
# 编辑 auto_start_tuya_mcp.sh，确认 CONDA_BASE 路径正确
# 常见路径：/home/bobo/miniconda3 或 /home/bobo/anaconda3
nano auto_start_tuya_mcp.sh

# 将服务文件复制到 systemd 目录
sudo cp /home/bobo/tuya-mcp.service /etc/systemd/system/

# 重新加载 systemd 配置
sudo systemctl daemon-reload

# 启用服务（开机自动启动）
sudo systemctl enable tuya-mcp.service

# 立即启动服务（测试）
sudo systemctl start tuya-mcp.service

# 查看服务状态
sudo systemctl status tuya-mcp.service
```

### 3. 验证安装

```bash
# 查看服务状态
sudo systemctl status tuya-mcp.service

# 查看服务日志
journalctl -u tuya-mcp.service -f

# 查看应用日志
tail -f /home/bobo/tuya_mcp_autostart.log
tail -f /home/bobo/tuya_mcp_service.log
```

## 服务管理命令

```bash
# 启动服务
sudo systemctl start tuya-mcp.service

# 停止服务
sudo systemctl stop tuya-mcp.service

# 重启服务
sudo systemctl restart tuya-mcp.service

# 查看服务状态
sudo systemctl status tuya-mcp.service

# 禁用开机自动启动
sudo systemctl disable tuya-mcp.service

# 启用开机自动启动
sudo systemctl enable tuya-mcp.service

# 查看实时日志
journalctl -u tuya-mcp.service -f
```

## 故障排查

### 1. 服务启动失败

```bash
# 查看详细错误信息
sudo systemctl status tuya-mcp.service
journalctl -u tuya-mcp.service -n 50

# 查看启动脚本日志
cat /home/bobo/tuya_mcp_autostart.log
```

### 2. Conda 环境问题

```bash
# 手动测试启动脚本
cd /home/bobo/lerobot
./auto_start_tuya_mcp.sh

# 检查 conda 路径
which conda
echo $CONDA_PREFIX

# 修改 auto_start_tuya_mcp.sh 中的 CONDA_BASE 路径
```

### 3. 权限问题

```bash
# 确保文件属于正确的用户
sudo chown -R bobo:bobo /home/bobo/lerobot
sudo chown bobo:bobo /home/bobo/tuya_mcp_*.log

# 确保脚本可执行
chmod +x /home/bobo/lerobot/auto_start_tuya_mcp.sh
chmod +x /home/bobo/lerobot/start_tuya_mcp_http_8000.sh
```

### 4. 网络延迟问题

如果服务启动过早导致网络未就绪，可以增加等待时间：

编辑 `auto_start_tuya_mcp.sh`，修改这一行：
```bash
sleep 10  # 将 10 改为更大的值，如 30
```

## 重要说明

1. **Conda 路径**：请根据实际安装路径修改 `auto_start_tuya_mcp.sh` 中的 `CONDA_BASE` 变量
2. **用户名**：如果你的树莓派用户不是 `bobo`，需要修改：
   - `tuya-mcp.service` 中的 `User` 和 `Group`
   - 所有脚本中的路径 `/home/bobo`
3. **日志文件**：服务会生成两个日志文件：
   - `/home/bobo/tuya_mcp_autostart.log` - 启动脚本日志
   - `/home/bobo/tuya_mcp_service.log` - systemd 服务日志

## 测试建议

1. **手动测试**：先手动运行脚本确认无误
   ```bash
   cd /home/bobo/lerobot
   ./auto_start_tuya_mcp.sh
   ```

2. **服务测试**：启用服务前先测试启动
   ```bash
   sudo systemctl start tuya-mcp.service
   sudo systemctl status tuya-mcp.service
   ```

3. **重启测试**：确认一切正常后重启树莓派测试开机自动启动
   ```bash
   sudo reboot
   ```

## 卸载服务

如果需要移除自动启动服务：

```bash
# 停止服务
sudo systemctl stop tuya-mcp.service

# 禁用服务
sudo systemctl disable tuya-mcp.service

# 删除服务文件
sudo rm /etc/systemd/system/tuya-mcp.service

# 重新加载 systemd
sudo systemctl daemon-reload
```

## 备选方案：使用 crontab

如果不想使用 systemd，也可以使用 crontab 在启动时运行：

```bash
# 编辑 crontab
crontab -e

# 添加以下行
@reboot sleep 30 && /home/bobo/lerobot/auto_start_tuya_mcp.sh
```

注意：crontab 方式的日志管理和服务重启功能不如 systemd 完善，推荐使用 systemd。
