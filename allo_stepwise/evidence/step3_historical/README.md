# Optional historical Step 3 evidence

The frozen-handoff downstream workflow does not require this directory to be populated.
The full historical audit in commands/01_audit_step3_handoff.sh does.

Expected layout:

    step3_historical/
    ├── iteration_1/
    │   ├── pocketminer_predict_residues_cluster/
    │   └── pocketminer_cluster_deepallo_score/
    ├── allodesigner/
    │   ├── 5vex_apo_model.npy
    │   ├── AlloDesigner_residue_probabilities_averge_0.7.csv
    │   └── every_apo_predict/
    └── expert/
        ├── holo_cluster_for_msa.csv
        ├── plb_scores_dcc_dvo.csv
        └── 6x18_seqres_to_atom_mapping.pkl

File names, expected counts and hashes are defined in
configs/stepwise/03_step3_pocket_selection.yaml. After supplying every file, run:

    RUN_STEP3_AUDIT=1 ./commands/00_plan.sh

Do not mix historical legacy-indexing evidence with corrected-mapping results.
