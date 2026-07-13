from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

import logging

logger = logging.getLogger(__name__)

fast_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.9, max_retries=0)
judge_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, max_retries=0)

NODE_MAX_COMPLETION_TOKENS = {
    "plan_prosecution_strategy": 180,
    "plan_defense_strategy": 180,
    "opening_prosecution": 140,
    "opening_defense": 140,
    "ask_question": 90,
    "objection_check": 50,
    "witness_answer": 110,
    "judge_ruling": 120,
    "summarize_trial_transcript": 260,
    "closing_prosecution": 170,
    "closing_defense": 170,
    "verdict": 180,
}


def invoke_structured(
    system_prompt: str,
    user_prompt: str,
    schema: type[BaseModel],
    llm: ChatOpenAI = fast_llm,
    *,
    node_name: str = "unknown",
) -> BaseModel:
    try:
        max_completion_tokens = NODE_MAX_COMPLETION_TOKENS.get(node_name, 160)
        structured_llm = llm.bind(
            max_completion_tokens=max_completion_tokens
        ).with_structured_output(schema, include_raw=True)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = structured_llm.invoke(messages)

        parsing_error = response.get("parsing_error")
        if parsing_error:
            raise parsing_error

        return response["parsed"]

    except Exception as e:
        logger.exception(
            "Failed to invoke structured output for node '%s'",
            node_name,
        )
        raise
