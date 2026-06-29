from datetime import datetime, timezone
import uuid


class CaseState:
    """
    Central state object for one Athena analysis case.
    Tracks every agent's output, timestamps, and the full audit trail.
    This is what gets logged and what UiPath Maestro Case will track as
    the case moves through stages.
    """

    def __init__(self, ticker):
        self.case_id = str(uuid.uuid4())
        self.ticker = ticker.upper().strip()
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.status = "initiated"
        self.stage = "intake"

        self.market_intelligence = None
        self.financial_analysis = None
        self.risk_intelligence = None
        self.research_synthesis = None
        self.investment_committee = None

        self.audit_log = []
        self.human_decision = None
        self.errors = []

        self._log_event("case_created", {"ticker": self.ticker})

    def _log_event(self, event_type, details=None):
        self.audit_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "details": details or {}
        })

    def set_stage(self, stage_name):
        self.stage = stage_name
        self._log_event("stage_change", {"stage": stage_name})

    def record_agent_output(self, agent_name, output):
        setattr(self, agent_name, output)
        agent_errors = output.get("data_quality", {}).get("errors", []) if output else []
        self._log_event(f"{agent_name}_complete", {
            "errors": agent_errors,
            "had_errors": len(agent_errors) > 0
        })
        if agent_errors:
            self.errors.extend([f"[{agent_name}] {e}" for e in agent_errors])

    def record_failure(self, agent_name, error_message):
        self._log_event(f"{agent_name}_failed", {"error": error_message})
        self.errors.append(f"[{agent_name}] FAILED: {error_message}")
        self.status = "failed"

    def set_human_decision(self, decision, notes=""):
        """decision should be 'approved', 'rejected', or 'escalated'"""
        self.human_decision = {
            "decision": decision,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.status = decision
        self._log_event("human_decision_recorded", {"decision": decision, "notes": notes})

    def to_dict(self):
        return {
            "case_id": self.case_id,
            "ticker": self.ticker,
            "created_at": self.created_at,
            "status": self.status,
            "stage": self.stage,
            "market_intelligence": self.market_intelligence,
            "financial_analysis": self.financial_analysis,
            "risk_intelligence": self.risk_intelligence,
            "research_synthesis": self.research_synthesis,
            "investment_committee": self.investment_committee,
            "human_decision": self.human_decision,
            "errors": self.errors,
            "audit_log": self.audit_log
        }