import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { InteractiveTrialPage } from "./interactive-trial-page";

vi.mock("@/hooks/use-audio-recorder", () => ({
  useAudioRecorder: () => ({
    clear: vi.fn(),
    errorMessage: null,
    recording: null,
    start: vi.fn(),
    state: "idle",
    stop: vi.fn(),
  }),
}));

vi.mock("@/hooks/use-case-file-catalog", () => ({
  useCaseFileCatalog: () => ({
    caseFiles: [
      {
        id: "case-1",
        case_file: {
          case_title: "Vehicle removal",
          witnesses: [
            { witness_id: "W1", name: "Ms. Chen", called_by: "prosecution" },
            { witness_id: "W2", name: "Jordan Vale", called_by: "defense" },
          ],
        },
      },
    ],
  }),
}));

describe("InteractiveTrialPage", () => {
  it("requires an eligible selected witness before starting a trial", () => {
    render(<InteractiveTrialPage />);

    const start = screen.getByRole("button", { name: "Start trial" });
    expect(start.hasAttribute("disabled")).toBe(true);

    fireEvent.change(screen.getByLabelText("Case file"), {
      target: { value: "case-1" },
    });
    expect(screen.getByLabelText("Jordan Vale")).toBeTruthy();

    fireEvent.click(screen.getByLabelText("Jordan Vale"));
    expect(start.hasAttribute("disabled")).toBe(false);
  });
});
