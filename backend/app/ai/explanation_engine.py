"""Concise deterministic recommendation explanations grounded in actual matches."""

from __future__ import annotations

from app.ai.ranking_engine import RankedGame


class RecommendationExplanationEngine:
    def explain(self, ranked: RankedGame) -> str:
        reasons = [self._render(item) for item in ranked.matched_attributes[:4]]
        if not reasons:
            return "Recommended because its overall description is semantically similar to your request."
        if len(reasons) == 1:
            joined = reasons[0]
        elif len(reasons) == 2:
            joined = f"{reasons[0]} and {reasons[1]}"
        else:
            joined = f"{', '.join(reasons[:-1])}, and {reasons[-1]}"
        return f"Recommended because it {joined}."

    @staticmethod
    def _render(match: str) -> str:
        category, value = match.split(":", 1)
        templates = {
            "genre": f"matches the {value} genre",
            "platform": f"supports {value}",
            "mode": f"supports {value}",
            "theme": f"includes the {value} theme",
            "mood": f"has a {value} mood",
            "price": f"is {value}",
            "difficulty": f"matches {value} difficulty",
            "hardware": f"matches {value} hardware",
        }
        return templates[category]
