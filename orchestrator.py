import json
import sys
import os
from datetime import datetime, timezone

sys.path.append(".")

from core.state import CaseState
from agents.market_intelligence import run_market_intelligence
from agents.financial_analysis import run_financial_analysis
from agents.risk_intelligence import run_risk_intelligence
from agents.research_synthesis import run_research_synthesis
from agents.investment_committee import run_investment_committee


def run_athena_pipeline(ticker):
    """
    Main orchestrator. Runs all 5 agents in sequence against a case state.
    If any agent fails outright (exception), the case is marked failed but
    the partial state is still returned and saved - nothing is silently lost.
    """
    case = CaseState(ticker)

    try:
        case.set_stage("market_intelligence")
        mi_output = run_market_intelligence(case.ticker)
        case.record_agent_output("market_intelligence", mi_output)

        case.set_stage("financial_analysis")
        fa_output = run_financial_analysis(mi_output)
        case.record_agent_output("financial_analysis", fa_output)

        case.set_stage("risk_intelligence")
        risk_output = run_risk_intelligence(fa_output, mi_output)
        case.record_agent_output("risk_intelligence", risk_output)

        case.set_stage("research_synthesis")
        synthesis_output = run_research_synthesis(fa_output, risk_output, mi_output)
        case.record_agent_output("research_synthesis", synthesis_output)

        case.set_stage("investment_committee")
        committee_output = run_investment_committee(fa_output, risk_output, synthesis_output, mi_output)
        case.record_agent_output("investment_committee", committee_output)

        case.set_stage("awaiting_human_approval")
        case.status = "awaiting_approval"

    except Exception as e:
        case.record_failure(case.stage, str(e))

    return case


def save_case(case, output_dir="outputs"):
    """Saves the full case state as JSON for audit trail purposes."""
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/case_{case.ticker}_{case.case_id[:8]}.json"
    with open(filename, "w") as f:
        json.dump(case.to_dict(), f, indent=2, default=str)
    return filename


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"

    print(f"Running Athena pipeline for {ticker}...\n")
    case = run_athena_pipeline(ticker)

    filename = save_case(case)
    print(f"Case saved to: {filename}")
    print(f"Status: {case.status}")
    print(f"Stage: {case.stage}")
    print(f"Errors: {len(case.errors)}")

    if case.investment_committee:
        score = case.investment_committee.get("overall_score")
        classification = case.investment_committee.get("classification")
        print(f"\nOverall Score: {score}")
        print(f"Classification: {classification}")
        print(f"\nCommittee Summary:\n{case.investment_committee.get('committee_summary')}")