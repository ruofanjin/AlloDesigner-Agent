#!/usr/bin/env bash
set -euo pipefail

if [[ -d "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_1" ]] && compgen -G "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_1/*.a3m" >/dev/null; then
  /lambda/nfs/file2/cqr_files/BioClaw_gpu_envs/localcolabfold/.pixi/envs/default/bin/colabfold_batch --num-recycle 3 --num-models 1 --num-seeds 1 --random-seed 42 --max-msa 8:16 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_1 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_1
else
  echo "SKIP missing directory or A3M: /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_1"
fi

if [[ -d "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_2" ]] && compgen -G "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_2/*.a3m" >/dev/null; then
  /lambda/nfs/file2/cqr_files/BioClaw_gpu_envs/localcolabfold/.pixi/envs/default/bin/colabfold_batch --num-recycle 3 --num-models 1 --num-seeds 1 --random-seed 42 --max-msa 8:16 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_2 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_2
else
  echo "SKIP missing directory or A3M: /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_2"
fi

if [[ -d "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_3" ]] && compgen -G "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_3/*.a3m" >/dev/null; then
  /lambda/nfs/file2/cqr_files/BioClaw_gpu_envs/localcolabfold/.pixi/envs/default/bin/colabfold_batch --num-recycle 3 --num-models 1 --num-seeds 1 --random-seed 42 --max-msa 8:16 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_3 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_3
else
  echo "SKIP missing directory or A3M: /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_3"
fi

if [[ -d "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_4" ]] && compgen -G "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_4/*.a3m" >/dev/null; then
  /lambda/nfs/file2/cqr_files/BioClaw_gpu_envs/localcolabfold/.pixi/envs/default/bin/colabfold_batch --num-recycle 3 --num-models 1 --num-seeds 1 --random-seed 42 --max-msa 8:16 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_4 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_4
else
  echo "SKIP missing directory or A3M: /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_4"
fi

if [[ -d "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_5" ]] && compgen -G "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_5/*.a3m" >/dev/null; then
  /lambda/nfs/file2/cqr_files/BioClaw_gpu_envs/localcolabfold/.pixi/envs/default/bin/colabfold_batch --num-recycle 3 --num-models 1 --num-seeds 1 --random-seed 42 --max-msa 8:16 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_5 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_5
else
  echo "SKIP missing directory or A3M: /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_5"
fi

if [[ -d "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_6" ]] && compgen -G "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_6/*.a3m" >/dev/null; then
  /lambda/nfs/file2/cqr_files/BioClaw_gpu_envs/localcolabfold/.pixi/envs/default/bin/colabfold_batch --num-recycle 3 --num-models 1 --num-seeds 1 --random-seed 42 --max-msa 8:16 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_6 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_6
else
  echo "SKIP missing directory or A3M: /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_6"
fi

if [[ -d "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_7" ]] && compgen -G "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_7/*.a3m" >/dev/null; then
  /lambda/nfs/file2/cqr_files/BioClaw_gpu_envs/localcolabfold/.pixi/envs/default/bin/colabfold_batch --num-recycle 3 --num-models 1 --num-seeds 1 --random-seed 42 --max-msa 8:16 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_7 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_7
else
  echo "SKIP missing directory or A3M: /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_7"
fi

if [[ -d "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_8" ]] && compgen -G "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_8/*.a3m" >/dev/null; then
  /lambda/nfs/file2/cqr_files/BioClaw_gpu_envs/localcolabfold/.pixi/envs/default/bin/colabfold_batch --num-recycle 3 --num-models 1 --num-seeds 1 --random-seed 42 --max-msa 8:16 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_8 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_8
else
  echo "SKIP missing directory or A3M: /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_8"
fi

if [[ -d "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_9" ]] && compgen -G "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_9/*.a3m" >/dev/null; then
  /lambda/nfs/file2/cqr_files/BioClaw_gpu_envs/localcolabfold/.pixi/envs/default/bin/colabfold_batch --num-recycle 3 --num-models 1 --num-seeds 1 --random-seed 42 --max-msa 8:16 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_9 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_9
else
  echo "SKIP missing directory or A3M: /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_9"
fi

if [[ -d "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_10" ]] && compgen -G "/lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_10/*.a3m" >/dev/null; then
  /lambda/nfs/file2/cqr_files/BioClaw_gpu_envs/localcolabfold/.pixi/envs/default/bin/colabfold_batch --num-recycle 3 --num-models 1 --num-seeds 1 --random-seed 42 --max-msa 8:16 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_10 /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_10
else
  echo "SKIP missing directory or A3M: /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise/workdir/run/01_iterative_shuffling/Iteration_5/shuffle_10"
fi

