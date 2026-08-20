
import os
import logging
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Any, Optional, Union, Sequence
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict, Counter
from tqdm import tqdm
from pathlib import Path
import re



class VotingAnalyzer:
    """
    Class that performs the core sequence voting calculations.
    
    This class provides methods to process sampling directories,
    create metric bins, and collect votes from sequences.
    """
    
    def __init__(self, max_workers: int = 64):
        """
        Initialize the VotingAnalyzer.
        
        Args:
            max_workers: Maximum number of concurrent workers for processing
        """
        self.max_workers = max_workers

    def process_sampling_dirs(self, 
                              base_dir: str, 
                              precomputed_metrics_file: Optional[str] = None,
                             ) -> Dict[str, Dict[str, float]]:
        """Process sampling directories to calculate metrics in parallel.
        
        Args:
            base_dir: Base directory containing sampling results
            filter_criteria: List of criteria for filtering structures
            basics: Basic configuration parameters
            precomputed_metrics_file: Optional path to precomputed metrics CSV/directory
            plddt_threshold: Minimum pLDDT score threshold
            hierarchical: Whether to process hierarchical sampling directories
            
        Returns:
            Dictionary mapping PDB paths to their metric values
        """
        results = {}


        # Try to load precomputed metrics first
        if precomputed_metrics_file:
            results = self._load_precomputed_metrics(
                precomputed_metrics_file
            )
            if results:
                return results

        return results

    def _process_pdb_file(self, pdb_path, filter_criteria, basics, plddt_threshold):
        """Process a single PDB file and return metrics if valid."""
        # Use the improved StructureAnalyzer method
        result = self.structure_analyzer.process_single_pdb(
            pdb_path, filter_criteria, basics, plddt_threshold
        )
        
        if result:
            # Extract only the required metrics for voting
            metrics = {
                criterion['name']: result[criterion['name']] 
                for criterion in filter_criteria 
                if criterion['name'] in result
            }
            
            return pdb_path, metrics
        
        return None

    def _load_precomputed_metrics(self, 
                                 precomputed_metrics_file: str, 
                                 ) -> Dict[str, Dict[str, float]]:
        """Load metrics from precomputed CSV files."""
        results = {}
        
        # Handle directory with multiple CSV files
        if os.path.isdir(precomputed_metrics_file):

            csv_path = './AF_ClaSeq/case/PCKS9/4ne9/run/02_m_fold_sampling/round_1/02_sampling/pocketminer_predict_residues_cluster_eps6/all_sampling_avg_distance_combined.csv'
            
            self._process_metrics_csv(csv_path, results)

        
        if results:
            print(f"Loaded metrics for {len(results)} structures from precomputed files")
            
        return results
    
    def _process_metrics_csv(self, 
                            csv_path: str, 
                            results: Dict[str, Dict[str, float]]) -> None:
        """Process a single metrics CSV file and update results dictionary."""
        metrics_df = pd.read_csv(csv_path)
        
        for _, row in metrics_df.iterrows():
                
            pdb_path = row['sampling_group_id']
            
            # Add metrics to results
            if pdb_path not in results:
                results[pdb_path] = {}

                results[pdb_path]['pocket_min_disatance'] = row['min_distance']

    def _collect_pdb_files(self, base_dir: str) -> List[str]:
        """Collect PDB files from single or multi-round sampling directories."""
        pdb_files = []
        
        # Check if we have a rounds-based directory structure
        round_dirs = [d for d in os.listdir(base_dir) if d.startswith('round_')]
        
        if round_dirs:
            # Multi-round structure
            for round_dir in round_dirs:
                round_path = os.path.join(base_dir, round_dir)
                sampling_path = os.path.join(round_path, '02_sampling')
                
                if not os.path.exists(sampling_path):
                    continue
                    
                sampling_dirs = [d for d in os.listdir(sampling_path) if d.startswith('sampling_')]
                
                for sampling_dir in sampling_dirs:
                    dir_path = os.path.join(sampling_path, sampling_dir)
                    for group_dir in os.listdir(dir_path):
                        if group_dir.endswith('.a3m'):
                            a3m_path = os.path.join(dir_path, group_dir)
                            base_name = os.path.splitext(a3m_path)[0]
                            pdb_name = f"{base_name}_unrelaxed_rank_001_alphafold2_ptm_model_1_seed_042.pdb"
                            if os.path.exists(pdb_name):
                                pdb_files.append(pdb_name)
        else:
            # Standard directory structure (single round)
            sampling_dirs = [d for d in os.listdir(base_dir) if d.startswith('sampling_')]
            
            for sampling_dir in sampling_dirs:
                dir_path = os.path.join(base_dir, sampling_dir)
                for f in os.listdir(dir_path):
                    if f.endswith('.a3m'):
                        base_name = os.path.splitext(os.path.join(dir_path, f))[0]
                        pdb_name = f"{base_name}_unrelaxed_rank_001_alphafold2_ptm_model_1_seed_042.pdb"
                        if os.path.exists(pdb_name):
                            pdb_files.append(pdb_name)
                        
        return pdb_files
    
    def _extract_indices(self, indices_spec, default_indices):
        """Extract indices from specification or use defaults."""
        if not indices_spec:
            return default_indices
            
        if isinstance(indices_spec, list):
            result = []
            for range_dict in indices_spec:
                result.extend(range(range_dict['start'], range_dict['end']+1))
            return result
        else:
            return list(range(indices_spec['start'], indices_spec['end'] + 1))
    
    def create_1d_metric_bins(self, 
                           results: Dict[str, Dict[str, float]], 
                           metric_name: str, 
                           num_bins: int = 20,
                           min_value: Optional[float] = None,
                           max_value: Optional[float] = None) -> Tuple[np.ndarray, Dict[str, int]]:
        """Create 1D bins for a specific metric and assign PDBs to bins.
        
        Args:
            results: Dictionary mapping PDB IDs to their metric values
            metric_name: Name of the metric to bin
            num_bins: Number of bins to create
            min_value: Optional minimum value for binning range. If None, uses min of data
            max_value: Optional maximum value for binning range. If None, uses max of data
            
        Returns:
            Tuple containing:
            - Array of bin edges
            - Dictionary mapping PDB IDs to bin indices
        """
        if not results:
            raise ValueError("No results provided for binning")
            
        metric_values = [metrics[metric_name] for metrics in results.values() if metric_name in metrics]
        if not metric_values:
            raise ValueError(f"No valid values found for metric {metric_name}. Check if metric calculation succeeded.")
            
        # Use provided min/max if given, otherwise use data min/max
        min_val = min_value if min_value is not None else min(metric_values)
        max_val = max_value if max_value is not None else max(metric_values)
        
        # Validate values are within range if min/max were provided
        if min_value is not None:
            assert all(v >= min_value for v in metric_values), f"Some {metric_name} values are below minimum {min_value}"
        if max_value is not None:
            assert all(v <= max_value for v in metric_values), f"Some {metric_name} values are above maximum {max_value}"
            
        bins = np.linspace(min_val, max_val, num_bins + 1)
        
        # Assign each PDB to a bin
        pdb_bins = {}
        for pdb, metrics in results.items():
            if metric_name in metrics:
                bin_idx = np.digitize(metrics[metric_name], bins) - 1
                pdb_bins[pdb] = bin_idx
            
        return bins, pdb_bins
    
    def create_focused_1d_bins(self,
                             results: Dict[str, Dict[str, float]],
                             metric_name: str,
                             num_bins: int,
                             min_value: Optional[float] = None,
                             max_value: Optional[float] = None) -> Tuple[np.ndarray, Dict[str, int]]:
        """Create 1D bins with focus range, assigning outliers to edge bins.
        
        Args:
            results: Dictionary mapping PDB IDs to their metric values
            metric_name: Name of the metric to bin
            num_bins: Number of bins to create within focus range
            min_value: Minimum value of focus range (optional)
            max_value: Maximum value of focus range (optional)
            
        Returns:
            Tuple containing:
            - Array of bin edges including outlier bins
            - Dictionary mapping PDB IDs to bin indices
        """
        if not results:
            raise ValueError("No results provided for binning")
            
        metric_values = [metrics[metric_name] for metrics in results.values() if metric_name in metrics]
        if not metric_values:
            raise ValueError(f"No valid values found for metric {metric_name}")
            
        # Use provided min/max if given, otherwise use data min/max
        min_val = min_value if min_value is not None else min(metric_values)
        max_val = max_value if max_value is not None else max(metric_values)
        
        # Create bins within focus range
        focus_bins = np.linspace(min_val, max_val, num_bins + 1)
        
        # Add edge bins for outliers
        bins = np.concatenate([[float('-inf')], focus_bins, [float('inf')]])
        
        # Assign each PDB to a bin
        pdb_bins = {}
        for pdb, metrics in results.items():
            if metric_name in metrics:
                value = metrics[metric_name]
                if value < min_val:
                    pdb_bins[pdb] = 0  # Below focus range
                elif value > max_val:
                    pdb_bins[pdb] = num_bins + 1  # Above focus range
                else:
                    # Within focus range - subtract 1 to account for the below-range bin
                    bin_idx = np.digitize(value, focus_bins) 
                    pdb_bins[pdb] = bin_idx
                    
        return bins, pdb_bins

    def create_2d_metric_bins(self,
                            results: Dict[str, Dict[str, float]],
                            metric_names: List[str],
                            num_bins: int = 10) -> Tuple[List[np.ndarray], Dict[str, Tuple[int, int]]]:
        """Create 2D bins using two metrics and assign PDBs to 2D bin coordinates."""
        if not results or len(metric_names) != 2:
            raise ValueError("Need results and exactly two metric names for 2D binning")

        metric1_name, metric2_name = metric_names
        
        # Get values for both metrics
        metric1_values = [metrics[metric1_name] for metrics in results.values() if metric1_name in metrics]
        metric2_values = [metrics[metric2_name] for metrics in results.values() if metric2_name in metrics]
        
        if not metric1_values or not metric2_values:
            raise ValueError("No valid values found for one or both metrics")

        # Create bins for each dimension
        bins1 = np.linspace(min(metric1_values), max(metric1_values), num_bins + 1)
        bins2 = np.linspace(min(metric2_values), max(metric2_values), num_bins + 1)

        # Assign each PDB to a 2D bin coordinate
        pdb_bins = {}
        for pdb, metrics in results.items():
            if metric1_name in metrics and metric2_name in metrics:
                bin_idx1 = np.digitize(metrics[metric1_name], bins1) - 1
                bin_idx2 = np.digitize(metrics[metric2_name], bins2) - 1
                pdb_bins[pdb] = (bin_idx1, bin_idx2)

        return [bins1, bins2], pdb_bins

    def create_3d_metric_bins(self,
                            results: Dict[str, Dict[str, float]],
                            metric_names: List[str],
                            num_bins: int = 10) -> Tuple[List[np.ndarray], Dict[str, Tuple[int, int, int]]]:
        """Create 3D bins using three metrics and assign PDBs to 3D bin coordinates."""
        if not results or len(metric_names) != 3:
            raise ValueError("Need results and exactly three metric names for 3D binning")

        metric1_name, metric2_name, metric3_name = metric_names
        
        # Get values for all three metrics
        metric1_values = [metrics[metric1_name] for metrics in results.values() if metric1_name in metrics]
        metric2_values = [metrics[metric2_name] for metrics in results.values() if metric2_name in metrics]
        metric3_values = [metrics[metric3_name] for metrics in results.values() if metric3_name in metrics]
        
        if not metric1_values or not metric2_values or not metric3_values:
            raise ValueError("No valid values found for one or more metrics")

        # Create bins for each dimension
        bins1 = np.linspace(min(metric1_values), max(metric1_values), num_bins + 1)
        bins2 = np.linspace(min(metric2_values), max(metric2_values), num_bins + 1)
        bins3 = np.linspace(min(metric3_values), max(metric3_values), num_bins + 1)

        # Assign each PDB to a 3D bin coordinate
        pdb_bins = {}
        for pdb, metrics in results.items():
            if all(m in metrics for m in metric_names):
                bin_idx1 = np.digitize(metrics[metric1_name], bins1) - 1
                bin_idx2 = np.digitize(metrics[metric2_name], bins2) - 1
                bin_idx3 = np.digitize(metrics[metric3_name], bins3) - 1
                pdb_bins[pdb] = (bin_idx1, bin_idx2, bin_idx3)

        return [bins1, bins2, bins3], pdb_bins
        
    def get_sequence_votes(self, 
                         source_msa: str, 
                         sampling_base_dir: str, 
                         pdb_bins: Dict[str, Union[int, Tuple]],
                         vote_threshold: float = 0.0,
                         hierarchical: bool = False) -> Tuple[Dict, Dict]:
        """Get votes for each sequence based on metric bins."""
        if not os.path.exists(source_msa):
            raise FileNotFoundError(f"Source MSA file not found: {source_msa}")
            
        with open(source_msa) as f:
            source_headers = {line.strip()[1:].split()[0] for line in f if line.startswith('>')}
            
        if not source_headers:
            raise ValueError("No headers found in source MSA file")
        
        # Collect all A3M files and their corresponding PDB files
        a3m_files = self._collect_a3m_files(sampling_base_dir, hierarchical)

        if not a3m_files:
            raise ValueError("No valid A3M/PDB file pairs found")



        # Process files in batches for better parallelization
        batch_size = max(1, len(a3m_files) // (self.max_workers * 4))

        batches = [a3m_files[i:i + batch_size] for i in range(0, len(a3m_files), batch_size)]
        
        all_votes = defaultdict(list)
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            batch_args = [(batch, pdb_bins, source_headers) for batch in batches]
            futures = [executor.submit(self._process_a3m_batch, args) for args in batch_args]
            
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing A3M batches"):
                batch_votes = future.result()
                for header, votes in batch_votes.items():
                    all_votes[header].extend(votes)

        # Process votes to find consensus
        sequence_votes = self._process_votes(all_votes, vote_threshold)

        if not sequence_votes:
            print("No sequence votes met the threshold criteria")

        return sequence_votes, dict(all_votes)
    
    def _collect_a3m_files(self, sampling_base_dir: str, hierarchical: bool) -> List[Tuple[str, str]]:
        """Collect A3M files and their corresponding PDB files from single or multi-round sampling."""
        a3m_files = []
        
        # Check if we have a rounds-based directory structure
        round_dirs = [d for d in os.listdir(sampling_base_dir) if d.startswith('round_')]
        
        if round_dirs:
            # Multi-round structure
            print(f"Found {len(round_dirs)} sampling rounds")
            for round_dir in round_dirs:
                round_path = os.path.join(sampling_base_dir, round_dir)
                sampling_path = os.path.join(round_path, '02_sampling')
                
                if os.path.exists(sampling_path):
                    sampling_dirs = [d for d in os.listdir(sampling_path) if d.startswith('sampling_')]
                    
                    for sampling_dir in sampling_dirs:
                        dir_path = os.path.join(sampling_path, sampling_dir)
                        for group_file in os.listdir(dir_path):
                            if group_file.endswith('.a3m'):
                                a3m_path = os.path.join(dir_path, group_file)
                                base_name = os.path.splitext(group_file)[0]
                                pdb_name = f"{base_name}_unrelaxed_rank_001_alphafold2_ptm_model_1_seed_042.pdb"
                                pdb_file = os.path.join(dir_path, pdb_name)
                                if os.path.exists(pdb_file):
                                    a3m_files.append((a3m_path, pdb_file))
        else:
            # Single round structure (flat directory)
            sampling_dirs = [d for d in os.listdir(sampling_base_dir) if d.startswith('sampling_')]
            
            for sampling_dir in sampling_dirs:
                dir_path = os.path.join(sampling_base_dir, sampling_dir)
                for a3m_file in os.listdir(dir_path):
                    if a3m_file.endswith('.a3m'):
                        a3m_path = os.path.join(dir_path, a3m_file)
                        base_name = os.path.splitext(a3m_file)[0]
                        pdb_name = f"{base_name}_unrelaxed_rank_001_alphafold2_ptm_model_1_seed_042.pdb"
                        pdb_file = os.path.join(dir_path, pdb_name)
                        if os.path.exists(pdb_file):
                            a3m_files.append((a3m_path, pdb_file))
                            
        print(f"Collected {len(a3m_files)} A3M/PDB file pairs")
        return a3m_files
    
    def _process_votes(self, all_votes, vote_threshold):
        """Process votes to find consensus for each sequence."""
        sequence_votes = {}

        for header, votes in all_votes.items():
            if not votes:
                continue
                
            total_votes = len(votes)
            
           
            # Handle 1D votes
            vote_array = np.array(votes)
            unique_votes, vote_counts = np.unique(vote_array, return_counts=True)
            most_common_idx = np.argmax(vote_counts)
            most_common_bin = unique_votes[most_common_idx]
            most_common_count = vote_counts[most_common_idx]
        
            # Only include votes that meet the threshold
            if most_common_count / total_votes >= vote_threshold:
                sequence_votes[header] = (most_common_bin, most_common_count, total_votes)

        return sequence_votes
    
    def _process_a3m_batch(self, batch_args):
        """Process a batch of A3M files in parallel"""
        a3m_files_batch, pdb_bins, source_headers = batch_args
        batch_votes = defaultdict(list)
        
        # Log sample information for debugging
        if source_headers:
            sample_headers = list(source_headers)[:5]  # Take first 5 headers as sample
            logging.info(f"Processing batch with {len(source_headers)} source headers")
            logging.info(f"Sample source headers: {sample_headers}...")
            
            if pdb_bins:
                sample_bins = list(pdb_bins.items())[:3]  # Take first 3 bin assignments as sample
                logging.info(f"PDB bins dictionary contains {len(pdb_bins)} entries")
                logging.info(f"Sample PDB bins: {sample_bins}...")
        else:
            logging.warning("No source headers found in the batch")
        
        for a3m_path, pdb_file in a3m_files_batch:
            match = re.search(r'sampling_(\d+)/group_(\d+)_', pdb_file)
            if match:
                sampling_i = match.group(1)
                group_i = match.group(2)
                combined_id = f"sampling_{sampling_i}_group_{group_i}"
            if combined_id in pdb_bins:
                try:
                    with open(a3m_path) as f:
                        headers = [line.strip()[1:].split('\t')[0] for line in f if line.startswith('>')]
                        
                    for header in headers:
                        if header in source_headers:
                            bin_assignment = pdb_bins[combined_id]
                            
                            # Add the bin assignment to the votes for this header
                            batch_votes[header].append(bin_assignment)
                except Exception as e:
                    logging.error(f"Error processing {a3m_path}: {str(e)}")
                        
        return dict(batch_votes)


class SequenceVotingRunner:
    """
    Runner class for sequence voting analysis.
    
    This class handles the process of analyzing sampling results,
    creating metric bins, and assigning votes to sequences based on
    their structural properties.
    """
    
    def __init__(
        self,
        sampling_dir: str,
        source_msa: str,
        output_dir: str,
        num_bins: int = 20,
        max_workers: int = 32,
        vote_threshold: float = 0.0,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        use_focused_bins: bool = False,
        precomputed_metrics: Optional[str] = None,
    ):
        """
        Initialize the voting runner with configuration parameters.
        
        Args:
            sampling_dir: Directory containing sampling results
            source_msa: Path to source MSA file
            config_path: Path to configuration JSON file
            output_dir: Output directory for voting results
            num_bins: Number of bins for voting
            max_workers: Maximum number of concurrent workers
            vote_threshold: Threshold for vote filtering (0-1)
            min_value: Minimum value for metric binning range
            max_value: Maximum value for metric binning range
            use_focused_bins: Whether to use focused 1D binning with outlier bins
            precomputed_metrics: Path to precomputed metrics CSV file or directory
            plddt_threshold: pLDDT threshold for filtering structures
            filter_criterion: Specific filter criterion name to process
        """
        self.sampling_dir = sampling_dir
        self.source_msa = source_msa
        self.output_dir = output_dir
        self.num_bins = num_bins
        self.max_workers = max_workers
        self.vote_threshold = vote_threshold
        self.min_value = min_value
        self.max_value = max_value
        self.use_focused_bins = use_focused_bins
        self.precomputed_metrics = precomputed_metrics

        
        # Initialize output directories
        self.voting_dir = self.output_dir
        os.makedirs(self.voting_dir, exist_ok=True)
        
        # Initialize voting analyzer
        self.analyzer = VotingAnalyzer(max_workers=self.max_workers)

    
    def run(self) -> Optional[str]:
        """
        Run the sequence voting analysis process.
        
        Returns:
            Path to results CSV file or None if process fails
        """
        results_file = os.path.join(self.voting_dir, "voting_results.csv")
        
        try:
            # Check if results file already exists
            if os.path.exists(results_file):
                print("Found existing results file, skipping computation")
                return results_file
            
            # Validate paths
            for path, name in [
                (self.sampling_dir, "Sampling directory"),
                (self.source_msa, "Source MSA file"),
            ]:
                if not os.path.exists(path):
                    raise FileNotFoundError(f"{name} not found: {path}")

            # Process sampling directories and get metrics

            results = self.analyzer.process_sampling_dirs(
                self.sampling_dir, 
                precomputed_metrics_file=self.precomputed_metrics,
            )
            
            if not results:
                print("No valid results found in sampling directories")
                return None
                
            # Create bins for the current criterion
            print("Creating metric bins...")
            criterion_name='pocket_min_disatance'
            if self.use_focused_bins:
                bins, pdb_bins = self.analyzer.create_focused_1d_bins(
                    results,
                    criterion_name,
                    self.num_bins,
                    self.min_value,
                    self.max_value
                )
            else:
                bins, pdb_bins = self.analyzer.create_1d_metric_bins(
                    results,
                    criterion_name,
                    num_bins=self.num_bins,
                    min_value=self.min_value,
                    max_value=self.max_value
                )
            

            sequence_votes, all_votes = self.analyzer.get_sequence_votes(
                self.source_msa,
                self.sampling_dir,
                pdb_bins,
                vote_threshold=self.vote_threshold
            )
            
            if not sequence_votes:
                self.logger.warning("No sequence votes met the threshold criteria")
                return None
                
            # Save raw sequence votes for later analysis
            self._save_raw_votes(all_votes)
            
            # Create and save results DataFrame
            results_df = self._create_results_dataframe(sequence_votes)
            results_df.to_csv(results_file, index=False)

            return results_file
            
        except Exception as e:
            print(f"An error occurred in sequence voting: {str(e)}")
            return None
    
    def _save_raw_votes(self, all_votes):
        """Save raw sequence votes to JSON file."""
        raw_votes_file = os.path.join(self.voting_dir, "raw_sequence_votes.json")
        
        # Convert votes to serializable format
        serializable_votes = {}
        for header, votes in all_votes.items():
            serializable_votes[header] = [int(v) for v in votes]
            
        with open(raw_votes_file, 'w') as f:
            json.dump(serializable_votes, f)
        
        print(f"Raw sequence votes saved to {raw_votes_file}")
    
    def _create_results_dataframe(self, sequence_votes):
        """Create DataFrame from sequence votes."""
        return pd.DataFrame([
            {
                "Sequence_Header": header,
                "Bin_Assignment": bin_num,
                "Vote_Count": vote_count,
                "Total_Votes": total_votes
            }
            for header, (bin_num, vote_count, total_votes) in sequence_votes.items()
        ])




# Create base output directory

voting_dir =  Path('./AF_ClaSeq/case/PCKS9/4ne9/run/03_voting')
voting_dir.mkdir(exist_ok=True)

# Use the correct path for m-fold sampling directory
m_fold_sampling_dir = './AF_ClaSeq/case/PCKS9/4ne9/run/02_m_fold_sampling'
source_a3m = './AF_ClaSeq/case/PCKS9/4ne9/default/4ne9.a3m'
results_files = []

criterion_output_dir = Path('./AF_ClaSeq/case/PCKS9/4ne9/run/03_voting/pocket_distance')
criterion_output_dir.mkdir(exist_ok=True)

# Create voting runner instance for this criterion
voting_runner = SequenceVotingRunner(
    sampling_dir=m_fold_sampling_dir,  # Updated to use the base m-fold directory
    source_msa=source_a3m,
    output_dir=criterion_output_dir,
    num_bins=20,
    max_workers=1,
    vote_threshold=0,
    # min_value=0,
    # max_value=20,
    min_value=None,
    max_value=None,
    use_focused_bins=True,
    precomputed_metrics='./AF_ClaSeq/case/PCKS9/4ne9/run/02_m_fold_sampling/round_1/02_sampling/pocketminer_predict_residues_cluster_eps6',
)

# Run voting analysis for this criterion
results_file = voting_runner.run()