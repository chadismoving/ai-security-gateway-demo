from __future__ import annotations

from pathlib import Path

import yaml

from app.models.schemas import Classification, Direction, PolicyDecision


class PolicyEngine:
    """Converts Llama Guard classification signals into explainable enforcement."""

    def __init__(self, policy_path: Path) -> None:
        with policy_path.open(encoding="utf-8") as policy_file:
            config = yaml.safe_load(policy_file)
        self.policies: dict[str, dict[str, str]] = config["policies"]

    def decide(
        self,
        *,
        direction: Direction,
        classification: Classification,
    ) -> PolicyDecision:
        if classification.classification == "unsafe":
            policy_key = "unsafe_response" if direction == "response" else "prompt_violation"
            detector = classification.detector
        elif classification.classification == "unavailable":
            policy_key = "classifier_unavailable"
            detector = classification.detector
        else:
            policy_key = "normal"
            detector = classification.detector

        policy = self.policies[policy_key]
        return PolicyDecision(
            risk=policy["severity"].upper(),
            action=policy["action"].upper(),
            reason=policy["reason"],
            policy=policy["label"],
            detector=detector,
        )
