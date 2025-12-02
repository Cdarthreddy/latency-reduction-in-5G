#!/bin/bash
# --- EC2 startup script for RL Orchestrator ---

# Update and install dependencies
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip git

# Clone your repo (replace with your real GitHub URL)
cd /home/ubuntu
git clone https://github.com/cdarthreddy/LatencyReductionInCloud.git
cd LatencyReductionInCloud

# Install Python dependencies
pip3 install -r requirements.txt

# Run training
python3 train_rl.py > train_log.txt 2>&1

# Upload results to S3 (optional — if utils/s3_io.py exists)
python3 main_remote.py > remote_log.txt 2>&1
