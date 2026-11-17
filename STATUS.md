# Status

Handover prepared 16 November 2026. Round 1 executed, then repaired after Codex review, on the
same day. **Round 2 is not authorised. No training has run. No row is accepted.**

## Handover history (unchanged)

Fresh-machine clarification: transfer ONLY this ZIP. No SSD, Polyvalent repository, domain model,
earlier report or prior chat is assumed. The pack supplies the context. Implement standalone mocks,
download the specified public LAYA dependency/checkpoint, and return Round 1 evidence. Actual
application attachment is deferred.

Completed in the handover: project context, approved two-route boundary, sizing decision,
English-only language scope, category/size contract, state/schema/questions, synthesis and
blind-verification prompts, environment/runbook, reference training wrapper, runtime/integration
contract, 16 illustrative policy fixtures, offline validator/export/metric checks, Python syntax
checks. Not performed: synthesis, human labelling, hardware detection, weight download, training,
calibration, human-test scoring, app integration.

## Round 1 — original submission (superseded, preserved)

Environment, pinned SDK/checkpoint, simulation plumbing and 100 candidate rows were delivered and
reviewed. Codex decision: **ROUND 1 REPAIR REQUIRED** (`LAYA_Codex_Round_1_Review/DECISION.json`),
source archive `b2c8b076…`, 70 manifest entries verified, no human annotation implied.

The original pilot is preserved at `data/pilot/archive/train_pilot_r1_original.jsonl` and the
original capsule `LAYA_Return_Round_1_2026-11-16.zip` is untouched.

## Round 1 repair — completed stage (packaged, reviewed next)

**Stage: repair complete, packaged, stopped for Codex review. No Round 2, no synthesis, no
training.**

Checklist:

- [x] Preserved the environment, checkpoint and the original pilot/capsule.
- [x] Boundary: ambiguous positives replaced; date-provenance row removed; proof context made explicit.
- [x] 49 semantic families declared before variants (the 10 controlled pairs are the mixed-label
      families in the pilot), ≤4 variants each.
- [x] Full synthetic plan rebuilt on family archetypes at 4000/600/400, quotas exact.
- [x] 10 controlled minimal pairs (20 rows), same message and asset readiness, opposite labels.
- [x] 43 rows with written context_dependency_reason; history_present vs necessary separated.
- [x] Duplicate audit: asset-normalised, cross-family review regardless of label, cross-split hard fail.
- [x] Verifier merge: completeness, uniqueness, enum, boolean, key-set and identity validated.
- [x] Fresh blind packet built after repair, opaque IDs, frozen hash-bound private mapping.
- [x] Token audit on the real assembled sequence, `--model-dir` honoured, negative fixture fails.
- [x] Temperature and import claims corrected in ENVIRONMENT.md and IMPLEMENTATION_PLAN.md.
- [x] Coverage: upload-only, vague-with-image, unsupported image mode; no fabricated hardware claims.
- [x] 14/14 regression probes behave as required.
- [ ] Independent blind verification (must run in a different-family session).
- [ ] Human review of the 100 candidate rows.
- [ ] Codex decision on this repair capsule.

Key artefacts: `data/pilot/train_pilot_r1_repair.jsonl`,
`data/families/pilot_families_r1r.json`, `data/allocation/full_split_family_plan_r1_repair.json`,
`data/verifier_r1_repair/`, `reports/round1r_audit.json`, `reports/round1r_token_audit.json`,
`reports/regressions_r1_repair.json`, `reports/pilot_before_after_r1_repair.json`,
`reports/source_diff_r1_repair.patch`, `RETURN_SUMMARY_REPAIR.md`.

Pending human input: (1) blind verification by a different model family; (2) human review of the
100 rows; (3) Codex's decision. `provenance.verifier` is null, `verification_status` is `pending`
and `human_reviewed` is false for every row — no AI review is recorded as human annotation.

Audit history preserved: the original submission, the review decision and the repair are all kept.
No failed run was edited into a success; the strict-validator failure is documented as expected
while rows are pending.

## Local qualification 1 (LQ1) — completed stage (failed gate, archived)

**Stage: LQ1 finished with both candidates failing the qualification gate; stopped for Codex review.**
Hosted-model synthesis and the hosted verifier retry are superseded by this local transition; the
separate Solar project stays archived and untouched.

- [x] Pre-round hashes and the previous STATUS.md saved to `runs/local_q1/pre_round/`.
- [x] Existing environment, LAYA SDK/checkpoint receipts and the repaired pilot preserved
      (packet `a1ab11ec…` unchanged; all 20 pack hashes still match).
- [x] Ollama 0.40.15 reused as found; `qwen3:14b-q4_K_M` (9.28 GB) and `gemma3:12b-it-q4_K_M`
      (8.16 GB) pulled, digests and Q4_K_M/family verified from the server.
- [x] 24 fixtures run per candidate, sequently, temperature 0, seed 20261116, ctx 4096, JSON schema;
      Qwen with `think=false`; each unloaded and `/api/ps` checked before the next.
- [x] Mechanical audit: 48/48 valid, schema-clean, no duplicates, annotation-free payloads, 100 % GPU
      residency, peak 10,337 / 9,873 MiB.
- [ ] **Candidate gate: FAILED for both — 21/24 each**, two false DEEPFAKE activations each.
- [ ] Frozen-pilot review by both models — not run (gate requires both to pass).
- [ ] 20 synthesis probes — not run (Qwen did not qualify).
- [ ] Gemma probe review — nothing to review.
- [ ] Codex decision on LQ1 evidence.

Evidence: `runs/local_q1/RETURN_SUMMARY.md`, `runs/local_q1/audit/lq1_audit.json`,
`runs/local_q1/{qwen,gemma}_qualification/`, `runs/local_q1/*_peak.json`, `SOURCE_DIFF.patch`,
`LAYA_Return_Local_Qualification_1_2026-11-16.zip`. No LAYA training, inference or acceptance ran;
`human_reviewed` remains false everywhere.

## Local qualification 2 (LQ2) — completed stage (failed gate, archived)

**Stage: LQ2 finished with both larger candidates failing the 40-check gate; stopped for Codex review.**
Authorised by `LAYA_Local_Qualification_2/review/CODEX_DECISION.md` (LOCAL_QUALIFICATION_2_AUTHORISED).

- [x] Pack verified 27/27 before any change; offline `self_check.py` passed.
- [x] Preserved: repaired pilot `dcc608db…`, frozen packet `a1ab11ec…`, LQ1 capsule `c536fc31…`,
      repair capsule `a8c19e33…`, LAYA receipts and pinned weights (never loaded).
- [x] Pulled exactly `qwen3:32b-q4_K_M` (20.2 GB) and `gemma3:27b-it-q4_K_M` (17.41 GB); digests,
      family, parameter count, Q4_K_M and licences recorded from the server.
- [x] Both ran the 40 fixtures sequentially, temperature 0, seed 20261116, ctx 4096, JSON schema,
      Qwen `think=false`; each unloaded with `/api/ps` empty before the next.
- [x] Full GPU residency verified (40/40 calls, size == size_vram); peaks 21,210 / 18,972 MiB; no OOM,
      no CPU offload, no context truncation.
- [ ] **Gate: FAILED — Qwen3-32B 38/40 (24/24 corrected prior, 14/16 new); Gemma3-27B 37/40 (23/24, 14/16).**
- [ ] Frozen-pilot dual review — not run (needs both to pass).
- [ ] 20 raw synthesis probes — not run (needs Qwen to pass). Zero accepted examples.
- [ ] Gemma probe review — nothing generated.
- [ ] Codex decision on LQ2 evidence.

Evidence: `runs/local_q2/RETURN_SUMMARY.md`, `runs/local_q2/audit/lq2_audit.json`,
`runs/local_q2/{qwen,gemma}_qualification/`, `runs/local_q2/*_peak.json`, `SOURCE_DIFF.patch`,
`LAYA_Return_Local_Qualification_2_2026-11-16.zip`. No training, no LAYA inference, no merge;
`human_reviewed` remains false everywhere.

## Dataset pilot 1 — last completed stage

**Stage: 20 raw synthesis candidates generated and blind-critiqued; zero accepted; stopped for Codex.**

Authorised by `Dataset_Pilot_1/AUTHORISATION.md` (DATASET_PILOT_1_ONLY); no qualification retry.

- [x] Pack verified 19/19, offline self-check passed, model digests matched the pinned LQ2 values.
- [x] Qwen3-32B: 16/16 jobs valid, **20/20 raw slots**, first attempts only, no retries; 219.9 s,
      5,137 output tokens, peak 21,296 MiB, 16/16 calls fully GPU-resident.
- [x] Gemma3-27B blind critique: 20/20 valid, payloads only `{packet_id,input}`, 0 ambiguity flags;
      96.2 s, peak 18,968 MiB, 20/20 fully GPU-resident.
- [x] Mechanical audit: ID bijection, no duplicate requests, scored == raw responses, no annotation
      leakage; no exact duplicate states.
- [ ] Intended-vs-critic agreement 15/20 — not accuracy. Inspector reading: 3 synthesis/label defects
      (01_2, 03_2, 11_1) and 2 critic errors (04_1, 10_1).
- [ ] Structural defects preserved: family_02 messages differ (not a minimal pair); slot_16_1 claims a
      new image with one asset; slot_06/13 empty asset IDs.
- [ ] **Zero accepted examples.** No merge, no LAYA inference/training, no next round.

Evidence: `Dataset_Pilot_1/runs/RETURN_SUMMARY.md`, `Dataset_Pilot_1/runs/audit/pilot_audit.json`,
`Dataset_Pilot_1/runs/{qwen_probes,gemma_review}/`, `Dataset_Pilot_1/runs/PILOT_COMPARISON.json`,
`Dataset_Pilot_1/runs/*_peak*.json`, `LAYA_Return_Dataset_Pilot_1_2026-11-16.zip`.

## Dataset batch 100 — last completed stage

**Stage: 100 planned candidate slots generated under the code-owned-state contract and blind-critiqued;
93 usable, 7 preserved failures, zero accepted; stopped for Codex review.**

Authorised by `Dataset_Batch_100/AUTHORISATION.md` (DATASET_BATCH_100_ONLY); no qualification retry.

- [x] Pack verified 21/21; pre-round hashes and STATUS snapshot in `Dataset_Batch_100/runs/pre_round/`;
      earlier capsules and `Dataset_Pilot_1` untouched.
- [x] New contract implemented in `Dataset_Batch_100/tools/local_runner.py`: assets, active ID, stored
      analysis and pair messages are code-owned, Qwen writes dialogue only, model-supplied state or a
      model-supplied fixed message is a schema error; `SOURCE_DIFF.patch` against `reference/`.
- [x] Offline checks (mock transport): 80 jobs → 100 slots, 60/40, 10 per category, 20 pairs, empty IDs,
      null prior analysis, smuggled state, role/field rules, one malformed job visible, label-free critic
      payloads, packet/mapping hash binding, resume without replay.
- [x] Qwen3-32B: 80/80 jobs valid JSON, **93/100 slots usable**, 7 failures (families 001/007/010 pair
      chronology, 022 single turn), first attempts only; 722.5 s, 16,906 output tokens at 24.76 tok/s,
      peak 21,238 MiB, 80/80 fully GPU-resident.
- [x] Qwen unloaded, `/api/ps` empty, then Gemma3-27B blind critique: 93/93 valid, 2 ambiguity flags,
      416.0 s, peak 18,982 MiB, 93/93 fully GPU-resident; both models unloaded again.
- [x] Mechanical audit all pass: code-owned state unchanged, fixed messages preserved, packet bijection,
      annotation-free payloads, scored == raw responses, no exact or ID-normalised duplicates,
      17/20 pairs mechanically valid.
- [ ] Intended/critic agreement 79/93 — not accuracy. Inspector reading: 10 critic errors (3 definite
      readiness violations), 3 synthesis/contrast defects, 1 ambiguity dispute; pair review 4 usable /
      6 readable-but-defective / 7 broken over the 17 complete pairs.
- [ ] Dialogue defects preserved: asset IDs and fixture text inside dialogue (6 + 2 + 4 rows),
      perspective inversion in 8 pairs, operations announced before the consent that authorises them in
      5 pairs, one cross-family message template shared by families 009 and 017.
- [ ] **Zero accepted examples.** No merge, no LAYA inference/training, no next batch self-authorised.

Evidence: `Dataset_Batch_100/RETURN_SUMMARY.md`, `Dataset_Batch_100/runs/BATCH_COMPARISON.json`,
`Dataset_Batch_100/runs/audit/`, `Dataset_Batch_100/runs/PAIR_REVIEW.md`,
`Dataset_Batch_100/runs/{qwen_generation,gemma_review}/`, `Dataset_Batch_100/runs/*_peak*.json`,
`LAYA_Return_Dataset_Batch_100_2026-11-16.zip`.

## Approved 2,000-row dataset — review bundle returned (17 November 2026)

Scope change: `LAYA_Router_2000/` replaces the 600/100/200 target with 2,000 train / 200 dev /
300 synthetic test, reused the completed Batch-100 material and ran no new qualification. The
deliverable is the single pre-fit review handoff; **nothing is accepted and nothing was fitted**.

- [x] Pack verified: `LAYA_Router_2000/qa/verify_pack.py` **PASS 31 supplied files**;
      `qa/self_check.py` PASS (label-free serialisation, train-only guard, metrics, paired
      comparison, 2000/200/300 guards). Earlier capsules untouched.
- [x] Plan: `tools/plan_2000.py` → 2,400 generated slots across 845 families (670 train / 70 dev /
      105 test), at most four variants per family, 720/80/120 context pairs.
- [x] Code owns state, roles, the operative offer and the neutral current message; the pinned
      Qwen3-32B wrote user utterances only. 300 batched requests (8 slots each), 3,939 s,
      91,182 output tokens, digest `030ee887…7840`.
- [x] 2,388/2,400 slots passed text checks first pass; the 12 rejects (user speaking as the
      assistant, or repeating the fixed current message) were re-sampled once with fresh seeds,
      **all 12 recovered** — no slot was written by hand.
- [x] Gemma3-27B blind critique on 1,200 rows (all dev/test, 600 train sampled, all 100 curated
      seeds): 1,200/1,200 valid, 5,145 s, digest `6be2e2ba…efe7d`. Agreement with the proposed
      route 95/700 train, 16/200 dev, 18/300 test — reported as a fallible opinion, never a gate.
- [x] Bundle checks: exact 2,000/200/300; exact dev 120/80 and test 180/120; train 1,120/880;
      670/70/105 families; no family in two splits; no message+history combination spans splits;
      no dev/test message overlap; every input validates against the schema; 39 files hashed.
- [ ] Train mix is 1,120/880, 80 rows short of the 1,200/800 target. Left as generated because each
      label follows a code-owned condition; forcing the ratio would have meant relabelling rows or
      twin families sharing one assistant turn and one state.
- [ ] 130 rows share their dialogue text with another row in the same split (114 generated pairs,
      16 singles, 0 inside a family); scenes, states and labels stay independent.
- [ ] Writer readback agreed on every row, which is self-assessment, not independent evidence.
- [x] **Zero accepted examples, zero training, no LAYA inference, no publication.**

Evidence: `LAYA_Dataset_2000_Review_2026-11-17.zip` (SHA-256
`3bec2683239192f24fd8594e579abf29787a292305ca988ec1712511c1b4833c`, 40 entries, 1.46 MB),
`LAYA_Router_2000/bundle/` (`REVIEW_ROWS.jsonl`, `candidates/`, `critic/`, `writer/`,
`failed_slots.jsonl`, `sources/`, `manifest.json`, `REVIEW_SUMMARY.md`) and
`LAYA_Router_2000/runs/{corpus2_generation,corpus2_retry,corpus2_review}/`.

Next: Codex reads the rows individually and returns corrections or a freeze decision. Fitting
(`qa/verify_pack.py` → `tools/export_pilot.py` → `tools/check_and_freeze.py` →
`tools/run_training_and_comparison.py`) has **not** been started.

## Reviewed data → fitted, compared, exported (17 November 2026)

`LAYA_Reviewed_Training.zip` was applied as supplied; no synthesis, teacher round or
qualification rerun happened. Input checks, one seed42 fit, dev-only selection, the fixed-test
comparison and the export are all complete.

- [x] Review pack verified: `qa/verify_pack.py` **PASS 33 files**, `qa/self_check.py` PASS,
      `qa/check_reviewed_data.py` **PASS 2500 reviewed rows** (locked data/questions/serializer
      hashes, labels, canonical inputs, groups, unique inputs, split separation).
- [x] Pinned-tokenizer check `tools/check_and_freeze.py`: 2000/200/300 rows, 730/70/105 families,
      **no dropped state tokens, two distinct option markers on every row**, no id/family/group/
      input overlap, max assembled 314 tokens. `data/FREEZE.json` written; test not scored.
- [x] One fit (`runs/reviewed_router`): seed42, soft-CE, effective batch 16, encoder+head,
      7/8 epochs, early stop on development patience, **selected epoch 4**. 894 s, 875 planned
      updates, peak 8.35 GiB, encoder/head probe deltas 0.00124 / 0.00601. Test untouched.
- [x] Dev selection: macro-F1 0.9785 vs baseline 0.5806. The optional head-only recovery did not
      run because the primary fit already beat the baseline on development.
- [x] Fixed-test comparison, 300 rows / 105 groups, identical inputs, questions, serializer and
      raw argmax: accuracy **0.6100 → 0.9800** (+37.00 pp), macro-F1 **0.6068 → 0.9787**
      (+0.3719), TP/TN/FP/FN 105/78/108/9 → 110/184/2/4, paired corrections 115, regressions 4,
      group-bootstrap 95% delta [0.3017, 0.4394], majority-BASE reference 0.62.
- [x] Export: `runs/reviewed_router/trained_laya_router/` (weights SHA-256
      `cbca78ad…97e8`) plus local archive `trained_laya_router.zip` (SHA-256 `1eaaa973…03c6`).
      Fresh-process reload re-scored 24 frozen test inputs with **identical predictions**.
- [ ] Limits unchanged: one seed42 run on template-assisted synthetic data; the large gain reflects
      the original checkpoint's DEEPFAKE over-firing (BASE false activation 0.5806). Not a
      human-test, production or multi-seed result. No human review claimed anywhere.

Capsule: `LAYA_Router_2000/reviewed/LAYA_Reviewed_Router_Results_2026-11-17.zip` (SHA-256
`c29b803201a027a152cadb29356866932b78247c40b1f97e318dd8bba0f4206d`, 23 entries, 44 KB, no weights).
Nothing was uploaded or published.
