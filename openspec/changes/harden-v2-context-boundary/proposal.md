## Why

The V2 intelligence engine needs a stronger package boundary before expanding case intelligence and graph execution. Actor contexts must be explicit projections rather than canonical case models with fields removed after the fact.

## What Changes

- Split the V2 courtroom engine domain models into the planned domain package structure.
- Add DTO-only actor context projections for model-backed nodes.
- Add audit records for every built context.
- Move visibility and action policy decisions into the access policy package.
- Add regression coverage for context leakage and canonical model exposure.

## Non-Goals

- No frontend changes.
- No FastAPI, RQ, or worker changes.
- No V1 graph changes.
- No expansion of the V2 graph beyond keeping the existing smoke path working.
