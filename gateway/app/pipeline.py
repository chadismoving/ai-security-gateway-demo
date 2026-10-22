from __future__ import annotations

import time

from app.llm.base import LLMProvider
from app.logging.audit import AuditLogger
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    Classification,
    SecuritySignals,
    TimelineItem,
)
from app.policy.engine import PolicyEngine
from app.scanners.llama_guard import LlamaGuardClient


class SecurityPipeline:
    def __init__(
        self,
        *,
        guard: LlamaGuardClient,
        policy: PolicyEngine,
        llm: LLMProvider,
        audit: AuditLogger,
    ) -> None:
        self.guard = guard
        self.policy = policy
        self.llm = llm
        self.audit = audit

    async def process(self, chat_request: ChatRequest) -> ChatResponse:
        started = time.perf_counter()
        timeline = [TimelineItem(stage="Request received", elapsed_ms=0)]

        request_classification = await self.guard.classify(
            "request", chat_request.prompt, mode=chat_request.guardrail_mode
        )
        timeline.append(self._timeline("Llama Guard request classification complete", started))
        request_decision = self.policy.decide(
            direction="request",
            classification=request_classification,
        )
        timeline.append(self._timeline("Request policy decision", started))
        request_security = self._signals(request_classification)
        request_latency = self._elapsed_ms(started)
        request_event_id = self.audit.log(
            user=chat_request.user,
            direction="request",
            classification=request_classification,
            decision=request_decision,
            latency_ms=request_latency,
            request_content=chat_request.prompt,
            response_content=None,
        )

        if request_decision.action == "BLOCK":
            timeline.append(self._timeline("Request blocked", started))
            return ChatResponse(
                status="blocked",
                action="BLOCK",
                risk=request_decision.risk,
                response=None,
                reason=request_decision.reason,
                direction="request",
                request_security=request_security,
                request_decision=request_decision,
                event_id=request_event_id,
                latency_ms=self._elapsed_ms(started),
                timeline=timeline,
            )

        model_response = await self.llm.chat(
            chat_request.prompt,
            demo_scenario=chat_request.demo_scenario if chat_request.demo_mode else None,
            mode=chat_request.backend_llm_mode,
        )
        timeline.append(self._timeline("Model response received", started))

        response_classification = await self.guard.classify(
            "response", model_response, mode=chat_request.guardrail_mode
        )
        timeline.append(self._timeline("Llama Guard response classification complete", started))
        if (
            chat_request.demo_mode
            and chat_request.demo_scenario == "unsafe_response"
            and response_classification.classification != "unsafe"
        ):
            response_classification = Classification(
                classification="unsafe",
                category="unsafe_model_response",
                confidence=1.0,
                detector="demo_response_enforcement",
            )
            timeline.append(
                self._timeline("Unsafe response demo enforcement applied", started)
            )
        response_decision = self.policy.decide(
            direction="response",
            classification=response_classification,
        )
        response_security = self._signals(response_classification)

        delivered_response: str | None = model_response
        if response_decision.action == "BLOCK":
            delivered_response = None
            timeline.append(self._timeline("Model response blocked", started))
        else:
            timeline.append(self._timeline("Response released", started))

        response_event_id = self.audit.log(
            user=chat_request.user,
            direction="response",
            classification=response_classification,
            decision=response_decision,
            latency_ms=self._elapsed_ms(started),
            request_content=chat_request.prompt,
            response_content=model_response,
        )

        response_overrides = response_decision.action in {"BLOCK", "LOG"}
        final_decision = response_decision if response_overrides else request_decision
        final_direction = "response" if response_overrides else "request"
        is_blocked = response_decision.action == "BLOCK"
        return ChatResponse(
            status="blocked" if is_blocked else "success",
            action=final_decision.action,
            risk=final_decision.risk,
            response=delivered_response,
            raw_llm_response=model_response,
            reason=final_decision.reason,
            direction=final_direction,
            request_security=request_security,
            response_security=response_security,
            request_decision=request_decision,
            response_decision=response_decision,
            event_id=response_event_id if response_overrides else request_event_id,
            latency_ms=self._elapsed_ms(started),
            timeline=timeline,
        )

    @staticmethod
    def _signals(
        classification: Classification,
    ) -> SecuritySignals:
        return SecuritySignals(
            classification=classification.classification,
            category=classification.category,
            confidence=classification.confidence,
            detector=classification.detector,
        )

    @staticmethod
    def _elapsed_ms(started: float) -> int:
        return max(0, round((time.perf_counter() - started) * 1000))

    @classmethod
    def _timeline(cls, stage: str, started: float) -> TimelineItem:
        return TimelineItem(stage=stage, elapsed_ms=cls._elapsed_ms(started))
