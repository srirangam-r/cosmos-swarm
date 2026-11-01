#!/bin/bash
set -ex
mkdir -p ~/w && cd ~/w
python3 -m pip install -q --user uv huggingface_hub hf_transfer
export PATH=$HOME/.local/bin:$PATH
(HF_HUB_ENABLE_HF_TRANSFER=1 python3 -c "from huggingface_hub import snapshot_download as s; s('nvidia/Cosmos3-Nano', local_dir='$HOME/w/Cosmos3-Nano', ignore_patterns=['assets/*'])" > ~/w/dl.log 2>&1; echo DL_EXIT $? >> ~/w/dl.log) &
DLPID=$!
uv venv -p 3.11 venv && source venv/bin/activate
uv pip install torch --index-url https://download.pytorch.org/whl/cu128
uv pip install "git+https://github.com/huggingface/diffusers@86ef420b" transformers accelerate imageio imageio-ffmpeg av opencv-python-headless sentencepiece protobuf numpy pillow
wait $DLPID
grep -q "DL_EXIT 0" ~/w/dl.log
python -c "import torch,diffusers;print('OK',torch.__version__,diffusers.__version__,torch.cuda.is_available())"
echo SETUP_DONE
