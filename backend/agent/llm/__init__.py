'''LLM package for warranty agent system.'''

from agent.llm.gigachat_setup import (
    GigaChatManager,
    get_classifier_llm,
    get_repair_days_llm,
    get_compliance_llm,
    get_dealer_insights_llm,
    get_report_summary_llm,
)
from agent.llm.prompts import (
    get_classifier_prompt,
    get_repair_days_prompt,
    get_compliance_prompt,
    get_dealer_insights_prompt,
    get_report_summary_prompt,
)

__all__ = [
    'GigaChatManager',
    'get_classifier_llm',
    'get_repair_days_llm',
    'get_compliance_llm',
    'get_dealer_insights_llm',
    'get_report_summary_llm',
    'get_classifier_prompt',
    'get_repair_days_prompt',
    'get_compliance_prompt',
    'get_dealer_insights_prompt',
    'get_report_summary_prompt',
]
