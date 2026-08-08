import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { InteractiveTrialVerdict } from "./interactive-trial-verdict";

describe("InteractiveTrialVerdict", () => {
  it("renders the structured verdict without raw result JSON", () => {
    render(
      <InteractiveTrialVerdict
        verdict={{
          outcome: "not guilty",
          reasoning: "The People did not prove intent beyond a reasonable doubt.",
          cited_chunk_ids: ["E1", "E2"],
        }}
      />,
    );

    expect(screen.getByRole("heading", { name: "not guilty" })).toBeTruthy();
    expect(screen.getByText(/did not prove intent/i)).toBeTruthy();
    expect(screen.getByText("Evidence cited: E1, E2")).toBeTruthy();
    expect(screen.queryByText(/full_trial_transcript/)).toBeNull();
  });
});
