import { NextRequest } from "next/server";

import { buildApiServiceUrl } from "@/lib/api-service";

type MessageRouteProps = {
  params: Promise<{
    caseFileId: string;
  }>;
};

export async function POST(request: NextRequest, { params }: MessageRouteProps) {
  const { caseFileId } = await params;
  const bodyText = await request.text();
  const response = await fetch(buildApiServiceUrl(`/case-files/${caseFileId}/messages`), {
    method: "POST",
    headers: {
      "Content-Type": request.headers.get("content-type") ?? "application/json",
    },
    body: bodyText,
    cache: "no-store",
  });

  return new Response(response.body, {
    status: response.status,
    headers: {
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
      "Content-Type": response.headers.get("content-type") ?? "text/event-stream",
      "x-vercel-ai-ui-message-stream":
        response.headers.get("x-vercel-ai-ui-message-stream") ?? "v1",
    },
  });
}
