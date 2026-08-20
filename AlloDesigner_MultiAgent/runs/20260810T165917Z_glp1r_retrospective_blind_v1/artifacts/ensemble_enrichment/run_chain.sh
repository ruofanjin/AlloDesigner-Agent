#!/usr/bin/env bash
set -euo pipefail
# target=GLP1R
export PYTHON_BIN=/lambda/nfs/file2/cqr_files/BioClaw_gpu_envs/glp1_allo_core/bin/python
export FPOCKET_BIN="${FPOCKET_BIN:-/lambda/nfs/file2/cqr_files/BioClaw_gpu_envs/allo-pocketminer/bin/fpocket}"
export COLABFOLD_BIN="${COLABFOLD_BIN:-colabfold_batch}"
# conda prefix: conda run -n glp1_allo_core --no-capture-output
cd /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise && ./commands/00_check_environment.sh --allow-missing-external
cd /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise && ./commands/00_plan.sh
cd /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise && ./commands/02_prepare_iteration_input.sh
cd /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise && ./commands/03_generate_iteration_msas.sh
cd /lambda/nfs/file2/jrf/AlloDesigner/allo_stepwise && ./commands/04_write_iteration_colabfold_commands.sh
cd /lambda/nfs/file2/jrf/AlloDesigner/AlphaFlow && python 1-mmseqs_search_helper.py --split ./GLP1_chain_seqres.csv --outdir ./alignment_dir/alignment_dir_GLP1
