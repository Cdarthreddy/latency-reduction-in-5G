import pandas as pd
from analysis.report_utils import aggregate_latency

def test_aggregate_latency_basic():
    df = pd.DataFrame({
        "strategy": ["RL","RL","Rule","Rule"],
        "latency": [100,110,200,220]
    })
    agg = aggregate_latency(df)
    assert "mean" in agg.columns
    assert abs(agg.loc[agg.strategy=="RL","mean"].values[0]-105) < 1e-6
