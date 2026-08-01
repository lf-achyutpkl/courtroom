# Prompt Runtime

`apps/agent-service-v2` owns the V2 prompt registry and OpenAI Responses adapter.

## Prompt structure

- Keep stable prompt instructions in the developer block.
- Keep dynamic case/runtime context in the later user block.
- Build prompts only through `build_prompt_bundle(...)`.

## GPT-5.6 caching

- V2 uses explicit GPT-5.6 cache breakpoints.
- The developer `input_text` block is the stable cached prefix and carries `prompt_cache_breakpoint: {"mode": "explicit"}`.
- Requests set `prompt_cache_options` to `{"mode": "explicit", "ttl": "30m"}`.
- Requests set `prompt_cache_key` from prompt library version, prompt ID, prompt version, and model tier. An optional normalized cache scope can be appended later to partition high-volume traffic without changing the stable prefix contract.
- Dynamic runtime context is intentionally outside the cached prefix.

## Response detail

- `PromptSpec.text_verbosity` is sent to the Responses API as `text.verbosity`.
- Prompt wording still controls task-specific structure and required content.
- `text.verbosity` controls the default detail level across requests.

## Runtime outcomes

Structured Outputs guarantee schema shape, not that the result is usable for the node.

- `success`: parsed output passes semantic validation.
- `insufficient_context`: parsed output is valid but explicitly indicates the node lacks enough grounded information.
- `refusal_or_unusable`: the provider refuses, no parsed output is returned, or semantic validation rejects the parsed output as operationally unusable.

The runtime parses first, then applies semantic validation. If the first parsed result is semantically fixable, the runtime may retry once using machine-generated validation feedback only. It must not add new substantive instructions during that retry.
