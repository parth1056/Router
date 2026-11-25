# Research evidence by repository

Links identify inspected Git snapshots. These commits locate the reported records. They need not be the original training commits. Some early experiments survive as reports.

## Router

Branch examined: main. The following links pin the evidence snapshot to commit 2f51d4b93622b8155de231a5672c15f6d645d319.

| Finding or ledger key | Research record |
|---|---|
| router.original.n, router.fine_tuned.n, router.original.accuracy, router.fine_tuned.accuracy, router.original.macro_f1, router.fine_tuned.macro_f1, router.original.deepfake_precision, router.fine_tuned.deepfake_precision, router.original.deepfake_recall, router.fine_tuned.deepfake_recall, router.original.base_false_activation_rate, router.fine_tuned.base_false_activation_rate, router.original.nll, router.fine_tuned.nll, router.original.brier, router.fine_tuned.brier, router.original.tp, router.fine_tuned.tp, router.original.tn, router.fine_tuned.tn, router.original.fp, router.fine_tuned.fp, router.original.fn, router.fine_tuned.fn | [tables/metrics.csv](https://github.com/parth1056/Router/blob/2f51d4b93622b8155de231a5672c15f6d645d319/tables/metrics.csv) |
| router.dev_history | [tables/epoch_history.csv](https://github.com/parth1056/Router/blob/2f51d4b93622b8155de231a5672c15f6d645d319/tables/epoch_history.csv) |
| Routing results | [results/capsule/RESULTS.md](https://github.com/parth1056/Router/blob/2f51d4b93622b8155de231a5672c15f6d645d319/results/capsule/RESULTS.md) |

## Image

Branch examined: master. The following links pin the evidence snapshot to commit 93b303a299ae7a83efb9eaf23da0f3c2884f7389.

| Finding or ledger key | Research record |
|---|---|
| df.deployed.ID, df.deployed.CM, df.deployed.CF, df.deployed.CD, df.deployed.MEAN, df.calibration | [deepfake_project/runs/timing/vanilla_calib/eval_calib.log](https://github.com/git-push-kar/LY_C68/blob/93b303a299ae7a83efb9eaf23da0f3c2884f7389/deepfake_project/runs/timing/vanilla_calib/eval_calib.log) |
| df.parent.ID, df.parent.CM, df.parent.CF, df.parent.CD, df.parent.MEAN | [deepfake_project/runs/intern_v2/logs/eval_best.log](https://github.com/git-push-kar/LY_C68/blob/93b303a299ae7a83efb9eaf23da0f3c2884f7389/deepfake_project/runs/intern_v2/logs/eval_best.log) |
| df.fused.ID, df.fused.CM, df.fused.CF, df.fused.CD, df.fused.MEAN | [deepfake_project/runs/timing/epoch3/eval_best.log](https://github.com/git-push-kar/LY_C68/blob/93b303a299ae7a83efb9eaf23da0f3c2884f7389/deepfake_project/runs/timing/epoch3/eval_best.log) |
| df.cd_generators | [deepfake_project/runs/timing/eval_by_generator_cd_vanilla.json](https://github.com/git-push-kar/LY_C68/blob/93b303a299ae7a83efb9eaf23da0f3c2884f7389/deepfake_project/runs/timing/eval_by_generator_cd_vanilla.json) |
| df.grounded_epochs | [deepfake_project/runs/intern_v2_ground/logs/epochs.csv](https://github.com/git-push-kar/LY_C68/blob/93b303a299ae7a83efb9eaf23da0f3c2884f7389/deepfake_project/runs/intern_v2_ground/logs/epochs.csv) |
| df.fused_dpo.ID, df.fused_dpo.CM, df.fused_dpo.CF, df.fused_dpo.CD, df.fused_dpo.MEAN | [deepfake_project/runs/intern_fused_dpo/logs/eval_dpo_best.log](https://github.com/git-push-kar/LY_C68/blob/93b303a299ae7a83efb9eaf23da0f3c2884f7389/deepfake_project/runs/intern_fused_dpo/logs/eval_dpo_best.log) |
| df.vanilla_dpo.ID, df.vanilla_dpo.CM, df.vanilla_dpo.CF, df.vanilla_dpo.CD, df.vanilla_dpo.MEAN | [deepfake_project/runs/intern_v2_dpo/logs/eval_dpo_best.log](https://github.com/git-push-kar/LY_C68/blob/93b303a299ae7a83efb9eaf23da0f3c2884f7389/deepfake_project/runs/intern_v2_dpo/logs/eval_dpo_best.log) |
| df.face | [deepfake_project/runs/calibration/ffiw_report_vanilla.json](https://github.com/git-push-kar/LY_C68/blob/93b303a299ae7a83efb9eaf23da0f3c2884f7389/deepfake_project/runs/calibration/ffiw_report_vanilla.json) |
| df.latency | [deepfake_project/runs/timing](https://github.com/git-push-kar/LY_C68/tree/93b303a299ae7a83efb9eaf23da0f3c2884f7389/deepfake_project/runs/timing) |

## Anomaly

Branch examined: master. The following links pin the evidence snapshot to commit 48b3917a1d9d17953b1fc4a216d529b0ee76c605.

| Finding or ledger key | Research record |
|---|---|
| tep.test | [docs/reports/evidence/files/test_contrast.json](https://github.com/git-push-kar/C68-Anomaly/blob/48b3917a1d9d17953b1fc4a216d529b0ee76c605/docs/reports/evidence/files/test_contrast.json) |
| tep.stratified | [docs/reports/figures/figure_data.json](https://github.com/git-push-kar/C68-Anomaly/blob/48b3917a1d9d17953b1fc4a216d529b0ee76c605/docs/reports/figures/figure_data.json) |
| tep.diagnosis, tep.diag_contrasts | [docs/reports/evidence/files/classifier_contrasts.json](https://github.com/git-push-kar/C68-Anomaly/blob/48b3917a1d9d17953b1fc4a216d529b0ee76c605/docs/reports/evidence/files/classifier_contrasts.json) |
| tep.kappa | [docs/reports/evidence/files/preference_kappa.json](https://github.com/git-push-kar/C68-Anomaly/blob/48b3917a1d9d17953b1fc4a216d529b0ee76c605/docs/reports/evidence/files/preference_kappa.json) |
| tep.protocolA | [outputs/tep_rca_v2_protocolA_seed42/training_summary.json](https://github.com/git-push-kar/C68-Anomaly/blob/48b3917a1d9d17953b1fc4a216d529b0ee76c605/outputs/tep_rca_v2_protocolA_seed42/training_summary.json) |
| tep.cells | [docs/reports/evidence/files/n4_cells.json](https://github.com/git-push-kar/C68-Anomaly/blob/48b3917a1d9d17953b1fc4a216d529b0ee76c605/docs/reports/evidence/files/n4_cells.json) |
| tep.order | [docs/reports/evidence/files/order_invariance.json](https://github.com/git-push-kar/C68-Anomaly/blob/48b3917a1d9d17953b1fc4a216d529b0ee76c605/docs/reports/evidence/files/order_invariance.json) |
| tep.selection | [docs/reports/evidence/files/selection_receipt.json](https://github.com/git-push-kar/C68-Anomaly/blob/48b3917a1d9d17953b1fc4a216d529b0ee76c605/docs/reports/evidence/files/selection_receipt.json) |
| tep.detector_all, tep.detector | [outputs/evaluation/detector_v2/v2_point/A_test.json](https://github.com/git-push-kar/C68-Anomaly/blob/48b3917a1d9d17953b1fc4a216d529b0ee76c605/outputs/evaluation/detector_v2/v2_point/A_test.json) |

## LR

Branch examined: master. The following links pin the evidence snapshot to commit 165d19a7580c83091b18acdaf24dd6b5796924ee.

| Finding or ledger key | Research record |
|---|---|
| lr.base.direct.LogicBench-BQA, lr.base.direct.LogicBench-MCQA, lr.base.direct.LogicNLI, lr.base.direct.Multi-LogiEval, lr.base.direct.ProofWriter_val, lr.base.direct.FOLIO_val, lr.base.direct.v3-holdout, lr.v3_sft.direct.LogicBench-BQA, lr.v3_sft.direct.LogicBench-MCQA, lr.v3_sft.direct.LogicNLI, lr.v3_sft.direct.Multi-LogiEval, lr.v3_sft.direct.ProofWriter_val, lr.v3_sft.direct.FOLIO_val, lr.v3_sft.direct.v3-holdout, lr.mcnemar | [results/summary_phase1.json](https://github.com/git-push-kar/C68-LR/blob/165d19a7580c83091b18acdaf24dd6b5796924ee/results/summary_phase1.json) |
| lr.p2.base.direct.LogicBench-BQA, lr.p2.base.direct.LogicBench-MCQA, lr.p2.base.direct.Multi-LogiEval, lr.p2.base.direct.LogicNLI, lr.p2.base.cot.LogicBench-BQA, lr.p2.base.cot.LogicBench-MCQA, lr.p2.base.cot.Multi-LogiEval, lr.p2.base.cot.LogicNLI, lr.p2.base.few_shot.LogicBench-BQA, lr.p2.base.few_shot.LogicBench-MCQA, lr.p2.base.few_shot.Multi-LogiEval, lr.p2.base.few_shot.LogicNLI, lr.p2.v3_sft.direct.LogicBench-BQA, lr.p2.v3_sft.direct.LogicBench-MCQA, lr.p2.v3_sft.direct.Multi-LogiEval, lr.p2.v3_sft.direct.LogicNLI, lr.p2.v3_sft.cot.LogicBench-BQA, lr.p2.v3_sft.cot.LogicBench-MCQA, lr.p2.v3_sft.cot.Multi-LogiEval, lr.p2.v3_sft.cot.LogicNLI, lr.sc5 | [results/summary_phase2.json](https://github.com/git-push-kar/C68-LR/blob/165d19a7580c83091b18acdaf24dd6b5796924ee/results/summary_phase2.json) |
| lr.perturb | [results/summary_perturb.json](https://github.com/git-push-kar/C68-LR/blob/165d19a7580c83091b18acdaf24dd6b5796924ee/results/summary_perturb.json) |
| lr.gate_verdict | [results/gate_decision.md](https://github.com/git-push-kar/C68-LR/blob/165d19a7580c83091b18acdaf24dd6b5796924ee/results/gate_decision.md) |

## Finance

Branch examined: main. The following links pin the evidence snapshot to commit 3efaef0df0a2baafec8048b6f3fc3681b1711d11.

| Finding or ledger key | Research record |
|---|---|
| fin.rot.protocol, fin.rot.seed42, fin.rot.seed123, fin.rot.seed456 | [docs/finance_evidence_20261118/rotation_records.json](https://github.com/git-push-kar/C68-FinanceRL/blob/3efaef0df0a2baafec8048b6f3fc3681b1711d11/docs/finance_evidence_20261118/rotation_records.json) |
| fin.strategy, fin.A.metrics | [docs/nifty_test_results/metrics.json](https://github.com/git-push-kar/C68-FinanceRL/blob/3efaef0df0a2baafec8048b6f3fc3681b1711d11/docs/nifty_test_results/metrics.json) |
| fin.stages_reported | [docs/FINANCE_EXPERIMENT_HANDOVER_20261118.md](https://github.com/git-push-kar/C68-FinanceRL/blob/3efaef0df0a2baafec8048b6f3fc3681b1711d11/docs/FINANCE_EXPERIMENT_HANDOVER_20261118.md) |
| fin.A.protocol | [docs/nifty_test_results/protocol.json](https://github.com/git-push-kar/C68-FinanceRL/blob/3efaef0df0a2baafec8048b6f3fc3681b1711d11/docs/nifty_test_results/protocol.json) |
| fin.A.intervals | [docs/nifty_test_results/paired_intervals_VALIDATED.json](https://github.com/git-push-kar/C68-FinanceRL/blob/3efaef0df0a2baafec8048b6f3fc3681b1711d11/docs/nifty_test_results/paired_intervals_VALIDATED.json) |
| fin.B.run2 | [docs/stateful_rl_run2_result](https://github.com/git-push-kar/C68-FinanceRL/tree/3efaef0df0a2baafec8048b6f3fc3681b1711d11/docs/stateful_rl_run2_result) |
| fin.B.run2_probes | [docs/stateful_rl_run2_result/validation_feature_sensitivity.json](https://github.com/git-push-kar/C68-FinanceRL/blob/3efaef0df0a2baafec8048b6f3fc3681b1711d11/docs/stateful_rl_run2_result/validation_feature_sensitivity.json) |
| fin.B.run3 | [docs/stateful_rl_run3_result](https://github.com/git-push-kar/C68-FinanceRL/tree/3efaef0df0a2baafec8048b6f3fc3681b1711d11/docs/stateful_rl_run3_result) |
| fin.B.run3_probes | [docs/stateful_rl_run3_result/selected_state_sensitivity.json](https://github.com/git-push-kar/C68-FinanceRL/blob/3efaef0df0a2baafec8048b6f3fc3681b1711d11/docs/stateful_rl_run3_result/selected_state_sensitivity.json) |
| fin.B.run1 | [docs/stateful_rl_run1_failure/manual_stop.json](https://github.com/git-push-kar/C68-FinanceRL/blob/3efaef0df0a2baafec8048b6f3fc3681b1711d11/docs/stateful_rl_run1_failure/manual_stop.json) |
| fin.expl_reported, fin.B.run4_reported | [docs/CONTEXT_TRANSFER_FULL.md](https://github.com/git-push-kar/C68-FinanceRL/blob/3efaef0df0a2baafec8048b6f3fc3681b1711d11/docs/CONTEXT_TRANSFER_FULL.md) |
| fin.C.reported | [docs/FULL_UNIVERSE_RESULT_20261118.md](https://github.com/git-push-kar/C68-FinanceRL/blob/3efaef0df0a2baafec8048b6f3fc3681b1711d11/docs/FULL_UNIVERSE_RESULT_20261118.md) |
| fin.D.numeric_control | [docs/COUNTERFACTUAL_RESULT_AND_FINAL_ROTATION.md](https://github.com/git-push-kar/C68-FinanceRL/blob/3efaef0df0a2baafec8048b6f3fc3681b1711d11/docs/COUNTERFACTUAL_RESULT_AND_FINAL_ROTATION.md) |
| fin.D.rl_only | [docs/finance_evidence_20261118/counterfactual_rl_only.json](https://github.com/git-push-kar/C68-FinanceRL/blob/3efaef0df0a2baafec8048b6f3fc3681b1711d11/docs/finance_evidence_20261118/counterfactual_rl_only.json) |
| fin.F.test | [demo/adapters/internvl3_native_rl/test_evaluation_summary.json](https://github.com/git-push-kar/C68-FinanceRL/blob/3efaef0df0a2baafec8048b6f3fc3681b1711d11/demo/adapters/internvl3_native_rl/test_evaluation_summary.json) |
| fin.F.forward | [demo/adapters/internvl3_native_rl/recent_2026_evaluation_summary.json](https://github.com/git-push-kar/C68-FinanceRL/blob/3efaef0df0a2baafec8048b6f3fc3681b1711d11/demo/adapters/internvl3_native_rl/recent_2026_evaluation_summary.json) |
| fin.F.checkpoints | [demo/adapters/internvl3_native_rl/best_rl_metrics.json](https://github.com/git-push-kar/C68-FinanceRL/blob/3efaef0df0a2baafec8048b6f3fc3681b1711d11/demo/adapters/internvl3_native_rl/best_rl_metrics.json) |
| fin.F.checkpoints | [demo/adapters/internvl3_native_rl/best_val_metrics.json](https://github.com/git-push-kar/C68-FinanceRL/blob/3efaef0df0a2baafec8048b6f3fc3681b1711d11/demo/adapters/internvl3_native_rl/best_val_metrics.json) |
| fin.F.checkpoints | [demo/adapters/internvl3_native_rl/training_history.json](https://github.com/git-push-kar/C68-FinanceRL/blob/3efaef0df0a2baafec8048b6f3fc3681b1711d11/demo/adapters/internvl3_native_rl/training_history.json) |

## Polyvalent

Branch examined: master. The following links pin the evidence snapshot to commit 89ba860181bb85708a6676221df478541dc28fc0.

| Finding or ledger key | Research record |
|---|---|
| Runtime integration | [docs/CONTEXT_TRANSFER_UNIFIED_FINANCE_INTEGRATION.md](https://github.com/git-push-kar/Polyvalent/blob/89ba860181bb85708a6676221df478541dc28fc0/docs/CONTEXT_TRANSFER_UNIFIED_FINANCE_INTEGRATION.md) |
| Runtime integration | [deepfake/face_detect.py](https://github.com/git-push-kar/Polyvalent/blob/89ba860181bb85708a6676221df478541dc28fc0/deepfake/face_detect.py) |
| Runtime integration | [router/adapter_service.py](https://github.com/git-push-kar/Polyvalent/blob/89ba860181bb85708a6676221df478541dc28fc0/router/adapter_service.py) |
