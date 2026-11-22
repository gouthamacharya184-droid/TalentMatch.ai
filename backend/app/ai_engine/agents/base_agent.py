import logging
import re

from sqlalchemy.orm import Session

from app.ai_engine.llm_service import LLMService
from app.models.all_models import AgentExecution, generate_uuid, utc_now

logger = logging.getLogger(__name__)


class BaseAgent:
    """
    Foundational class for all stateful AI recruitment agents.
    Provides execution tracing, prompt injection neutralization, token tracking,
    and automatic deterministic fallback execution.
    """

    def __init__(self, agent_name: str, description: str):
        self.agent_name = agent_name
        self.description = description
        self.llm_service = LLMService()

    def sanitize_untrusted_input(self, text: str, max_chars: int = 15000) -> str:
        """
        Sanitize untrusted user/document inputs before passing to prompt contexts.
        Defends against prompt injection, instruction override, and secret extraction attacks.
        """
        if not text:
            return ""

        # 1. Truncate oversized text to prevent token flooding
        cleaned = text[:max_chars]

        # 2. Defang adversarial prompt injection patterns
        injection_patterns = [
            r"ignore\s+(all\s+)?(previous|prior)\s+instructions?",
            r"disregard\s+(all\s+)?(previous|prior)\s+instructions?",
            r"system\s*:\s*you\s+are\s+now",
            r"give\s+this\s+candidate\s+(a\s+)?100%",
            r"override\s+scoring",
            r"print\s+system\s+prompt",
            r"reveal\s+your\s+prompt",
            r"<\s*/?\s*system\s*>",
        ]
        for pat in injection_patterns:
            cleaned = re.sub(pat, "[FILTERED_SECURITY_DIRECTIVE]", cleaned, flags=re.IGNORECASE)

        return cleaned

    def frame_data(self, tag: str, content: str) -> str:
        """
        Wrap untrusted content in XML-style tags to clearly isolate
        data from instructions for the model.
        """
        sanitized = self.sanitize_untrusted_input(content)
        return f"<{tag}>\n{sanitized}\n</{tag}>"

    def record_execution(
        self,
        db: Session | None,
        task_name: str,
        target_entity_type: str | None,
        target_entity_id: str | None,
        status: str,
        duration_ms: int,
        tokens_used: int = 0,
        model_used: str | None = None,
        input_summary: str | None = None,
        output_summary: str | None = None,
        error_message: str | None = None,
    ) -> AgentExecution | None:
        """Record real agent telemetry directly into the database."""
        if not db:
            return None

        try:
            execution = AgentExecution(
                id=generate_uuid(),
                agent_name=self.agent_name,
                task_name=task_name,
                target_entity_type=target_entity_type,
                target_entity_id=target_entity_id,
                status=status,
                duration_ms=duration_ms,
                tokens_used=tokens_used,
                model_used=model_used or self.llm_service.model,
                input_summary=input_summary[:500] if input_summary else None,
                output_summary=output_summary[:500] if output_summary else None,
                error_message=error_message[:500] if error_message else None,
                created_at=utc_now(),
            )
            db.add(execution)
            db.commit()
            return execution
        except Exception as e:
            logger.warning(f"Failed to record agent execution log: {e}")
            try:
                db.rollback()
            except Exception:
                pass
            return None
