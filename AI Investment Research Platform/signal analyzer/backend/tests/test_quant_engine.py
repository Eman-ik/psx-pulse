import unittest
import numpy as np
import pandas as pd

from backend.quant_engine import FEATURE_COLUMNS, ModelConfig, SignalModel, build_features, synthetic_market, validate_prices
from backend.multi_model import ThreeModelSystem
from backend.feature_engine import EXTENDED_FEATURE_COLUMNS, build_panel_dataset
from backend.point_in_time import asof_join_features


class QuantEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prices = synthetic_market(days=800)

    def test_rejects_duplicate_observations(self):
        bad = pd.concat([self.prices, self.prices.iloc[[0]]])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_prices(bad)

    def test_features_use_past_and_labels_use_future(self):
        features = build_features(self.prices)
        row = features[features["symbol"] == "MARI"].dropna(subset=FEATURE_COLUMNS + ["target"]).iloc[100]
        symbol = self.prices[self.prices["symbol"] == "MARI"].reset_index(drop=True)
        idx = symbol.index[symbol["date"] == row["date"]][0]
        expected_5d = symbol.loc[idx, "close"] / symbol.loc[idx - 5, "close"] - 1
        self.assertAlmostEqual(row["return_5d"], expected_5d)

    def test_signal_gate_never_issues_unvalidated_trade(self):
        config = ModelConfig(min_train_days=252, test_days=63, embargo_days=5, minimum_validated_accuracy=0.99)
        model = SignalModel(config).fit(self.prices)
        self.assertTrue(all(x["signal"] in {"HOLD", "NO SIGNAL"} for x in model.rank(self.prices)))

    def test_probabilities_are_valid(self):
        model = SignalModel().fit(self.prices)
        values = [x["outperformance_probability"] for x in model.rank(self.prices)]
        self.assertTrue(all(0 <= x <= 1 for x in values))

    def test_three_model_forecast_contract(self):
        config = ModelConfig(min_train_days=252, test_days=63, embargo_days=5)
        system = ThreeModelSystem(config).fit(self.prices)
        forecasts = system.forecast(self.prices)
        self.assertTrue(forecasts)
        self.assertTrue(all(0 <= x["outperformance_probability"] <= 1 for x in forecasts))
        self.assertTrue(all(0 <= x["downside_probability"] <= 1 for x in forecasts))
        self.assertTrue(all(x["volatility_regime"] in {"LOW", "MEDIUM", "HIGH"} for x in forecasts))

    def test_relative_and_structure_features_are_in_panel(self):
        panel = build_panel_dataset(self.prices)
        required = {"sector_relative_20d", "market_relative_20d", "breakout_60d", "adx_14", "ema200_slope_5d"}
        self.assertTrue(required.issubset(EXTENDED_FEATURE_COLUMNS))
        self.assertTrue(required.issubset(panel.columns))

    def test_point_in_time_join_never_uses_future_fundamental(self):
        panel = pd.DataFrame({"date":["2026-01-10","2026-03-01"],"symbol":["FFC","FFC"]})
        external = pd.DataFrame({"ticker":["FFC"],"available_at":["2026-02-25"],"roe":[0.31]})
        joined = asof_join_features(panel, external, ["roe"])
        self.assertTrue(pd.isna(joined.iloc[0]["roe"]))
        self.assertEqual(joined.iloc[1]["roe"], 0.31)


if __name__ == "__main__":
    unittest.main()
