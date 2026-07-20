"use client";

import type { UIMessage } from "ai";

import type { CaseEditResult } from "@/lib/case-files";

export type CaseEditorMessage = UIMessage<
  unknown,
  { "case-file-update": CaseEditResult }
>;
