type TranscriptTurn = { scene?: string; speaker_id?: string; text?: string };

export function LiveProceedingTranscript({ turns }: { turns: TranscriptTurn[] }) {
  return (
    <section className="interactive-trial__transcript" aria-label="Live proceeding transcript" aria-live="polite">
      <h2>Live proceeding</h2>
      {turns.length ? [...turns].reverse().map((turn, index) => (
        <article className="interactive-trial__transcript-turn" key={`${turn.speaker_id}-${turn.scene}-${turn.text}-${index}`}>
          <p className="interactive-trial__speaker">{turn.speaker_id ?? turn.scene ?? "Court"}</p>
          <p>{turn.text}</p>
        </article>
      )) : <p className="interactive-trial__empty">The proceeding is preparing. New testimony will appear here.</p>}
    </section>
  );
}
