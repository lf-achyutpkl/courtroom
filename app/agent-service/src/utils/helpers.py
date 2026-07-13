# from __future__ import annotations

# from time import perf_counter

# from langchain_openai import ChatOpenAI
# from pydantic import BaseModel

# from court_simulation_studio.llms import (
#     DEBUG_GRAPH,
#     NODE_MAX_COMPLETION_TOKENS,
#     fast_llm,
# )
# from court_simulation_studio.types import (
#     CaseFile,
#     TranscriptTurn,
#     TrialState,
#     WitnessProfile,
# )


# def render_case_context(case_file: CaseFile) -> str:
#     evidence_lines = "\n".join(
#         f"- {e.evidence_id}: {e.description}" for e in case_file.evidence
#     )
#     facts_lines = "\n".join(f"- {fact}" for fact in case_file.disputed_facts)
#     return f"""CASE FILE
#     Case ID: {case_file.case_id}
#     Case type: {case_file.case_type}
#     Jurisdiction: {case_file.jurisdiction}
#     Charge/Claim: {case_file.charge_or_claim}
#     Parties: {case_file.parties}

#     Disputed facts:
#     {facts_lines}

#     Evidence on record:
#     {evidence_lines}"""


# def spoken_style_rules(max_sentences: int, role_hint: str) -> str:
#     return (
#         "This output will be used directly in the frontend/TTS transcript. "
#         f"Write it as spoken dialogue for {role_hint}. "
#         f"Keep it to at most {max_sentences} short sentences. "
#         "Every sentence must include at least one inline delivery tag in square brackets, "
#         "such as [steady], [firm], [measured], [tense], [frustrated], [quiet], or [somber]. "
#         "Use realistic emotional delivery, not exaggerated stage directions. "
#         "Do not describe actions outside the dialogue."
#     )


# def preview_text(text: str | None, limit: int = 120) -> str:
#     if not text:
#         return "-"
#     text = " ".join(text.split())
#     return text if len(text) <= limit else text[: limit - 3] + "..."


# def log_graph_event(node_name: str, state: TrialState | None = None, **extra) -> None:
#     if not DEBUG_GRAPH:
#         return
#     details: list[str] = []
#     if state is not None:
#         details.extend(
#             [
#                 f"witness={state.current_witness_id}",
#                 f"phase={state.examination_phase}",
#                 f"attorney={state.examining_attorney}",
#                 f"turn_count={state.turn_count}/{state.max_turns}",
#                 f"queue={state.witness_queue}",
#                 f"transcript_turns={len(state.current_witness_transcript)}",
#             ]
#         )
#     details.extend(f"{key}={value}" for key, value in extra.items())
#     print(f"[{node_name}] " + " | ".join(details))


# def log_llm_usage(node_name: str, raw_message, elapsed_ms: float) -> None:
#     usage = getattr(raw_message, "usage_metadata", None) or {}
#     response_metadata = getattr(raw_message, "response_metadata", None) or {}
#     token_usage = response_metadata.get("token_usage", {})
#     model_name = (
#         response_metadata.get("model_name")
#         or getattr(raw_message, "model_name", None)
#         or getattr(getattr(raw_message, "response_metadata", None), "model_name", None)
#     )
#     input_tokens = usage.get("input_tokens") or token_usage.get("prompt_tokens") or 0
#     output_tokens = (
#         usage.get("output_tokens") or token_usage.get("completion_tokens") or 0
#     )
#     total_tokens = (
#         usage.get("total_tokens")
#         or token_usage.get("total_tokens")
#         or (input_tokens + output_tokens)
#     )
#     input_details = usage.get("input_token_details") or {}
#     output_details = usage.get("output_token_details") or {}
#     cached_input_tokens = (
#         input_details.get("cache_read")
#         or input_details.get("cached_tokens")
#         or token_usage.get("prompt_tokens_details", {}).get("cached_tokens")
#         or 0
#     )
#     reasoning_output_tokens = (
#         output_details.get("reasoning")
#         or token_usage.get("completion_tokens_details", {}).get("reasoning_tokens")
#         or 0
#     )
#     finish_reason = (
#         response_metadata.get("finish_reason")
#         or token_usage.get("finish_reason")
#         or "-"
#     )
#     print(
#         "[llm_usage] "
#         f"node={node_name} | model={model_name or '-'} | latency_ms={elapsed_ms:.1f} | "
#         f"input={input_tokens} | cached_input={cached_input_tokens} | output={output_tokens} | "
#         f"reasoning_output={reasoning_output_tokens} | total={total_tokens} | finish_reason={finish_reason}"
#     )


# def format_recent_transcript(turns: list[TranscriptTurn], max_turns: int = 6) -> str:
#     recent_turns = turns[-max_turns:]
#     return "\n".join(
#         f"{turn.speaker_id}: {preview_text(turn.text, 220)}" for turn in recent_turns
#     )


# def format_recent_testimony(turns: list[TranscriptTurn], max_turns: int = 6) -> str:
#     testimony_turns = [turn for turn in turns if turn.scene in {"direct", "cross"}]
#     recent_turns = testimony_turns[-max_turns:]
#     return "\n".join(
#         f"[{turn.scene}] {turn.speaker_id}: {preview_text(turn.text, 220)}"
#         for turn in recent_turns
#     )


# def append_witness_turn(
#     state: TrialState, turn: TranscriptTurn
# ) -> list[TranscriptTurn]:
#     return state.current_witness_transcript + [turn]


# def current_phase_question_count(state: TrialState) -> int:
#     return sum(
#         1
#         for turn in state.current_witness_transcript
#         if turn.scene == state.examination_phase
#         and turn.speaker_id == state.examining_attorney
#     )


# def phase_complete_next_node(state: TrialState):
#     return "swap_to_cross" if state.examination_phase == "direct" else "__end__"


# def should_end_phase(state: TrialState) -> bool:
#     return (
#         state.attorney_is_done or current_phase_question_count(state) >= state.max_turns
#     )


# def invoke_structured(
#     system_prompt: str,
#     user_prompt: str,
#     schema: type[BaseModel],
#     llm: ChatOpenAI = fast_llm,
#     *,
#     state: TrialState | None = None,
#     node_name: str = "unknown",
# ) -> BaseModel:
#     log_graph_event(
#         f"invoke:{node_name}",
#         state,
#         schema=schema.__name__,
#         mode="live",
#         prompt=preview_text(user_prompt),
#     )
#     try:
#         max_completion_tokens = NODE_MAX_COMPLETION_TOKENS.get(node_name, 160)
#         structured_llm = llm.bind(
#             max_completion_tokens=max_completion_tokens
#         ).with_structured_output(schema, include_raw=True)
#         started_at = perf_counter()
#         response = structured_llm.invoke(
#             [
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": user_prompt},
#             ]
#         )
#         elapsed_ms = (perf_counter() - started_at) * 1000
#         if response.get("raw") is not None:
#             log_llm_usage(node_name, response["raw"], elapsed_ms)
#         if response.get("parsing_error") is not None:
#             raise response["parsing_error"]
#         result = response["parsed"]
#         log_graph_event(
#             f"invoke:{node_name}:result",
#             state,
#             result=preview_text(result.model_dump_json(), 160),
#         )
#         return result
#     except Exception as exc:
#         log_graph_event(
#             f"invoke:{node_name}:error",
#             state,
#             error=type(exc).__name__,
#             message=preview_text(str(exc), 160),
#         )
#         raise
