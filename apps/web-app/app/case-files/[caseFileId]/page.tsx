import { CaseFileEditorPage } from "@/components/case-editor/case-file-editor-page";

type CaseFileEditorRouteProps = {
  params: Promise<{
    caseFileId: string;
  }>;
};

export default async function CaseFileEditorRoute({ params }: CaseFileEditorRouteProps) {
  const { caseFileId } = await params;
  return <CaseFileEditorPage caseFileId={caseFileId} />;
}
