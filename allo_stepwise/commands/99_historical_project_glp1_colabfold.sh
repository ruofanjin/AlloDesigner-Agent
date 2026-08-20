#!/usr/bin/env bash
set -euo pipefail

# Historical GLP1/GPL1 ColabFold commands copied from the project-level
# colabfold_batch.sh. They write to the original case/GPL1 directory and are
# included only to document the parameters and stage placement.

echo "This provenance script is permanently disabled because it targets the original case directory."
echo "Use commands/04_write_iteration_colabfold_commands.sh and 12_write_final_colabfold_commands.sh."
exit 2

colabfold_batch --num-recycle 3 --num-models 1 --num-seeds 1 --random-seed 42 /root/data1/data/move/ZYY/zyy/works/AF_ClaSeq/case/GPL1/6x18_chianR_R/run/01_iterative_shuffling/Iteration_1/shuffle_1 /root/data1/data/move/ZYY/zyy/works/AF_ClaSeq/case/GPL1/6x18_chianR_R/run/01_iterative_shuffling/Iteration_1/shuffle_1
colabfold_batch --num-recycle 3 --num-models 1 --num-seeds 1 --random-seed 42 /root/data1/data/move/ZYY/zyy/works/AF_ClaSeq/case/GPL1/6x18_chianR_R/run/01_iterative_shuffling/Iteration_6/shuffle_1 /root/data1/data/move/ZYY/zyy/works/AF_ClaSeq/case/GPL1/6x18_chianR_R/run/01_iterative_shuffling/Iteration_6/shuffle_1
colabfold_batch --num-recycle 3 --num-models 1 --num-seeds 1 --random-seed 42 /root/data1/data/move/ZYY/zyy/works/AF_ClaSeq/case/GPL1/6x18_chianR_R/run/02_m_fold_sampling/round_1/02_init_random_split /root/data1/data/move/ZYY/zyy/works/AF_ClaSeq/case/GPL1/6x18_chianR_R/run/02_m_fold_sampling/round_1/02_init_random_split
colabfold_batch --num-recycle 3 --num-models 1 --num-seeds 1 --random-seed 42 /root/data1/data/move/ZYY/zyy/works/AF_ClaSeq/case/GPL1/6x18_chianR_R/run/02_m_fold_sampling/round_1/02_sampling/sampling_1 /root/data1/data/move/ZYY/zyy/works/AF_ClaSeq/case/GPL1/6x18_chianR_R/run/02_m_fold_sampling/round_1/02_sampling/sampling_1
colabfold_batch --num-recycle 3 --num-models 5 --num-seeds 8 /root/data1/data/move/ZYY/zyy/works/AF_ClaSeq/case/GPL1/6x18_chianR_R/run/04_recompile/pocket_min_distance/prediction/bin_3_4 /root/data1/data/move/ZYY/zyy/works/AF_ClaSeq/case/GPL1/6x18_chianR_R/run/04_recompile/pocket_min_distance/prediction/bin_3_4
colabfold_batch --num-recycle 3 --num-models 5 --num-seeds 8 /root/data1/data/move/ZYY/zyy/works/AF_ClaSeq/case/GPL1/6x18_chianR_R/run/04_recompile/pocket_min_distance/control_prediction/bin_3_4 /root/data1/data/move/ZYY/zyy/works/AF_ClaSeq/case/GPL1/6x18_chianR_R/run/04_recompile/pocket_min_distance/control_prediction/bin_3_4
