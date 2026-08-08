import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ParticipantTurnCard } from "./participant-turn-card";

const commonProps = {
  hasRecording: false,
  isFinalQuestion: false,
  onDiscard: vi.fn(),
  onFinalQuestionChange: vi.fn(),
  onSkip: vi.fn(),
  onStart: vi.fn(),
  onStop: vi.fn(),
  onSubmit: vi.fn(),
  processing: false,
  recorderState: "idle" as const,
};

describe("ParticipantTurnCard", () => {
  it("shows question controls without an objection bypass", () => {
    render(
      <ParticipantTurnCard
        {...commonProps}
        turn={{
          turnId: "turn-1",
          scene: "question",
          attorneySide: "defense",
          context: {
            action: "question",
            instruction: "Ask the next question.",
            examinationPhase: "cross",
            witness: { name: "Ms. Chen", persona: "Repair lot manager" },
          },
        }}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "cross examination: Ms. Chen" }),
    ).toBeTruthy();
    expect(screen.getByLabelText(/final question/i)).toBeTruthy();
    expect(screen.queryByRole("button", { name: /no objection/i })).toBeNull();
  });

  it("shows the no-objection control only for an objection turn", () => {
    render(
      <ParticipantTurnCard
        {...commonProps}
        turn={{
          turnId: "turn-2",
          scene: "objection",
          attorneySide: "defense",
          context: { action: "objection", instruction: "Object or continue." },
        }}
      />,
    );

    expect(screen.getByRole("button", { name: "No objection — continue" })).toBeTruthy();
  });
});
