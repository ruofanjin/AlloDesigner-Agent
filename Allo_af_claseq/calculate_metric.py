from af_claseq.utils.structure_analysis import (
    StructureAnalyzer,
    apply_filters,
    load_filter_modes
)
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Sequence
from tqdm import tqdm
import pandas as pd
from joblib import Parallel, delayed
import random
import logging
import json

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_result_df(parent_dir: str | Path,
                  filter_criteria: Sequence[Dict[str, Any]],
                  basics: Dict[str, Any],
                  plddt_threshold: float = 0) -> pd.DataFrame:
    logger.info(f'Processing {parent_dir}')
    parent_path = Path(parent_dir)
    pdb_files = [
        str(f) for f in parent_path.rglob('*.pdb')
        if 'non_a3m' not in str(f.parent)
    ]
    logger.info(f'Found {len(pdb_files)} PDB files')
    analyzer = StructureAnalyzer()
    results = Parallel(n_jobs=1)(
        delayed(analyzer.process_single_pdb)(
            pdb, filter_criteria, basics, plddt_threshold
        ) for pdb in tqdm(pdb_files, desc="Processing PDB files")
    )
    results = [r for r in results if r is not None]
    return pd.DataFrame(results)


def calculate_metric_values(
                            filter_modes: Dict[str, Any],
                            base_dir: str) -> Tuple[pd.DataFrame, str]:
    all_data = []
    metric_type = filter_modes['filter_criteria'][0]['type']
    metric_name = filter_modes['filter_criteria'][0]['name']


    results_df = get_result_df(
        base_dir,
        filter_modes['filter_criteria'],
        filter_modes['basics']
    )

    if not results_df.empty:
        data = pd.DataFrame({
            'PDB': results_df['PDB'],
            'seq_count': results_df['seq_count'],
            'plddt': results_df['plddt'],
            metric_name: results_df[metric_name]
        })
        all_data.append(data)

    combined_df = pd.concat(all_data, ignore_index=True)
    return combined_df, metric_type




if __name__ == "__main__":
    base_dir = "./AF_ClaSeq/case/CB1R/random_select_msa_num/random_select_msa_num20"

    with open("./AF_ClaSeq/case/CB1R/configs/config_cb1r_distance.json", "r") as f:
        filter_modes = json.load(f)

    result_df, metric_type = calculate_metric_values(filter_modes, base_dir)

    print("Result DataFrame:")
    print(f"\nMetric Type: {metric_type}")

    output_csv = "./AF_ClaSeq/case/CB1R/random_select_msa_num/random_select_msa_num20/csv/random_select_msa_num20_metric.csv"
    result_df.to_csv(output_csv, index=False)
