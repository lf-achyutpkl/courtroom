type Verdict = {
  outcome?: string;
  reasoning?: string;
  cited_chunk_ids?: string[];
};

export function InteractiveTrialVerdict({ verdict }: { verdict: Verdict }) {
  return (
    <section className="interactive-trial__verdict" aria-label="Trial verdict">
      <p className="interactive-trial__eyebrow">Verdict</p>
      {verdict.outcome && <h2>{verdict.outcome}</h2>}
      {verdict.reasoning && <p>{verdict.reasoning}</p>}
      {verdict.cited_chunk_ids?.length ? (
        <p className="interactive-trial__verdict-citations">
          Evidence cited: {verdict.cited_chunk_ids.join(", ")}
        </p>
      ) : null}
    </section>
  );
}
