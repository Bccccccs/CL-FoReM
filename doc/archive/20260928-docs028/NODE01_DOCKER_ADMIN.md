# node01：管理员配置 Docker GPU 支持

当前 Docker 和驱动已安装，ybc 已有 Docker 权限。请补齐 NVIDIA Container Toolkit，修复镜像下载并验证。以下命令尚未执行。

## 1. 安装 NVIDIA Container Toolkit

在 Bash 中执行：

```bash
set -euo pipefail
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor --yes \
      -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

## 2. 修复 Docker 镜像下载

当前加速源返回 403，直连 Docker Hub 返回 EOF。请配置可用的内部镜像源或 daemon 代理。下面提供移除失效源、配置代理的方式；已有有效配置则跳过。

备份并移除失效源，保留其他字段：

```bash
sudo mkdir -p /etc/docker
if sudo test -f /etc/docker/daemon.json; then
  sudo cp -a /etc/docker/daemon.json "/etc/docker/daemon.json.bak.$(date +%Y%m%d-%H%M%S)"
fi
sudo python3 - <<'PY'
import json
from pathlib import Path
p = Path('/etc/docker/daemon.json')
c = json.loads(p.read_text()) if p.exists() else {}
c.pop('registry-mirrors', None)
p.write_text(json.dumps(c, indent=2) + '\n')
PY
```

使用我们当前的宿主代理 `http://127.0.0.1:17893`。已实测经此代理访问 Docker Hub 返回正常的认证响应 401；Docker 拉取仍需执行末节验证。请确保该代理在拉取期间持续运行。

```bash
sudo mkdir -p /etc/systemd/system/docker.service.d
sudo tee /etc/systemd/system/docker.service.d/mm-husky-proxy.conf >/dev/null <<PROXY
[Service]
Environment="HTTP_PROXY=http://127.0.0.1:17893"
Environment="HTTPS_PROXY=http://127.0.0.1:17893"
Environment="NO_PROXY=localhost,127.0.0.1,::1"
PROXY
```

## 3. 配置 GPU runtime 并重启

```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo dockerd --validate --config-file=/etc/docker/daemon.json
sudo docker ps
```

确认不会影响其他任务后执行：

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
sudo systemctl is-active docker
```

## 4. 验证并反馈结果

```bash
nvidia-ctk --version
sudo docker pull ros:noetic-ros-base-focal
sudo docker pull nvidia/cuda:12.8.1-base-ubuntu22.04

sudo docker run --rm --gpus all \
  nvidia/cuda:12.8.1-base-ubuntu22.04 nvidia-smi

# 验证项目入口使用的 NVIDIA runtime / CDI 模式
sudo docker run --rm --runtime=nvidia \
  -e NVIDIA_VISIBLE_DEVICES=nvidia.com/gpu=all \
  nvidia/cuda:12.8.1-base-ubuntu22.04 nvidia-smi
```

预期两次均能列出 4 张 RTX PRO 6000 Blackwell。请反馈 Toolkit 版本、验证结果；失败则提供命令及脱敏后的错误。

无需在宿主安装 ROS、PyTorch、完整 CUDA Toolkit 或重装驱动。

参考：[NVIDIA 官方安装指南](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)。
