# LAYA router dataset — one review bundle (2,000 / 200 / 300)

Nothing in this bundle is accepted data or a training result. `human_reviewed` and
`accepted_for_training` are false on every row, and no model was fitted.

- `REVIEW_ROWS.jsonl` — every row: id, split, family, recipe group, proposed route, label source,
  full five-field runtime input, label reason, quality flags, critic view, provenance.
- `candidates/{train,dev,test}_candidates.jsonl` — the same rows split per file.
- `writer/` — raw generator output, assembled rows, per-request events and receipt.
- `critic/` — blind inputs, judgements and receipt. `PRIVATE_MAPPING.json` links packets to rows
  and was never shown to the critic.
- `failed_slots.jsonl` — every slot the generator failed to deliver, with its reason.
- `sources/` — plan, recipes, seed, policy, schema, generator prompt and the actual code used.
- `manifest.json` — counts, checks, hashes and disclosures. `REVIEW_SUMMARY.md` — the narrative.

Read `REVIEW_SUMMARY.md` first.
