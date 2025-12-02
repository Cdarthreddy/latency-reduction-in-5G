# Utils Folder - Utility Functions

The `utils` folder contains reusable utility functions and classes that support the orchestrator project. These are cross-cutting concerns used across multiple modules.

---

## 📁 Files Overview

| File | Purpose | Used By |
|------|---------|---------|
| `cloudwatch.py` | AWS CloudWatch logging and metrics | `train_rl.py`, `main_remote.py` |
| `console.py` | Safe console output with Windows encoding support | All scripts |
| `logger.py` | CSV file logging utility | Legacy code (may be deprecated) |
| `manifest.py` | Experiment manifest/metadata generation | `main_remote.py` |
| `s3_io.py` | AWS S3 file upload utilities | `main_remote.py` |

---

## 🔍 Detailed File Descriptions

### 1. `cloudwatch.py` - CloudWatch Integration

**Purpose:** Provides AWS CloudWatch logging and metrics publishing capabilities.

**Key Classes:**
- `CloudWatchLogger`: Streams application logs to CloudWatch Logs
- `CloudWatchMetrics`: Publishes custom metrics to CloudWatch Metrics

**Features:**
- Automatic log group/stream creation
- Graceful degradation when AWS credentials unavailable (local mode)
- Singleton pattern via `get_logger()` and `get_metrics()`
- Supports training metrics, latency metrics, and job completion tracking

**Usage:**
```python
from utils.cloudwatch import get_logger, get_metrics

logger = get_logger()
logger.info("Training started")

metrics = get_metrics()
metrics.put_metric("AverageLatency", 123.45, "Milliseconds")
```

**Used in:**
- `train_rl.py` - Logs training progress and metrics
- `main_remote.py` - Remote execution logging

---

### 2. `console.py` - Safe Console Output

**Purpose:** Handles console output with proper encoding support, especially for Windows.

**Key Functions:**
- `safe_print()`: Prints messages with fallback for encoding errors
- `setup_console_encoding()`: Configures UTF-8 encoding on Windows

**Features:**
- Handles Unicode encoding errors gracefully
- Automatic emoji fallback replacement
- Cross-platform compatibility

**Usage:**
```python
from utils.console import safe_print

safe_print("✅ Training complete!")
# Falls back to "[OK] Training complete!" on encoding errors
```

**Used in:**
- `main.py`
- `main_remote.py`
- `utils/cloudwatch.py`
- Most scripts that need console output

---

### 3. `logger.py` - CSV File Logger (Legacy)

**Purpose:** Simple CSV logging utility for task execution results.

**Key Class:**
- `Logger`: Writes task results to CSV file

**Features:**
- Creates CSV file with headers
- Logs task_id, node, and latency_ms

**Usage:**
```python
from utils.logger import Logger

logger = Logger("data/results.csv")
logger.log(task_id=1, node="edge-1", latency=123.45)
logger.close()
```

**Note:** This appears to be legacy code. Current code uses direct CSV writing or pandas.

---

### 4. `manifest.py` - Experiment Metadata

**Purpose:** Creates and saves experiment manifests (metadata files) for reproducibility.

**Key Functions:**
- `create_manifest()`: Builds a manifest dictionary with run metadata
- `save_manifest_local()`: Saves manifest to local JSON file

**Manifest Contents:**
- Run ID and timestamp
- Simulator type and configuration
- Number of episodes and tasks
- Average latency results
- AWS region and S3 bucket info
- Hostname

**Usage:**
```python
from utils.manifest import create_manifest, save_manifest_local

manifest = create_manifest(
    sim_type="simple",
    episodes=300,
    tasks=300,
    avg_latency=123.45
)
path = save_manifest_local(manifest)
```

**Used in:**
- `main_remote.py` - Creates manifest before uploading to S3

**Example Manifest:**
```json
{
  "run_id": "run-20251202T094808Z",
  "timestamp": "2025-12-02T09:48:08Z",
  "simulator": "simple",
  "episodes": 300,
  "tasks": 300,
  "avg_latency_ms": 911.11,
  "region": "us-east-1",
  "s3_bucket": "latency-results-project",
  "s3_prefix": "runs/run-20251202T094808Z",
  "host": "ec2-instance-123"
}
```

---

### 5. `s3_io.py` - S3 File Operations

**Purpose:** Handles file uploads to AWS S3 bucket.

**Key Functions:**
- `upload_file()`: Uploads local file to S3 with automatic path prefixing

**Features:**
- Automatic path prefixing (`runs/{RUN_ID}/`)
- Error handling for missing files
- Returns S3 URL on success

**Usage:**
```python
from utils.s3_io import upload_file

url = upload_file("data/workload_results.csv")
# Uploads to: s3://bucket/runs/run-20251202T094808Z/workload_results.csv
```

**Used in:**
- `main_remote.py` - Uploads all experiment artifacts to S3

**Dependencies:**
- Requires AWS credentials (IAM role or access keys)
- Uses `boto3` library

---

## 🔄 Common Patterns

### 1. Graceful Degradation
Most utils handle missing dependencies gracefully:
```python
try:
    from utils.cloudwatch import get_logger
    logger = get_logger()
except ImportError:
    logger = None  # Continue without CloudWatch
```

### 2. Local vs Remote Mode
Utils adapt to execution environment:
- **Local:** CloudWatch disabled, S3 operations skipped
- **Remote (EC2):** Full AWS integration enabled

### 3. Error Handling
All utils include robust error handling:
- Invalid AWS credentials → Silent degradation
- Missing files → Clear error messages
- Encoding issues → Automatic fallbacks

---

## 📦 Dependencies

| Utility | Required Dependencies | Optional |
|---------|----------------------|----------|
| `cloudwatch.py` | `boto3`, `botocore` | - |
| `console.py` | None (standard library) | - |
| `logger.py` | None (standard library) | - |
| `manifest.py` | None (standard library) | - |
| `s3_io.py` | `boto3`, `botocore` | - |

---

## 🎯 Design Principles

1. **Fail Gracefully:** Utils work without AWS credentials (local mode)
2. **Single Responsibility:** Each file has one clear purpose
3. **Reusability:** Functions can be imported and used across modules
4. **Error Handling:** Clear error messages and fallback behavior
5. **Cross-Platform:** Works on Windows, Linux, and Mac

---

## 📝 Usage Examples

### Complete Example: Remote Execution
```python
from utils.cloudwatch import get_logger, get_metrics
from utils.s3_io import upload_file
from utils.manifest import create_manifest, save_manifest_local

# Initialize CloudWatch
logger = get_logger()
metrics = get_metrics()

# Log training start
logger.info("Starting RL training")

# Create manifest
manifest = create_manifest("simple", 300, 300, 123.45)
save_manifest_local(manifest)

# Upload artifacts
upload_file("data/workload_results.csv")
upload_file("data/manifest.json")

# Log metrics
metrics.put_metric("TrainingLatency", 123.45, "Milliseconds")
```

---

## 🔧 Future Enhancements

Potential improvements:
- Add retry logic for S3 uploads
- Add batch metric publishing
- Support for CloudWatch Insights queries
- Add manifest validation
- Unit tests for each utility

---

## 📚 Related Documentation

- See `config.py` for AWS configuration
- See `EXECUTABLE_FILES.md` for usage context
- See `README.md` for overall project structure

