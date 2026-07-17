import { NextResponse } from "next/server";

import { buildApiServiceUrl } from "@/lib/api-service";

type RouteContext = {
  params: Promise<{
    simulationRunId: string;
  }>;
};

export async function GET(_: Request, context: RouteContext) {
  const { simulationRunId } = await context.params;
  const response = await fetch(
    buildApiServiceUrl(`/simulation-runs/${simulationRunId}/playback`),
    {
      cache: "no-store",
    },
  );

  const payload = await response.json();
  return NextResponse.json(payload, { status: response.status });
}
