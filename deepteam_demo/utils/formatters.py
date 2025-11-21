"""Output formatters for red teaming results."""

from typing import Dict, Any
from deepteam.red_teamer.risk_assessment import RiskAssessment
from deepteam.test_case import RTTestCase


def format_risk_assessment_summary(risk_assessment: RiskAssessment) -> str:
    """Format risk assessment as a summary string.
    
    Args:
        risk_assessment: RiskAssessment object
        
    Returns:
        Formatted summary string
    """
    overview = risk_assessment.overview
    
    total_passing = sum(r.passing for r in overview.vulnerability_type_results)
    total_failing = sum(r.failing for r in overview.vulnerability_type_results)
    total_errored = overview.errored
    total_test_cases = total_passing + total_failing + total_errored
    overall_pass_rate = (
        total_passing / total_test_cases if total_test_cases > 0 else 0.0
    )
    
    return (
        f"Pass Rate: {overall_pass_rate:.1%} | "
        f"Total: {total_test_cases} | "
        f"Passing: {total_passing} | "
        f"Failing: {total_failing} | "
        f"Errored: {total_errored}"
    )


def format_test_case(test_case: RTTestCase) -> Dict[str, Any]:
    """Format a test case as a dictionary.
    
    Args:
        test_case: RTTestCase object
        
    Returns:
        Dictionary representation
    """
    return {
        "vulnerability": test_case.vulnerability,
        "vulnerability_type": str(test_case.vulnerability_type.value),
        "attack_method": test_case.attack_method,
        "input": test_case.input,
        "output": test_case.actual_output,
        "score": test_case.score,
        "reason": test_case.reason,
        "error": test_case.error,
    }

