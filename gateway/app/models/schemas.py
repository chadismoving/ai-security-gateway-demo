from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


Direction = Literal["request", "response"]
Action = Literal["ALLOW", "BLOCK", "LOG"]
Risk = Literal["LOW", "MEDIUM", "HIGH"]
GuardrailMode = Literal["offline", "online", "local"]
BackendLLMMode = Literal["offline", "online", "local"]


class ChatRequest(BaseModel):
    user: str = Field(default="demo-user", min_length=1, max_length=100)
    prompt: str = Field(min_length=1, max_length=20_000)
    demo_mode: bool = False
    demo_scenario: Optional[
        Literal["normal", "prompt_attack", "unsafe_response"]
    ] = None
    guardrail_mode: GuardrailMode = "offline"
    backend_llm_mode: BackendLLMMode = "offline"


class Classification(BaseModel):
    classification: Literal["safe", "unsafe", "unavailable"]
    category: Optional[str] = None
    confidence: Optional[float] = None
    detector: str = "llama_guard"
    fallback: bool = False


class SecuritySignals(BaseModel):
    classification: Literal["safe", "unsafe", "unavailable"]
    category: Optional[str] = None
    confidence: Optional[float] = None
    detector: str = "llama_guard"


class PolicyDecision(BaseModel):
    risk: Risk
    action: Action
    reason: str
    policy: str
    detector: str


class TimelineItem(BaseModel):
    stage: str
    elapsed_ms: int


class ChatResponse(BaseModel):
    status: Literal["success", "blocked", "error"]
    action: Action
    risk: Risk
    response: Optional[str] = None
    raw_llm_response: Optional[str] = None
    reason: str
    direction: Direction
    request_security: SecuritySignals
    response_security: Optional[SecuritySignals] = None
    request_decision: PolicyDecision
    response_decision: Optional[PolicyDecision] = None
    event_id: Optional[int] = None
    latency_ms: int
    timeline: list[TimelineItem] = Field(default_factory=list)


class SecurityEvent(BaseModel):
    id: int
    timestamp: str
    user: str
    direction: str
    classification: str
    category: Optional[str]
    risk: str
    action: str
    reason: str
    detector: str
    latency_ms: int
    request_preview: Optional[str]
    response_preview: Optional[str]
