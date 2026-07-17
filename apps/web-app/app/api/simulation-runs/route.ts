import { NextResponse } from "next/server";

import { buildApiServiceUrl } from "@/lib/api-service";

export async function GET() {
  const response = await fetch(buildApiServiceUrl("/simulation-runs"), {
    cache: "no-store",
  });

  const payload = await response.json();
  return NextResponse.json(payload, { status: response.status });
}
