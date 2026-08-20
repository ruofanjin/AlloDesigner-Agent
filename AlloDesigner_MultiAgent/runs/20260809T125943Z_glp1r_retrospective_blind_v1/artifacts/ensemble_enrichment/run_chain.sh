#!/usr/bin/env bash
set -euo pipefail
# target=GLP1R
# conda prefix: conda run -n allo-pocketminer --no-capture-output
cd /lambda/nfs/file2/jrf/AlloDesigner/AlphaFlow && python 1-mmseqs_search_helper.py --split ./GLP1_chain_seqres.csv --outdir ./alignment_dir/alignment_dir_GLP1
cd /lambda/nfs/file2/jrf/AlloDesigner/AlphaFlow && bash 2-predict_test.sh
cd /lambda/nfs/file2/jrf/AlloDesigner/Allo_af_claseq && python 1_exact_pdb_from_dir_remove_new_dir_all_shuffle.py && python 2_fpocket_msa_pdb.py && python 3_calucate_fpocket_center_dir.py
cd /lambda/nfs/file2/jrf/AlloDesigner/Allo_af_claseq && python 11_sequence_voting.py
cd /lambda/nfs/file2/jrf/AlloDesigner/Allo_af_claseq && python 12_recompile.py
