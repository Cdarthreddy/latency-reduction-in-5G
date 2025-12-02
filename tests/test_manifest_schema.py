import json
import os
from utils.manifest import create_manifest


def test_manifest_structure(tmp_path):
    """Test that manifest contains all required keys."""
    m = create_manifest("simple", 300, 200, 500.0)
    p = tmp_path / "manifest.json"
    with open(p, "w") as f:
        json.dump(m, f)
    d = json.load(open(p))
    
    # Check required keys match actual manifest structure
    required_keys = [
        "run_id",
        "timestamp",
        "simulator",  # Note: manifest uses "simulator", not "sim_type"
        "episodes",
        "tasks",
        "avg_latency_ms",  # Note: manifest uses "avg_latency_ms", not "avg_latency"
        "region",
        "s3_bucket",
        "s3_prefix",
        "host"
    ]
    
    for key in required_keys:
        assert key in d, f"Missing required key: {key}"
    
    # Verify data types
    assert isinstance(d["episodes"], int)
    assert isinstance(d["tasks"], int)
    assert isinstance(d["avg_latency_ms"], (int, float))
    assert isinstance(d["simulator"], str)
