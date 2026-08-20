# env_action=reuse profile=allo_pocketminer env=allo-pocketminer
cd /lambda/nfs/file2/jrf/AlloDesigner/Allo-PocketMiner && conda run -n allo-pocketminer --no-capture-output python case_predict.py
# threshold=0.7, target=GLP1R
