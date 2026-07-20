import type { CardDetail } from "../types";

const CHARGE_LABEL: Record<string, string> = { "-1": "−1 (anionic)", "1": "+1 (cationic)", "0": "neutral" };

export function CardDetailView({ card }: { card: CardDetail }) {
  const c = card.computed;
  const p = card.properties;
  return (
    <>
      <h2 className="card-name">{card.name}</h2>
      {card.aliases.length > 0 && <div className="aliases">{card.aliases.join(", ")}</div>}
      <p className="relevance">{card.relevance}</p>

      <div className="section-title">Properties</div>
      <div className="props">
        <span className="k">Formula</span>
        <span>{c.formula}</span>
        <span className="k">Mol. weight</span>
        <span>{c.mol_weight} g/mol</span>
        <span className="k">cLogP</span>
        <span>{c.clogp}</span>
        <span className="k">TPSA</span>
        <span>{c.tpsa} Å²</span>
        <span className="k">H-bond D / A</span>
        <span>
          {c.h_donors} / {c.h_acceptors}
        </span>
        {p.typical_pka && (
          <>
            <span className="k">Typical pKa</span>
            <span>{p.typical_pka}</span>
          </>
        )}
        {p.charge_at_ph7_4 != null && (
          <>
            <span className="k">Charge @ pH 7.4</span>
            <span>{CHARGE_LABEL[String(p.charge_at_ph7_4)] ?? p.charge_at_ph7_4}</span>
          </>
        )}
        {p.polarity && (
          <>
            <span className="k">Polarity</span>
            <span>{p.polarity}</span>
          </>
        )}
      </div>

      {card.examples.length > 0 && (
        <>
          <div className="section-title">Example molecules</div>
          <ul className="examples">
            {card.examples.map((e) => (
              <li key={e.name}>
                {e.name}
                {e.role && <span className="role"> — {e.role}</span>}
              </li>
            ))}
          </ul>
        </>
      )}

      {card.tags.length > 0 && (
        <>
          <div className="section-title">Tags</div>
          <div className="chips">
            {card.tags.map((t) => (
              <span key={t} className="chip">
                {t}
              </span>
            ))}
          </div>
        </>
      )}

      {card.provenance.length > 0 && (
        <div className="provenance">
          Sources: {sourcesLine(card)}
        </div>
      )}
    </>
  );
}

function sourcesLine(card: CardDetail): string {
  const refs = new Map(card.references.map((r) => [r.id, r.citation]));
  const seen = new Set<string>();
  const parts: string[] = [];
  for (const pr of card.provenance) {
    const label = pr.source ?? (pr.ref ? (refs.get(pr.ref) ?? pr.ref) : null);
    if (label && !seen.has(label)) {
      seen.add(label);
      parts.push(label);
    }
  }
  return parts.join("; ");
}
