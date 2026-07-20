import { NextResponse } from "next/server";

import { buildApiServiceUrl } from "@/lib/api-service";

type CaseFileRouteProps = {
  params: Promise<{
    caseFileId: string;
  }>;
};

export async function GET(_: Request, { params }: CaseFileRouteProps) {
  const { caseFileId } = await params;
  const response = await fetch(buildApiServiceUrl(`/case-files/${caseFileId}`), {
    cache: "no-store",
  });

  const payload = await response.json();
  return NextResponse.json(payload, { status: response.status });
}
