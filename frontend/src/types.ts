// Response shapes mirrored from the FastAPI backend (see api/schemas.py and
// schema/card.py). Kept minimal to what the UI consumes.

export interface DeckSummary {
  id: string;
  title: string;
  description: string;
  order: number;
  level: string;
  card_count: number;
}

export interface CardSummary {
  id: string;
  name: string;
  deck: string;
  difficulty: number;
  tags: string[];
  svg: string;
}

export interface DeckDetail extends DeckSummary {
  prerequisites: string[];
  cards: CardSummary[];
}

export interface Example {
  name: string;
  smiles: string;
  role?: string | null;
  chembl_id?: string | null;
  pubchem_cid?: number | null;
  wikidata_id?: string | null;
}

export interface ComputedProperties {
  formula: string;
  mol_weight: number;
  clogp: number;
  tpsa: number;
  h_donors: number;
  h_acceptors: number;
  rotatable_bonds: number;
  fraction_csp3: number;
  num_rings: number;
  num_aromatic_rings: number;
}

export interface CuratedProperties {
  typical_pka?: string | null;
  charge_at_ph7_4?: number | null;
  polarity?: "low" | "medium" | "high" | null;
  notes?: string | null;
}

export interface Provenance {
  field: string;
  source?: string | null;
  ref?: string | null;
  url?: string | null;
  retrieved?: string | null;
  license?: string | null;
}

export interface Reference {
  id: string;
  citation: string;
  url?: string | null;
}

export interface CardDetail extends CardSummary {
  aliases: string[];
  smarts: string;
  representative_smiles: string;
  relevance: string;
  properties: CuratedProperties;
  computed: ComputedProperties;
  examples: Example[];
  bioisosteres: string[];
  references: Reference[];
  provenance: Provenance[];
}
