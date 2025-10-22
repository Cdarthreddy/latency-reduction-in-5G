import matplotlib.pyplot as plt

def plot_latency_comparison(df, out_path="data/latency_comparison.png"):
    # Build simple boxplot of latency grouped by strategy
    strategies = df["strategy"].unique().tolist()
    data = [df[df["strategy"] == s]["latency"].values for s in strategies]

    plt.figure(figsize=(8, 5))
    plt.boxplot(data, labels=strategies, showmeans=True)
    plt.title("Latency Comparison: Random vs Rule-Based Orchestration")
    plt.ylabel("Latency (ms)")
    plt.xlabel("Strategy")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(out_path)
    print(f"📈 Saved plot → {out_path}")
