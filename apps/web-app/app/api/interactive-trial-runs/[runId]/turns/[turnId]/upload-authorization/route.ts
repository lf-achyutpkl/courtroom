import { NextRequest, NextResponse } from "next/server";
import { buildApiServiceUrl } from "@/lib/api-service";

export async function POST(request: NextRequest, { params }: { params: Promise<{ runId: string; turnId: string }> }) {
  const { runId, turnId } = await params;
  const response = await fetch(buildApiServiceUrl(`/interactive-trial-runs/${runId}/turns/${turnId}/upload-authorization`), {
    method: "POST", headers: { "Content-Type": request.headers.get("content-type") ?? "application/json" }, body: await request.text(), cache: "no-store",
  });
  return NextResponse.json(await response.json(), { status: response.status });
}
