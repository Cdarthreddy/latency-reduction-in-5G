"""
Enhanced CloudWatch logging and metrics utility for the orchestrator project.
Supports both log streaming and custom metrics publishing.
"""

import boto3
import time
import os
from typing import Optional
from datetime import datetime, timezone

# Import botocore exceptions for better error handling
try:
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    # Fallback if botocore not available
    ClientError = Exception
    NoCredentialsError = Exception

# Import safe print utility
try:
    from utils.console import safe_print
except ImportError:
    def safe_print(msg: str, fallback: str | None = None) -> None:
        try:
            print(msg)
        except UnicodeEncodeError:
            if fallback:
                print(fallback)
            else:
                print(msg.encode('ascii', 'replace').decode('ascii'))


class CloudWatchLogger:
    """
    CloudWatch Logs logger for streaming application logs.
    Automatically handles log group and stream creation.
    """
    
    def __init__(
        self, 
        log_group: str = "/aws/latency-orchestrator/logs",
        log_stream: Optional[str] = None,
        region: Optional[str] = None
    ):
        """
        Initialize CloudWatch logger.
        
        Args:
            log_group: CloudWatch log group name
            log_stream: Log stream name (auto-generated if None)
            region: AWS region (defaults to config or us-east-1)
        """
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.log_group = log_group
        self.log_stream = log_stream or f"orchestrator-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
        
        self.client = None
        self.sequence_token = None
        self.enabled = False
        self._error_shown = False  # Track if we've already shown the error message
        
        # Try to initialize boto3 client (will fail gracefully if AWS credentials not available)
        try:
            self.client = boto3.client("logs", region_name=self.region)
            # Test credentials by trying to describe log groups (lightweight operation)
            try:
                self.client.describe_log_groups(logGroupNamePrefix=self.log_group, limit=1)
                self._ensure_log_group()
                self._ensure_log_stream()
                self.enabled = True
                safe_print(
                    f"[OK] CloudWatch logging enabled -> {self.log_group}/{self.log_stream}",
                    fallback=f"[OK] CloudWatch logging enabled -> {self.log_group}/{self.log_stream}"
                )
            except Exception as e:
                # Credentials invalid - disable silently
                self.client = None
                self.enabled = False
                if not self._error_shown:
                    safe_print(
                        f"[INFO] CloudWatch logging disabled (local mode - invalid AWS credentials)",
                        fallback=f"[INFO] CloudWatch logging disabled (local mode - invalid AWS credentials)"
                    )
                    self._error_shown = True
        except Exception as e:
            # Not an error - just means we're running locally without AWS credentials
            self.enabled = False
            if not self._error_shown:
                safe_print(
                    f"[INFO] CloudWatch logging disabled (local mode - no AWS credentials)",
                    fallback=f"[INFO] CloudWatch logging disabled (local mode - no AWS credentials)"
                )
                self._error_shown = True

    def _ensure_log_group(self):
        """Create log group if it doesn't exist."""
        if not self.client or not self.enabled:
            return
        try:
            self.client.create_log_group(logGroupName=self.log_group)
            # Set retention to 7 days (optional, but good practice)
            try:
                self.client.put_retention_policy(
                    logGroupName=self.log_group,
                    retentionInDays=7
                )
            except Exception:
                pass  # Ignore if policy already set or permission denied
        except self.client.exceptions.ResourceAlreadyExistsException:
            pass
        except Exception as e:
            # Disable on credential errors and only show once
            error_str = str(e).lower()
            if "token" in error_str or "credentials" in error_str or "unauthorized" in error_str:
                self.enabled = False
                self.client = None
                if not self._error_shown:
                    safe_print(
                        f"[INFO] CloudWatch logging disabled (invalid AWS credentials)",
                        fallback=f"[INFO] CloudWatch logging disabled (invalid AWS credentials)"
                    )
                    self._error_shown = True
            # Only show other errors once
            elif not self._error_shown:
                safe_print(
                    f"[WARN] Could not create log group: {e}",
                    fallback=f"[WARN] Could not create log group: {e}"
                )
                self._error_shown = True

    def _ensure_log_stream(self):
        """Create log stream if it doesn't exist."""
        if not self.client or not self.enabled:
            return
        try:
            self.client.create_log_stream(
                logGroupName=self.log_group,
                logStreamName=self.log_stream
            )
        except self.client.exceptions.ResourceAlreadyExistsException:
            pass
        except Exception as e:
            # Disable on credential errors and only show once
            error_str = str(e).lower()
            if "token" in error_str or "credentials" in error_str or "unauthorized" in error_str:
                self.enabled = False
                self.client = None
                if not self._error_shown:
                    safe_print(
                        f"[INFO] CloudWatch logging disabled (invalid AWS credentials)",
                        fallback=f"[INFO] CloudWatch logging disabled (invalid AWS credentials)"
                    )
                    self._error_shown = True
            # Only show other errors once
            elif not self._error_shown:
                safe_print(
                    f"[WARN] Could not create log stream: {e}",
                    fallback=f"[WARN] Could not create log stream: {e}"
                )
                self._error_shown = True

    def log(self, message: str, level: str = "INFO"):
        """
        Log a message to CloudWatch.
        
        Args:
            message: Log message
            level: Log level (INFO, WARN, ERROR, DEBUG)
        """
        if not self.enabled or not self.client:
            return  # Silently skip if not enabled (local mode)
        
        timestamp = int(time.time() * 1000)
        formatted_message = f"[{level}] {message}"
        
        params = {
            "logGroupName": self.log_group,
            "logStreamName": self.log_stream,
            "logEvents": [
                {
                    "timestamp": timestamp,
                    "message": formatted_message
                }
            ]
        }

        if self.sequence_token:
            params["sequenceToken"] = self.sequence_token

        try:
            resp = self.client.put_log_events(**params)
            self.sequence_token = resp.get("nextSequenceToken")
        except Exception as e:
            # Disable on credential errors and suppress repeated warnings
            error_str = str(e).lower()
            if "token" in error_str or "credentials" in error_str or "unauthorized" in error_str:
                self.enabled = False
                self.client = None
                # Warning already shown in initialization
            # Silently ignore - don't spam warnings

    def info(self, message: str):
        """Log an INFO message."""
        self.log(message, "INFO")

    def warning(self, message: str):
        """Log a WARNING message."""
        self.log(message, "WARN")

    def error(self, message: str):
        """Log an ERROR message."""
        self.log(message, "ERROR")

    def debug(self, message: str):
        """Log a DEBUG message."""
        self.log(message, "DEBUG")


class CloudWatchMetrics:
    """
    CloudWatch Metrics publisher for custom metrics.
    """
    
    def __init__(self, namespace: str = "LatencyOrchestrator", region: Optional[str] = None):
        """
        Initialize CloudWatch metrics publisher.
        
        Args:
            namespace: CloudWatch metrics namespace
            region: AWS region (defaults to config or us-east-1)
        """
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.namespace = namespace
        self.client = None
        self.enabled = False
        self._error_shown = False  # Track if we've already shown the error message
        
        try:
            self.client = boto3.client("cloudwatch", region_name=self.region)
            # Test credentials by trying to list metrics (lightweight operation)
            try:
                self.client.list_metrics(Namespace=self.namespace, MaxRecords=1)
                self.enabled = True
            except Exception as e:
                # Credentials invalid - disable silently
                self.client = None
                self.enabled = False
                if not self._error_shown:
                    safe_print(
                        f"[INFO] CloudWatch metrics disabled (local mode - invalid AWS credentials)",
                        fallback=f"[INFO] CloudWatch metrics disabled (local mode - invalid AWS credentials)"
                    )
                    self._error_shown = True
        except Exception as e:
            self.enabled = False
            if not self._error_shown:
                safe_print(
                    f"[INFO] CloudWatch metrics disabled (local mode - no AWS credentials)",
                    fallback=f"[INFO] CloudWatch metrics disabled (local mode - no AWS credentials)"
                )
                self._error_shown = True

    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "None",
        dimensions: Optional[dict] = None
    ):
        """
        Publish a custom metric to CloudWatch.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit (Count, Milliseconds, Percent, None, etc.)
            dimensions: Optional dimensions (dict of key-value pairs)
        """
        if not self.enabled or not self.client:
            return  # Silently skip if not enabled
        
        metric_data = {
            "MetricName": metric_name,
            "Value": value,
            "Unit": unit,
            "Timestamp": datetime.now(timezone.utc)
        }
        
        if dimensions:
            metric_data["Dimensions"] = [
                {"Name": k, "Value": str(v)} for k, v in dimensions.items()
            ]
        
        try:
            self.client.put_metric_data(
                Namespace=self.namespace,
                MetricData=[metric_data]
            )
        except Exception as e:
            # Disable on credential errors and suppress repeated warnings
            error_str = str(e).lower()
            if "token" in error_str or "credentials" in error_str or "unauthorized" in error_str:
                self.enabled = False
                self.client = None
                # Warning already shown in initialization
            # Silently ignore - don't spam warnings

    def put_latency_metric(self, latency_ms: float, node_type: str, app_type: str):
        """Helper to publish latency metrics."""
        self.put_metric(
            "TaskLatency",
            latency_ms,
            "Milliseconds",
            dimensions={"NodeType": node_type, "AppType": app_type}
        )

    def put_training_metric(self, episode: int, reward: float, avg_latency: float):
        """Helper to publish RL training metrics."""
        self.put_metric("TrainingReward", reward, "None", dimensions={"Episode": str(episode)})
        self.put_metric("AverageLatency", avg_latency, "Milliseconds", dimensions={"Episode": str(episode)})

    def put_completion_metric(self, success: bool, total_tasks: int):
        """Helper to publish job completion metrics."""
        status = "Success" if success else "Failure"
        self.put_metric(
            "JobCompletion",
            1.0,
            "Count",
            dimensions={"Status": status, "TotalTasks": str(total_tasks)}
        )


# Singleton instances (optional, can be instantiated per module)
_default_logger: Optional[CloudWatchLogger] = None
_default_metrics: Optional[CloudWatchMetrics] = None


def get_logger() -> CloudWatchLogger:
    """Get or create default CloudWatch logger instance."""
    global _default_logger
    if _default_logger is None:
        _default_logger = CloudWatchLogger()
    return _default_logger


def get_metrics() -> CloudWatchMetrics:
    """Get or create default CloudWatch metrics instance."""
    global _default_metrics
    if _default_metrics is None:
        _default_metrics = CloudWatchMetrics()
    return _default_metrics

