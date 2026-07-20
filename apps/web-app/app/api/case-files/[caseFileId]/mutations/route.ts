import { NextRequest, NextResponse } from "next/server";

import { buildApiServiceUrl } from "@/lib/api-service";

type MutationRouteProps = {
  params: Promise<{
    caseFileId: string;
  }>;
};

export async function POST(request: NextRequest, { params }: MutationRouteProps) {
  const { caseFileId } = await params;
  const bodyText = await request.text();
  const response = await fetch(buildApiServiceUrl(`/case-files/${caseFileId}/mutations`), {
    method: "POST",
    headers: {
      "Content-Type": request.headers.get("content-type") ?? "application/json",
    },
    body: bodyText,
    cache: "no-store",
  });

  const payload = await response.json();
  return NextResponse.json(payload, { status: response.status });
}
