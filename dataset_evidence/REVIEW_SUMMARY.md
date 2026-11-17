# Review bundle: 2,000 / 200 / 300 synthetic LAYA rows

Status: raw candidates, AI-reviewed only, **not accepted**, **nothing fitted** and **no human review**.

## Counts

| split | rows | BASE | DEEPFAKE | context rows | families | max variants |
|---|---|---|---|---|---|---|
| train | 2000 | 1120 | 880 | 805 | 670 | 4 |
| dev | 200 | 120 | 80 | 80 | 70 | 4 |
| test | 300 | 180 | 120 | 120 | 105 | 4 |

Train includes 100 curated Batch-100 rows (all train-reserved).

## Checks that passed

- Exact sizes, exact dev/test class mixes (120/80, 180/120).
- Train mix is 1120 BASE / 880 DEEPFAKE against the 1200/800 target: 80 rows (4 points) short on BASE. The deviation is left in place because every label follows a code-owned condition; it was not corrected by relabelling rows or by adding twin families whose two variants would share one assistant turn and one state.
- 670 train / 70 dev / 105 test families, at most four variants per family.
- No family appears in two splits; no message+history combination spans splits; dev and test share no message text.
- Every input validates against `input_schema.json`. Generated pair rows carry exactly one user turn and one code-owned assistant turn before a separate neutral current message; five curated seed rows keep their longer reviewed four-turn history.
- Shared dialogue (another row with the same message and history text): 130 rows, of which 114 are generated pairs, 16 singles, and 0 sit inside their own family. Scenes, states and labels remain independent, and no message text is shared between dev and test.
- 12 first-pass generator slots failed their text checks; `failed_slots.jsonl` lists each with its reason and `writer/retry_receipt.json` shows all of them re-sampled and recovered with a fresh seed, so no row is missing and none was written by hand.

## Critic coverage

{
  "rows": 1200,
  "dev": 200,
  "test": 300,
  "train_sample": 600,
  "curated_seeds": 100
}

## Agreement (reported, not gated)

| split | critic views | critic disagreements | critic ambiguous | writer readback disagreements |
|---|---|---|---|---|
| train | 700 | 95 | 14 | 0 |
| dev | 200 | 16 | 1 | 0 |
| test | 300 | 18 | 6 | 0 |

## Disclosures

- Every row is template-assisted: scenario catalogue, state, code-owned assistant turn, operative offer and neutral current message are code; the pinned generator wrote only the user request text.
- human_reviewed is false everywhere; Codex inspection is AI adjudication.
- accepted_for_training is false everywhere; nothing was fitted.
- Curated seed rows reuse the Batch-100 reviewed material and were not regenerated; their earlier curation is preserved verbatim.
- Writer readback is the generator reading its own row, not a blind check; it agreed with the condition on every row, so it carries no independent evidence.
- The critic is a fallible blind opinion, not a label; its agreement is not used as a gate and no threshold was introduced.
- Critic coverage is disclosed per split: dev/test fully, train sampled plus all curated seeds.
- 12 of 2,400 generated slots failed first-pass text checks (user speaking as the assistant, or repeating the fixed current message); each was re-sampled once with a fresh seed, all 12 recovered, and every replacement records the slot it replaced in provenance. No slot was synthesised by hand.

## Measured time

```
{
  "generation_requests": 300,
  "generation_wall_seconds": 3939.1,
  "generation_eval_tokens": 91182,
  "critic_requests": 1200,
  "critic_wall_seconds": 5145.0
}
```

## Files

Every file with its SHA-256 is in `manifest.json`.
