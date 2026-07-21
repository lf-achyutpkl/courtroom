import { NextRequest, NextResponse } from "next/server";

import { buildApiServiceUrl } from "@/lib/api-service";

export async function POST(request: NextRequest) {
  const bodyText = await request.text();
  const response = await fetch(buildApiServiceUrl("/start-simulation"), {
    method: "POST",
    headers: {
      "Content-Type": request.headers.get("content-type") ?? "application/json",
    },
    body: bodyText || undefined,
    cache: "no-store",
  });

  const payload = await response.json();
  return NextResponse.json(payload, { status: response.status });
}
