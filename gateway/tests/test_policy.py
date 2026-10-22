from app.models.schemas import Classification
from app.policy.engine import PolicyEngine


def test_policy_decisions_are_separate_from_detection(settings) -> None:
    policy = PolicyEngine(settings.policy_path)
    safe = Classification(classification="safe", confidence=0.99)
    unsafe = Classification(
        classification="unsafe", category="prompt_policy_violation", confidence=0.98
    )
    assert policy.decide(direction="request", classification=safe).action == "ALLOW"
    request_decision = policy.decide(direction="request", classification=unsafe)
    response_decision = policy.decide(direction="response", classification=unsafe)
    assert request_decision.action == "BLOCK"
    assert request_decision.policy == "PROMPT SECURITY"
    assert response_decision.action == "BLOCK"
    assert response_decision.policy == "RESPONSE SECURITY"
