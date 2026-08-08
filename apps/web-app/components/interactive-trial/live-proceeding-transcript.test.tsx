import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LiveProceedingTranscript } from "./live-proceeding-transcript";

describe("LiveProceedingTranscript", () => {
  it("shows the most recent transcript turn first", () => {
    const { container } = render(
      <LiveProceedingTranscript
        turns={[
          { scene: "cross", speaker_id: "prosecution", text: "Where were you?" },
          { scene: "cross", speaker_id: "W2", text: "At the repair lot." },
        ]}
      />,
    );

    expect(screen.getByText("Where were you?")).toBeTruthy();
    expect(screen.getByText("At the repair lot.")).toBeTruthy();
    expect(
      [...container.querySelectorAll<HTMLElement>(".interactive-trial__transcript-turn")]
        .map((turn) => turn.textContent),
    ).toEqual(["W2At the repair lot.", "prosecutionWhere were you?"]);
  });
});
