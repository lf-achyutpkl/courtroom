"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { LiveProceedingTranscript } from "@/components/interactive-trial/live-proceeding-transcript";
import { ParticipantTurnCard } from "@/components/interactive-trial/participant-turn-card";
import { InteractiveTrialVerdict } from "@/components/interactive-trial/interactive-trial-verdict";
import { useAudioRecorder } from "@/hooks/use-audio-recorder";
import { useCaseFileCatalog } from "@/hooks/use-case-file-catalog";

type Run = {
  interactiveTrialRunId: string; status: string; transcript: { scene?: string; speaker_id?: string; text?: string }[];
  liveTranscript: { scene?: string; speaker_id?: string; text?: string }[];
  result?: { verdict?: { outcome?: string; reasoning?: string; cited_chunk_ids?: string[] } };
  errorMessage?: string;
  pendingHumanTurn?: { turnId: string; scene: string; attorneySide: string; context: { action: "opening" | "closing" | "question" | "objection"; instruction: string; examinationPhase?: string; witness?: { name: string; persona: string } } };
};

export function InteractiveTrialPage() {
  const { caseFiles } = useCaseFileCatalog();
  const recorder = useAudioRecorder();
  const [caseFileId, setCaseFileId] = useState("");
  const [side, setSide] = useState<"defense" | "prosecution">("defense");
  const [witnessPlan, setWitnessPlan] = useState<string[]>([]);
  const [run, setRun] = useState<Run | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [submittedTurnId, setSubmittedTurnId] = useState<string | null>(null);
  const [isFinalQuestion, setIsFinalQuestion] = useState(false);
  const selectedCase = useMemo(() => caseFiles.find((item) => item.id === caseFileId)?.case_file, [caseFileId, caseFiles]);
  const eligibleWitnesses = useMemo(
    () => selectedCase?.witnesses.filter((witness) => witness.called_by === side) ?? [],
    [selectedCase, side],
  );

  const refresh = useCallback(async () => { if (!run) return; const response = await fetch(`/api/interactive-trial-runs/${run.interactiveTrialRunId}`, { cache: "no-store" }); if (response.ok) setRun(await response.json()); }, [run]);
  useEffect(() => { if (!run || ["completed", "failed"].includes(run.status)) return; const timer = window.setInterval(() => void refresh(), 2000); return () => window.clearInterval(timer); }, [refresh, run]);

  const create = async () => {
    if (!caseFileId || !witnessPlan.length) return;
    setMessage(null);
    const response = await fetch("/api/interactive-trial-runs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ case_file_id: caseFileId, human_attorney_side: side, human_witness_plan: witnessPlan }) });
    if (!response.ok) { setMessage("Unable to start trial. Check the selected witness plan."); return; }
    recorder.clear(); setSubmittedTurnId(null); setRun(await response.json());
  };
  const submit = async () => {
    const turn = run?.pendingHumanTurn;
    if (!turn || !recorder.recording || submittedTurnId === turn.turnId) return;
    const contentType = recorder.recording.type.split(";", 1)[0].trim().toLowerCase();
    try {
      const auth = await fetch(`/api/interactive-trial-runs/${run.interactiveTrialRunId}/turns/${turn.turnId}/upload-authorization`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content_type: contentType }) });
      if (!auth.ok) throw new Error("authorization");
      const authorization = await auth.json() as { uploadUrl: string; requiredHeaders: Record<string, string> };
      const upload = await fetch(authorization.uploadUrl, { method: "PUT", headers: authorization.requiredHeaders, body: recorder.recording });
      if (!upload.ok) throw new Error("upload");
      const response = await fetch(`/api/interactive-trial-runs/${run.interactiveTrialRunId}/turns/${turn.turnId}/submit`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ object: true, ...(turn.context.action === "question" ? { is_final: isFinalQuestion } : {}) }) });
      if (!response.ok) throw new Error("submit");
      setSubmittedTurnId(turn.turnId); setIsFinalQuestion(false); recorder.clear(); await refresh();
    } catch { setMessage("Your recording could not be submitted. Please try again."); }
  };
  const skipObjection = async () => { const turn = run?.pendingHumanTurn; if (!turn) return; const response = await fetch(`/api/interactive-trial-runs/${run.interactiveTrialRunId}/turns/${turn.turnId}/submit`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ object: false }) }); if (response.ok) { setSubmittedTurnId(turn.turnId); recorder.clear(); await refresh(); } };
  const toggleWitness = (id: string) => setWitnessPlan((plan) => plan.includes(id) ? plan.filter((item) => item !== id) : [...plan, id]);
  const activeTurn = run?.pendingHumanTurn;
  const verdict = run?.result?.verdict;
  return <main className="interactive-trial"><header className="interactive-trial__header"><p className="interactive-trial__eyebrow">Live proceeding</p><h1>AI-vs-human trial</h1><p>Choose your witnesses, then guide your side through the proceeding.</p></header>
    {!run ? <section className="interactive-trial__setup"><label>Case file<select value={caseFileId} onChange={(event) => { setCaseFileId(event.target.value); setWitnessPlan([]); }}><option value="">Choose a case</option>{caseFiles.map((item) => <option key={item.id} value={item.id}>{item.case_file.case_title}</option>)}</select></label><label>Your side<select value={side} onChange={(event) => { setSide(event.target.value as "defense" | "prosecution"); setWitnessPlan([]); }}><option value="defense">Defense</option><option value="prosecution">Prosecution</option></select></label>
      <fieldset className="interactive-trial__witnesses"><legend>Your witnesses, in examination order</legend>{caseFileId && !eligibleWitnesses.length && <p className="interactive-trial__empty">This case has no witnesses assigned to your side. Assign one in the case editor before starting.</p>}{eligibleWitnesses.map((witness) => <label key={witness.witness_id}><input type="checkbox" checked={witnessPlan.includes(witness.witness_id)} onChange={() => toggleWitness(witness.witness_id)} />{witnessPlan.includes(witness.witness_id) ? `${witnessPlan.indexOf(witness.witness_id) + 1}. ` : ""}{witness.name}</label>)}</fieldset><button className="interactive-trial__button interactive-trial__button--primary" disabled={!caseFileId || !witnessPlan.length} onClick={() => void create()}>Start trial</button></section>
    : <section className="interactive-trial__proceeding"><div className="interactive-trial__status"><span className={`interactive-trial__status-dot interactive-trial__status-dot--${run.status}`} /><span>{run.status.replaceAll("_", " ")}</span></div>{activeTurn && <ParticipantTurnCard turn={activeTurn} recorderState={recorder.state} hasRecording={Boolean(recorder.recording)} processing={submittedTurnId === activeTurn.turnId} isFinalQuestion={isFinalQuestion} onFinalQuestionChange={setIsFinalQuestion} onStart={() => void recorder.start()} onStop={recorder.stop} onSubmit={() => void submit()} onSkip={() => void skipObjection()} onDiscard={recorder.clear} />}<LiveProceedingTranscript turns={run.liveTranscript ?? run.transcript} />{verdict && <InteractiveTrialVerdict verdict={verdict} />}</section>}
    {message && <p role="alert">{message}</p>}{recorder.errorMessage && <p role="alert">{recorder.errorMessage}</p>}</main>;
}
