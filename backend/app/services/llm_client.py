"""LLM Client — Wrapper around Claude API for investment analysis.

Handles:
- Prompt construction from EvidencePack
- API calls with caching and retries
- Response parsing into structured analysis
- Token tracking and cost estimation
- Different analysis modes (quick, deep, forecast)

Input: EvidencePack (structured facts)
Output: Structured analysis (bullish/bearish thesis, risks, catalysts)
"""

import logging
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLMAnalysisResult:
    """Structured analysis from LLM."""

    ticker: str
    overall_thesis: str  # "Bullish", "Bearish", "Neutral", "Mixed"
    confidence: float  # 0-100%
    bull_case: str  # Key bullish arguments
    bear_case: str  # Key bearish arguments
    key_catalysts: list  # Upcoming events that could move stock
    key_risks: list  # Major risks to thesis
    price_target_rationale: str  # Why this price target
    investment_rating: str  # "Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"
    time_horizon: str  # "3-6 months", "6-12 months", "1+ years"
    tokens_used: int  # Total tokens consumed
    cache_creation_tokens: int  # Tokens for creating cache
    cache_read_tokens: int  # Tokens read from cache

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "overall_thesis": self.overall_thesis,
            "confidence": self.confidence,
            "bull_case": self.bull_case,
            "bear_case": self.bear_case,
            "key_catalysts": self.key_catalysts,
            "key_risks": self.key_risks,
            "price_target_rationale": self.price_target_rationale,
            "investment_rating": self.investment_rating,
            "time_horizon": self.time_horizon,
            "tokens_used": self.tokens_used,
            "cache_creation_tokens": self.cache_creation_tokens,
            "cache_read_tokens": self.cache_read_tokens,
        }


class LLMClient:
    """Claude API wrapper for investment analysis."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-opus-5"):
        """Initialize LLM client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
        """
        import os
        from anthropic import Anthropic

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.client = Anthropic(api_key=self.api_key)
        self.logger = logging.getLogger(__name__)

    def analyze_quick(self, evidence_pack: "EvidencePack") -> Optional[LLMAnalysisResult]:
        """Quick analysis: 2-3 minute turnaround.

        Args:
            evidence_pack: Structured facts about company

        Returns:
            Analysis result or None on error
        """
        return self._analyze(evidence_pack, mode="quick")

    def analyze_deep(self, evidence_pack: "EvidencePack") -> Optional[LLMAnalysisResult]:
        """Deep analysis: comprehensive, multi-angle examination.

        Args:
            evidence_pack: Structured facts about company

        Returns:
            Analysis result or None on error
        """
        return self._analyze(evidence_pack, mode="deep")

    def analyze_forecast(self, evidence_pack: "EvidencePack", months: int = 12) -> Optional[LLMAnalysisResult]:
        """Forecast analysis: price and fundamental targets.

        Args:
            evidence_pack: Structured facts about company
            months: Forecast period (default 12 months)

        Returns:
            Analysis result or None on error
        """
        return self._analyze(evidence_pack, mode="forecast", context=f"{months}-month horizon")

    def _analyze(
        self,
        evidence_pack: "EvidencePack",
        mode: str = "quick",
        context: Optional[str] = None
    ) -> Optional[LLMAnalysisResult]:
        """Internal analysis method with retries.

        Args:
            evidence_pack: Structured facts
            mode: Analysis mode (quick, deep, forecast)
            context: Optional additional context

        Returns:
            Analysis result or None on error
        """
        try:
            # Build system prompt
            system_prompt = self._build_system_prompt(mode)

            # Build user prompt from evidence pack
            user_prompt = self._build_user_prompt(evidence_pack, mode, context)

            # Call Claude API with prompt caching
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
            )

            # Parse response
            analysis_text = response.content[0].text
            result = self._parse_analysis(evidence_pack.ticker, analysis_text)

            # Track token usage
            if hasattr(response, "usage"):
                result.tokens_used = response.usage.input_tokens + response.usage.output_tokens
                result.cache_creation_tokens = getattr(response.usage, "cache_creation_input_tokens", 0)
                result.cache_read_tokens = getattr(response.usage, "cache_read_input_tokens", 0)

            self.logger.info(f"Analyzed {evidence_pack.ticker}: {result.overall_thesis} (confidence {result.confidence}%)")
            return result

        except Exception as e:
            self.logger.error(f"Error analyzing {evidence_pack.ticker}: {e}")
            return None

    @staticmethod
    def _build_system_prompt(mode: str) -> str:
        """Build system prompt for analysis mode.

        Args:
            mode: Analysis mode

        Returns:
            System prompt
        """
        base_prompt = """You are an expert investment analyst specializing in Pakistani equities (PSX).

Your role is to analyze structured company data and provide investment recommendations.

Key principles:
1. Base analysis only on provided facts, never speculate
2. Distinguish between high-confidence and low-confidence signals
3. Consider both bull and bear cases objectively
4. Identify specific catalysts and risks with timelines
5. Rate confidence 0-100% based on data quality and signal strength
6. Provide actionable investment recommendations

Output format: JSON with keys: overall_thesis, confidence, bull_case, bear_case,
key_catalysts, key_risks, price_target_rationale, investment_rating, time_horizon"""

        if mode == "quick":
            return base_prompt + "\n\nQUICK ANALYSIS: Focus on 3-5 key signals only. Be concise."
        elif mode == "deep":
            return base_prompt + "\n\nDEEP ANALYSIS: Examine from multiple angles (financial, technical, macro, sentiment). Thorough."
        elif mode == "forecast":
            return base_prompt + "\n\nFORECAST ANALYSIS: Project future fundamentals and price targets. Include bull/base/bear scenarios."
        else:
            return base_prompt

    @staticmethod
    def _build_user_prompt(
        evidence_pack: "EvidencePack",
        mode: str,
        context: Optional[str] = None
    ) -> str:
        """Build user prompt from evidence pack.

        Args:
            evidence_pack: Structured facts
            mode: Analysis mode
            context: Optional context

        Returns:
            User prompt
        """
        narrative = evidence_pack.to_narrative()
        context_text = f"\n\nAdditional context: {context}" if context else ""

        return f"""Analyze the following company for investment purposes:

{narrative}

{context_text}

Provide a structured investment analysis. Be specific with numbers and reasoning."""

    @staticmethod
    def _parse_analysis(ticker: str, response_text: str) -> LLMAnalysisResult:
        """Parse LLM response into structured analysis.

        Args:
            ticker: Company ticker
            response_text: Raw LLM response

        Returns:
            Parsed analysis result
        """
        try:
            # Try to extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
            else:
                # Fall back to parsing key lines
                data = {}
                for line in response_text.split("\n"):
                    if "thesis:" in line.lower():
                        data["overall_thesis"] = line.split(":", 1)[1].strip()
                    elif "confidence:" in line.lower():
                        conf_str = line.split(":", 1)[1].strip().split("%")[0]
                        data["confidence"] = float(conf_str) if conf_str else 50.0

            # Build result with defaults
            result = LLMAnalysisResult(
                ticker=ticker,
                overall_thesis=data.get("overall_thesis", "Mixed"),
                confidence=float(data.get("confidence", 50.0)),
                bull_case=data.get("bull_case", "See analysis"),
                bear_case=data.get("bear_case", "See analysis"),
                key_catalysts=data.get("key_catalysts", []),
                key_risks=data.get("key_risks", []),
                price_target_rationale=data.get("price_target_rationale", ""),
                investment_rating=data.get("investment_rating", "Hold"),
                time_horizon=data.get("time_horizon", "6-12 months"),
                tokens_used=0,
                cache_creation_tokens=0,
                cache_read_tokens=0,
            )

            return result

        except Exception as e:
            logger.error(f"Error parsing analysis for {ticker}: {e}")
            # Return neutral default
            return LLMAnalysisResult(
                ticker=ticker,
                overall_thesis="Unable to analyze",
                confidence=0.0,
                bull_case="Analysis failed",
                bear_case="Analysis failed",
                key_catalysts=[],
                key_risks=[],
                price_target_rationale="",
                investment_rating="Hold",
                time_horizon="Unknown",
                tokens_used=0,
                cache_creation_tokens=0,
                cache_read_tokens=0,
            )

    def estimate_cost(self, evidence_pack_count: int = 1) -> Dict[str, float]:
        """Estimate API costs.

        Args:
            evidence_pack_count: Number of analyses to run

        Returns:
            Cost estimate dictionary
        """
        # Rough estimates (Claude 3.5 Sonnet pricing)
        input_tokens_per_analysis = 1500  # Evidence pack + prompt
        output_tokens_per_analysis = 500   # Analysis response
        cache_creation_tokens_per_analysis = 1500  # System prompt (cached)

        input_cost_per_mtok = 0.003  # $0.003 per million input tokens
        output_cost_per_mtok = 0.015  # $0.015 per million output tokens
        cache_creation_cost_per_mtok = 0.00375  # 25% of input cost for cache creation
        cache_read_cost_per_mtok = 0.0003  # 10% of input cost for cache reads

        # Assume 50% cache hit rate after first run
        first_run_input = input_tokens_per_analysis + cache_creation_tokens_per_analysis
        subsequent_runs_input = output_tokens_per_analysis + (cache_creation_tokens_per_analysis * 0.1)

        first_run_cost = (first_run_input / 1_000_000) * input_cost_per_mtok
        first_run_cost += (output_tokens_per_analysis / 1_000_000) * output_cost_per_mtok

        subsequent_run_cost = (subsequent_runs_input / 1_000_000) * cache_read_cost_per_mtok
        subsequent_run_cost += (output_tokens_per_analysis / 1_000_000) * output_cost_per_mtok

        total_cost = first_run_cost + (max(0, evidence_pack_count - 1) * subsequent_run_cost)

        return {
            "first_analysis_cost": first_run_cost,
            "subsequent_analysis_cost": subsequent_run_cost,
            "total_estimated_cost": total_cost,
            "analyses_counted": evidence_pack_count,
        }
