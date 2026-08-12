from pathlib import Path
import json
import pandas as pd

from .multi_model import ThreeModelSystem
from .feature_engine import EXTENDED_FEATURE_COLUMNS, TARGET_COLUMNS, build_panel_dataset, feature_manifest


def main():
    panel = pd.read_csv("research/yahoo_psx_panel.csv", parse_dates=["date"])
    training_panel = build_panel_dataset(panel)
    training_columns = ["date", "symbol"] + EXTENDED_FEATURE_COLUMNS + TARGET_COLUMNS
    training_panel[training_columns].to_csv("research/training_panel_5d.csv", index=False)
    system = ThreeModelSystem().fit(panel)
    forecasts = system.forecast(panel)
    report = {
        "experiment": "psx_five_day_three_model_system", "data_source": "cached_yahoo_research",
        "benchmark": "equal_weight_24_stock_research_universe", "metrics": asdict(system.metrics),
        "forecasts": forecasts,
        "qualification": "BUY requires >=60% outperformance probability, >=0.4% expected excess return, <=20% downside probability, and validated direction precision >=60%.",
        "feature_count": len(EXTENDED_FEATURE_COLUMNS), "feature_manifest": feature_manifest(),
        "training_schema": ["date", "symbol"] + EXTENDED_FEATURE_COLUMNS + TARGET_COLUMNS,
        "warning": "Research only. Benchmark has survivorship bias and is not KSE-100.",
    }
    output = Path("research/three_model_report.json")
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    system.save(Path("research/model_artifacts"))
    print(json.dumps({"metrics": report["metrics"], "top_forecasts": forecasts[:5], "report": str(output)}, indent=2))


if __name__ == "__main__":
    from dataclasses import asdict
    main()
