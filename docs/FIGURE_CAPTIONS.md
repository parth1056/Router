# Figure captions and reuse

SVG is the scalable source for paper/presentation insertion; PNG is the quick preview. tools/make_figures.py regenerates both formats and the CSV tables directly from preserved results. Macro-F1 is plotted as a unitless0-1 score; accuracy and false activation are percentages. No invented confidence bars or multiple-seed variability is shown.

1. router_architecture: The evaluated routing component serializes current text, conversation and trusted attachment/prior-result metadata, supplies a fixed typed-choice question, and obtains BASE/DEEPFAKE from the fine-tuned English LAYA encoder/head. Image pixels and specialist classification are outside this experiment.
2. routing_comparison: Original and fine-tuned LAYA on the same frozen300-example AI-labelled synthetic test, comprising105 scenario groups. False activation is measured over186 BASE-labelled requests. One seed and the indirect-label limitations apply.
3. routing_confusion_matrices: Frozen-label counts for original versus trained router, with a common colour scale. Rows are gold BASE/DEEPFAKE; columns are predicted routes. All300 examples appear in each matrix.
4. development_learning_curve: Development macro-F1 across seven completed epochs, with pristine baseline and selected epoch4 marked. Selection also uses false activation and NLL for ties; no test metric selected the checkpoint.

Limits to retain near these figures in the paper/slides: synthetic/template-assisted data, AI review, single training seed; all six final disagreements occur in16 indirect requests and some of their frozen labels are debatable/inconsistent. Do not describe98% as measured production accuracy or alter the scored benchmark.
