#!/bin/bash
# Brev box bootstrap for a Cosmos3-Nano queue endpoint (board stack: tools/cosmos_local/server.py, diffusers bf16).
# Runs at boot as the startup script. Installs uv + a py3.12 venv, pulls the Nano weights; touches ~/nano/READY.
U=$(getent passwd 1000 | cut -d: -f1); H=$(getent passwd 1000 | cut -d: -f6); [ -z "$H" ] && H=/root && U=root
D=$H/nano; mkdir -p $D; chown $U $D
cat > $D/setup.sh <<'EOS'
#!/bin/bash
set -x
cd ~/nano
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH=$HOME/.local/bin:$PATH
uv venv -p 3.12 venv312
uv pip install -p venv312 huggingface_hub hf_transfer
( HF_HUB_ENABLE_HF_TRANSFER=1 venv312/bin/hf download nvidia/Cosmos3-Nano --local-dir models/Cosmos3-Nano > dl.log 2>&1 && touch WEIGHTS_OK ) &
uv pip install -p venv312 "diffusers @ git+https://github.com/huggingface/diffusers.git" torch torchvision transformers accelerate fastapi uvicorn python-multipart av opencv-python-headless requests > pip.log 2>&1 && touch PIP_OK
wait
[ -f WEIGHTS_OK ] && [ -f PIP_OK ] && touch READY
EOS
chmod +x $D/setup.sh; chown $U $D/setup.sh
su - $U -c "nohup bash ~/nano/setup.sh > ~/nano/setup.log 2>&1 &"
