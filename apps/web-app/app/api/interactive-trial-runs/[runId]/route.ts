import { NextResponse } from "next/server";
import { buildApiServiceUrl } from "@/lib/api-service";

export async function GET(_: Request, { params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  const response = await fetch(buildApiServiceUrl(`/interactive-trial-runs/${runId}`), { cache: "no-store" });
  return NextResponse.json(await response.json(), { status: response.status });
}
