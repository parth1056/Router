# Pinned training API inspected for this run

Official source: https://github.com/NandhaKishorM/laya/blob/80a1da1fa5448ea12163f4d977935625a0aea670/laya/train.py
Sequence format: https://github.com/NandhaKishorM/laya/blob/80a1da1fa5448ea12163f4d977935625a0aea670/laya/common.py

Codex inspected these exact source files while preparing this pack. Use the existing installed pin; no latest-library substitution is needed.

- load_checkpoint(model_dir) loads the full existing state dict strictly, on CPU in FP32. Do not reset/reinitialise the task head for the baseline.
- items_from_rows accepts {state,questions,gold}, returning items and skip counts. Use one choice question with canonical BASE,DEEPFAKE criteria for both checkpoints.
- TrainConfig supports soft-ce, shuffle_options=(choice,), freeze_encoder, micro_batch, grad_accum and explicit 512/192 budgets. train_model accepts on_epoch_end(epoch,mean_loss). It sets train mode at entry; callbacks that evaluate must restore train mode afterward (and leave encoder.eval in head-only mode).
- calibration_records returns RAW logits and targets in canonical option order; it does not apply saved temperatures. It preserves item order. Targets are not fed to the model forward pass. Do not temperature-scale one baseline differently.
- save_checkpoint exports FP16 tensors plus encoder config/tokenizer/config. Evaluate the SAVED/RELOADED chosen checkpoint, not only the in-memory training object. Do not assume exact probability identity across the save precision conversion.
- uses_parallel_layout(cfg) preserves the weight checkpoint's layout. Do not invent a new layout to make inference faster.
- build_sequence(...,return_stats=True,return_truncation_stats=True) reports actual head/options and surviving state. A per-message token count cannot prove full context survived. The supplied freeze checker uses this actual path.

The wrappers have CPU syntax/export/metric tests, not a claimed GPU run. Freebuff is authorised to resolve ordinary wrapper/API or memory issues on the actual college PC, with logs/source changes, and continue this single run to actual results. No intermediate approval gate is required.
