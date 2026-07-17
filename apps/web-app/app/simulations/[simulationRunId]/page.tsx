import { CourtroomPage } from "@/components/courtroom/courtroom-page";

type SimulationPlaybackPageProps = {
  params: Promise<{
    simulationRunId: string;
  }>;
};

export default async function SimulationPlaybackPage({
  params,
}: SimulationPlaybackPageProps) {
  const { simulationRunId } = await params;

  return <CourtroomPage simulationRunId={simulationRunId} />;
}
