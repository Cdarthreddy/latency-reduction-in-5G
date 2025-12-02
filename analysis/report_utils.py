"""
Utility functions for aggregating and visualizing latency results.
Handles multiple CSV formats from different experiment types.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt
import os


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize DataFrame to standard schema with 'strategy' and 'latency' columns.
    
    Handles two formats:
    1. RL-only format: task_id, node, latency_ms
    2. Multi-strategy format: strategy, app_type, size_mb, priority, node, latency
    """
    df = df.copy()  # Don't modify original
    
    # Normalize latency column name
    if "latency_ms" in df.columns:
        df.rename(columns={"latency_ms": "latency"}, inplace=True)
    elif "latency" not in df.columns:
        raise ValueError("DataFrame must contain either 'latency' or 'latency_ms' column")
    
    # Normalize strategy column
    if "strategy" not in df.columns:
        if "node" in df.columns:
            # RL-only format: derive strategy from node type
            df["strategy"] = df["node"].apply(
                lambda x: "RL-Edge" if "edge" in str(x).lower() else "RL-Cloud"
            )
        else:
            # Default to RL if no strategy or node info
            df["strategy"] = "RL"
    
    # Ensure latency is numeric
    df["latency"] = pd.to_numeric(df["latency"], errors="coerce")
    
    # Drop rows with invalid latency values
    df = df.dropna(subset=["latency"])
    
    return df


def aggregate_latency(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate latency statistics by strategy.
    
    Args:
        df: DataFrame with latency data (will be normalized)
        
    Returns:
        DataFrame with columns: strategy, mean, std, count, sem
    """
    if df.empty:
        return pd.DataFrame(columns=["strategy", "mean", "std", "count", "sem"])
    
    # Normalize the DataFrame schema
    try:
        df = normalize_dataframe(df)
    except Exception as e:
        raise ValueError(f"Failed to normalize DataFrame: {e}")
    
    if "latency" not in df.columns or "strategy" not in df.columns:
        raise ValueError("DataFrame must contain 'latency' and 'strategy' columns after normalization")
    
    # Group by strategy and compute statistics
    grouped = df.groupby("strategy")["latency"].agg(["mean", "std", "count"])
    grouped["sem"] = grouped["std"] / np.sqrt(grouped["count"])  # Standard error of mean
    
    # Fill NaN std with 0 (for single-value groups)
    grouped["std"] = grouped["std"].fillna(0.0)
    grouped["sem"] = grouped["sem"].fillna(0.0)
    
    return grouped.reset_index()


def plot_latency_distribution(df: pd.DataFrame, out_path: str):
    """
    Generate box plot of latency distributions by strategy.
    
    Args:
        df: DataFrame with latency data
        out_path: Output path for the plot
    """
    if df.empty:
        print("[WARN] Empty DataFrame - skipping plot generation")
        return
    
    # Normalize DataFrame
    try:
        df = normalize_dataframe(df)
    except Exception as e:
        print(f"[WARN] Failed to normalize DataFrame for plotting: {e}")
        return
    
    if "latency" not in df.columns or "strategy" not in df.columns:
        print("[WARN] Missing required columns for plotting")
        return
    
    # Create box plot
    plt.figure(figsize=(10, 6))
    
    # Get unique strategies
    strategies = df["strategy"].unique()
    
    if len(strategies) == 1:
        # Single strategy - simple box plot
        plt.boxplot(df["latency"])
        plt.xticks([1], [strategies[0]])
        plt.ylabel("Latency (ms)")
        plt.title(f"Latency Distribution: {strategies[0]}")
    else:
        # Multiple strategies - grouped box plot
        data_by_strategy = [df[df["strategy"] == s]["latency"].values for s in strategies]
        plt.boxplot(data_by_strategy)
        plt.xticks(range(1, len(strategies) + 1), strategies)
        plt.ylabel("Latency (ms)")
        plt.xlabel("Strategy")
        plt.title("Latency Distribution per Strategy")
    
    plt.grid(True, linestyle="--", alpha=0.5, axis="y")
    plt.tight_layout()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    plt.savefig(out_path, dpi=120)
    plt.close()
    print(f"[OK] Saved plot -> {out_path}")


def write_summary_md(stats_df: pd.DataFrame, out_path: str):
    """
    Write markdown summary of latency statistics.
    
    Args:
        stats_df: DataFrame with columns: strategy, mean, std, count, sem
        out_path: Output path for markdown file
    """
    if stats_df.empty:
        print("[WARN] Empty statistics DataFrame - skipping markdown generation")
        return
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# RL Orchestrator Performance Summary\n\n")
        f.write("## Latency Statistics by Strategy\n\n")
        
        # Write table header
        f.write("| Strategy | Mean (ms) | Std Dev (ms) | Count | SEM (ms) |\n")
        f.write("|----------|-----------|--------------|-------|----------|\n")
        
        # Write statistics for each strategy
        for _, row in stats_df.iterrows():
            strategy = row["strategy"]
            mean = row["mean"]
            std = row["std"] if "std" in row else 0.0
            count = int(row["count"]) if "count" in row else 0
            sem = row["sem"] if "sem" in row else 0.0
            
            f.write(f"| **{strategy}** | {mean:.2f} | {std:.2f} | {count} | {sem:.2f} |\n")
        
        f.write("\n")
        f.write("**Legend:**\n")
        f.write("- Mean: Average latency in milliseconds\n")
        f.write("- Std Dev: Standard deviation\n")
        f.write("- Count: Number of tasks\n")
        f.write("- SEM: Standard error of the mean\n")
    
    print(f"[OK] Saved markdown summary -> {out_path}")


