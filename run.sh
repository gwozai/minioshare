#!/bin/bash

# 检查是否安装了conda
if ! command -v conda &> /dev/null; then
    echo "Error: conda is not installed. Please install Anaconda or Miniconda first."
    exit 1
fi

# 设置环境名称
ENV_NAME="minioshare"

# 停用当前环境
echo "Deactivating current conda environment..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda deactivate

# 检查环境是否存在
if ! conda env list | grep -q "^$ENV_NAME "; then
    echo "Creating new conda environment: $ENV_NAME"
    conda create -n $ENV_NAME python=3.9 -y
fi

# 激活环境
echo "Activating conda environment: $ENV_NAME"
conda activate $ENV_NAME

# 安装依赖
echo "Installing dependencies..."
pip install -r requirements.txt

# 运行应用
echo "Starting Flask application..."
python app.py 