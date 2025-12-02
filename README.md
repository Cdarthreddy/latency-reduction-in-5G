# 🚀 Optimizing Task Orchestration for Latency Reduction in 5G-Enabled Cloud Environments

An AI-driven Reinforcement Learning (RL) orchestrator that intelligently distributes workloads between edge and cloud nodes to minimize latency in 5G-enabled cloud environments.

## 🎯 Overview

This project implements a **self-learning orchestrator** using Q-learning to decide whether computational tasks (IoT, AR/VR, VANET) should execute on edge servers or cloud data centers. The system learns optimal policies through simulation and can be deployed on AWS infrastructure for real-world testing.

---

## ✨ Key Features

- 🤖 **Reinforcement Learning**: Q-learning based task orchestration
- 🌐 **5G Simulation**: Lightweight network simulator with extensible architecture
- ☁️ **AWS Integration**: EC2, S3, and CloudWatch for cloud deployment
- 📊 **Multi-Trial Automation**: Automated experiment execution and result aggregation
- 🧪 **Comprehensive Testing**: Unit tests with pytest (41 tests passing)
- 🏗️ **Infrastructure as Code**: Terraform-based deployment
- 📈 **Result Analysis**: Automated aggregation and visualization of experiment results

---

## 📋 Table of Contents

- [Setup](#-setup-instructions)
- [Local Execution](#-local-execution)
- [AWS Deployment](#-aws-deployment)
- [Project Structure](#-project-structure)
- [Technologies](#-technologies-used)
- [Output Files](#-output-files)
- [Testing](#-testing)
- [Utils Documentation](#-utils-documentation)

---

## ⚙️ Setup Instructions

### Prerequisites

- Python 3.10 or higher
- Git
- AWS Account (for cloud deployment, optional for local testing)

### Installation

#### 1. Clone Repository

```bash
git clone https://github.com/<your-username>/LatencyReductionInCloud.git
cd LatencyReductionInCloud
```

#### 2. Create Virtual Environment

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

> **Note:** If PowerShell shows "execution policy" error, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

#### 3. Install Dependencies

**Linux/Mac:**
```bash
pip install -r requirements.txt
```

**Windows:**
```powershell
python -m pip install -r requirements.txt
```

> **Note:** On Windows, always use `python -m pip` instead of `pip` directly.

---

## 💻 Local Execution

### Baseline Orchestration

Compare Random, Rule-based, and RL strategies:

```bash
python main.py
```

**Outputs:**
- `data/workload_results.csv` - Per-task latency records
- `data/workload_comparison.png` - Latency comparison visualization

### RL Training

Train the Q-learning orchestrator:

```bash
python train_rl.py
```

**Outputs:**
- `data/rl_weights.npy` - Learned Q-table weights
- `data/reward_curve.png` - Training progress visualization
- `data/workload_results.csv` - Evaluation results
- `data/workload_comparison.png` - Performance comparison

### Performance Analysis

Aggregate and analyze results from local files:

**Windows PowerShell:**
```powershell
$env:USE_LOCAL="1"; python -m analysis.analyze_results
```

**Windows CMD:**
```cmd
set USE_LOCAL=1 && python -m analysis.analyze_results
```

**Linux/Mac:**
```bash
USE_LOCAL=1 python -m analysis.analyze_results
```

**Outputs:**
```
analysis/out/
├── summary_stats.csv
├── latency_summary.png
└── summary.md
```

### Run Tests

```bash
python -m pytest -v
```

**Expected:** 41 tests passing

---

## ☁️ AWS Deployment

### Configuration

Edit `config.py` with your AWS settings:

```python
AWS_REGION = "us-east-1"
S3_BUCKET = "latency-results-project"
```

Or set environment variables:
```bash
export AWS_REGION=us-east-1
export S3_BUCKET=your-bucket-name
```

### Deploy with Terraform

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

Terraform provisions:
- EC2 instance with IAM role
- S3 bucket for artifacts
- CloudWatch log group
- Security groups

See `infra/terraform/TERRAFORM_SETUP.md` for detailed instructions.

### Run on EC2

Once deployed, the EC2 instance automatically runs `main_remote.py` via `user_data.sh`, which:

1. Generates workloads (if absent)
2. Trains RL model
3. Evaluates performance
4. Uploads artifacts to S3
5. Publishes logs and metrics to CloudWatch

**Uploaded Artifacts to S3:**
- `runs/{RUN_ID}/rl_weights.npy`
- `runs/{RUN_ID}/reward_curve.png`
- `runs/{RUN_ID}/workload_results.csv`
- `runs/{RUN_ID}/workload_comparison.png`
- `runs/{RUN_ID}/manifest.json`

### Multi-Trial Experiments

Run multiple trials that upload to S3:

```bash
python runner/exp_cli.py --episodes 200 300 --tasks 300 --sim simple
```

### Analyze Remote Results

Download and analyze results from S3:

```bash
python -m analysis.analyze_results
```

This downloads all results from S3 and generates aggregated reports.

### CloudWatch Setup

CloudWatch logging and metrics are automatically configured when using Terraform. See `infra/terraform/CLOUDWATCH_SETUP.md` for detailed documentation.

**Logs** (`/aws/latency-orchestrator/logs`):
- Training start/end times
- S3 upload status
- Errors and warnings
- Configuration details

**Metrics** (Namespace: `LatencyOrchestrator`):
- `TrainingAverageLatency` - Average latency from training
- `TaskLatency` - Per-task latency with dimensions (NodeType, AppType)
- `EvaluationEdgeAvgLatency` / `EvaluationCloudAvgLatency` - Evaluation metrics
- `JobCompletion` - Job completion status

**Viewing Logs:**
```bash
aws logs tail /aws/latency-orchestrator/logs --follow --region us-east-1
```

**Viewing Metrics:**
- AWS Console: CloudWatch → Metrics → Custom namespaces → LatencyOrchestrator

> **Note:** CloudWatch works automatically on EC2 with proper IAM role. If running locally without AWS credentials, it gracefully degrades to console logging without errors.

---

## 🗂️ Project Structure

```
tarun-project/
├── orchestrator/              # Core orchestration logic
│   ├── __init__.py
│   ├── base_orchestrator.py   # Base orchestrator class (legacy)
│   ├── environment.py         # Task and Node definitions
│   ├── rl_agent.py           # Alternative RL agent implementation
│   ├── rl_orchestrator.py    # Q-learning orchestrator (main RL implementation)
│   ├── random_orchestrator.py # Baseline: Random strategy
│   ├── rule_orchestrator.py  # Baseline: Rule-based strategy
│   ├── sim_interface.py      # Network simulator interface and implementations
│   ├── simu5g_adapter.py     # Simu5G integration stub
│   ├── simulation.py         # Simulation utilities
│   ├── workload_generator.py # Workload generation
│   └── generate_workloads.py # Legacy workload generator utility
│
├── utils/                     # Utility modules
│   ├── cloudwatch.py         # AWS CloudWatch logging & metrics
│   ├── console.py            # Safe console output (Windows encoding support)
│   ├── logger.py             # CSV file logging utility (legacy)
│   ├── manifest.py           # Experiment metadata generation
│   ├── s3_io.py              # AWS S3 file upload operations
│   └── README.md             # Utils documentation
│
├── analysis/                  # Result analysis and reporting
│   ├── __init__.py
│   ├── analyze_results.py    # Aggregate and analyze results (S3 or local)
│   ├── report_utils.py       # Visualization and aggregation utilities
│   └── out/                  # Generated analysis reports
│       ├── summary_stats.csv
│       ├── latency_summary.png
│       └── summary.md
│
├── runner/                    # Experiment automation
│   └── exp_cli.py            # Multi-trial CLI runner
│
├── tests/                     # Test suite
│   ├── conftest.py           # Pytest configuration (path setup)
│   ├── test_aggregation.py   # Test aggregation utilities
│   ├── test_manifest_schema.py # Test manifest structure
│   ├── test_node.py          # Test Node class (13 tests)
│   ├── test_rl_orchestrator.py # Test RL orchestrator (13 tests)
│   ├── test_simulator.py     # Test simulators (12 tests)
│   └── test_train_entrypoint.py # Test training entrypoint
│
├── infra/                     # Infrastructure as Code
│   └── terraform/            # Terraform configuration
│       ├── main.tf           # Main Terraform configuration
│       ├── variables.tf      # Variable definitions
│       ├── outputs.tf        # Output values
│       ├── terraform.tfvars  # Variable values
│       ├── user_data.sh      # EC2 startup script
│       ├── TERRAFORM_SETUP.md # Terraform setup guide
│       ├── CLOUDWATCH_SETUP.md # CloudWatch configuration guide
│       └── KEY_PAIR_SETUP.md # SSH key pair setup guide
│
├── data/                      # Generated data and results
│   ├── workloads.csv         # Generated workload tasks
│   ├── workload_results.csv  # Task execution results
│   ├── rl_weights.npy        # Learned Q-table weights
│   ├── reward_curve.png      # Training progress visualization
│   ├── workload_comparison.png # Latency comparison plot
│   └── manifest.json         # Experiment metadata (if generated locally)
│
├── main.py                    # Baseline comparison script
├── train_rl.py               # RL training entrypoint
├── main_remote.py            # AWS remote execution script
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
└── readme.md                 # This file
```

---

## 🧰 Technologies Used

| Category | Technologies |
|----------|-------------|
| **Language** | Python 3.10+ |
| **ML/AI** | Q-learning, NumPy, Pandas |
| **Visualization** | Matplotlib, Seaborn, SciPy |
| **Cloud** | AWS EC2, S3, CloudWatch, boto3 |
| **Infrastructure** | Terraform |
| **Testing** | PyTest |
| **Version Control** | Git, GitHub |

---

## 📊 Output Files

| File | Description | Location |
|------|-------------|----------|
| `workload_results.csv` | Per-task latency records (task_id, node, latency_ms) | `data/` |
| `reward_curve.png` | RL training progress visualization | `data/` |
| `workload_comparison.png` | Edge vs Cloud latency comparison box plot | `data/` |
| `rl_weights.npy` | Learned Q-table weights (NumPy array) | `data/` |
| `manifest.json` | Run metadata (timestamp, config, metrics) | `data/` or S3 |
| `summary_stats.csv` | Aggregated performance statistics | `analysis/out/` |
| `latency_summary.png` | Aggregated latency distribution plot | `analysis/out/` |
| `summary.md` | Human-readable analysis report | `analysis/out/` |

---

## 🧪 Testing

The project includes comprehensive unit tests:

```bash
# Run all tests
python -m pytest -v

# Run specific test file
python -m pytest tests/test_rl_orchestrator.py -v

# Run with more details
python -m pytest -v --tb=short
```

**Test Coverage:**
- ✅ 41 tests passing
- Node and Task execution (13 tests)
- RL Orchestrator (13 tests)
- Simulator implementations (12 tests)
- Aggregation utilities (1 test)
- Manifest schema (1 test)
- Training entrypoint (1 test)

---

## 📚 Utils Documentation

The `utils/` folder contains reusable utility functions. See [utils/README.md](utils/README.md) for detailed documentation:

- **cloudwatch.py**: AWS CloudWatch logging and metrics
- **console.py**: Safe console output with Windows encoding support
- **manifest.py**: Experiment metadata generation
- **s3_io.py**: AWS S3 file upload operations
- **logger.py**: CSV file logging (legacy)

---

## 📖 Additional Documentation

- [Utils Documentation](utils/README.md) - Detailed utils folder documentation
- [Terraform Setup Guide](infra/terraform/TERRAFORM_SETUP.md) - Terraform deployment instructions
- [CloudWatch Setup Guide](infra/terraform/CLOUDWATCH_SETUP.md) - CloudWatch configuration and troubleshooting
- [Key Pair Setup Guide](infra/terraform/KEY_PAIR_SETUP.md) - SSH key pair configuration

---

## 🔧 AWS Configuration

### IAM Permissions Required

- **S3**: `s3:PutObject`, `s3:GetObject`, `s3:ListBucket`
- **CloudWatch Logs**: `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`
- **CloudWatch Metrics**: `cloudwatch:PutMetricData`

The Terraform configuration automatically sets up all required IAM roles and permissions.

### Environment Variables

You can override default configuration via environment variables:

```bash
export AWS_REGION=us-west-2
export S3_BUCKET=my-bucket-name
export DATA_DIR=./results
export SIM_TYPE=simple
export EPISODES=300
export USE_LOCAL=1  # For local-only analysis
```

---

## 🧪 Example Run Output

### Local Execution

```
[config] Using region=us-east-1, bucket=latency-results-project, run=run-20251202T094808Z
[INFO] CloudWatch logging disabled (local mode - invalid AWS credentials)
[INFO] CloudWatch metrics disabled (local mode - invalid AWS credentials)
[OK] Using simulator: simple
[START] Starting Q-Learning simulation...
Episode  20/300 | Avg reward (last 20): -284520.45
Episode  40/300 | Avg reward (last 20): -267830.12
...
Episode 300/300 | Avg reward (last 20): -252840.84
[OK] RL training completed.
[OK] RL done | avg latency: 845.62 ms
[OK] Training + Evaluation complete.
```

### Remote Execution (EC2)

```
[OK] Workload already present; re-using existing file.
[OK] CloudWatch logging enabled -> /aws/latency-orchestrator/logs/orchestrator-20251202T094808
[OK] Using simulator: simple
[START] Starting Q-Learning simulation...
...
[OK] Uploading artifacts to S3 under prefix: runs/run-20251027T132619Z
[OK] Uploaded -> s3://latency-results-project/runs/run-20251027T132619Z/rl_weights.npy
[OK] Uploaded -> s3://latency-results-project/runs/run-20251027T132619Z/reward_curve.png
[OK] Uploaded -> s3://latency-results-project/runs/run-20251027T132619Z/workload_results.csv
[OK] Uploaded -> s3://latency-results-project/runs/run-20251027T132619Z/workload_comparison.png
[OK] Uploaded -> s3://latency-results-project/runs/run-20251027T132619Z/manifest.json
[OK] Remote execution complete.
```

---

## 📈 Development Timeline

| Week | Focus | Deliverable |
|------|-------|-------------|
| 1-2 | Research & Setup | Literature review, environment design |
| 3-4 | Core Design | Node, Task, and simulator architecture |
| 5 | Baseline | Random and Rule-based orchestrators |
| 6 | Integration | Verified simulation flow |
| 7-9 | RL Implementation | Q-learning orchestrator with training |
| 10 | AWS Integration | EC2 + S3 deployment automation |
| 11 | Automation | Multi-trial runner + CloudWatch |
| 12 | Evaluation | Regression tests + performance analysis |

---

## 🎯 Quick Commands Reference

### Local Execution
```bash
# Activate venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows PowerShell

# Run baseline comparison
python main.py

# Train RL agent
python train_rl.py

# Analyze local results
USE_LOCAL=1 python -m analysis.analyze_results

# Run tests
python -m pytest -v
```

### Remote Execution (EC2)
```bash
# Run remote execution
python main_remote.py

# Run multiple trials
python runner/exp_cli.py --episodes 200 300 --tasks 300 --sim simple

# Analyze S3 results
python -m analysis.analyze_results
```

---

## 🐛 Troubleshooting

**CloudWatch warnings locally:**
- These are normal when running without AWS credentials
- CloudWatch automatically disables in local mode
- No action needed

**Import errors:**
- Ensure virtual environment is activated
- Run `python -m pytest` instead of `pytest` directly
- Check that you're in the project root directory

**AWS access errors:**
- For local analysis: Use `USE_LOCAL=1` environment variable
- For S3: Configure credentials via `aws configure` or IAM roles

**Test failures:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Run from project root: `python -m pytest -v`

---

## 📜 License

Licensed under the **MIT License**. You may use, modify, and distribute this code with proper attribution.

---

## 🏁 Citation

> "Optimizing Task Orchestration for Latency Reduction in 5G-Enabled Cloud Environments." 2025.

---

## 👤 Author

**Siddhartha Reddy Thigala**

---

## 📝 Notes

- The project gracefully handles missing AWS credentials for local development
- All CloudWatch operations are optional and fail gracefully in local mode
- The `utils/` folder contains reusable utilities documented in `utils/README.md`
- Test suite uses `conftest.py` for proper Python path configuration

---

**© 2025 Siddhartha | Latency Reduction in Cloud Project**
