import os
import logging
import random
from pathlib import Path
from typing import List, Dict
from Bio.PDB import PDBParser, PPBuilder

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_protein_sequence(pdb_filename: str) -> str:
    pdb_parser = PDBParser(QUIET=True)
    structure = pdb_parser.get_structure("Protein", pdb_filename)
    ppb = PPBuilder()
    
    sequences = [str(pp.get_sequence()) for pp in ppb.build_peptides(structure)]
    full_sequence = ''.join(sequences)
    
    if not full_sequence:
        logger.warning(f"No protein sequence found in {pdb_filename}")
        
    return full_sequence

def read_a3m_to_dict(a3m_file_path: str) -> Dict[str, str]:
    try:
        sequences = {}
        current_header = None
        
        with open(a3m_file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('>'):
                    current_header = line.split()[0]
                    sequences[current_header] = ''
                elif current_header is not None:
                    sequences[current_header] += ''.join(char for char in line if not char.islower())
        return sequences
    except FileNotFoundError:
        logger.error(f"File not found: {a3m_file_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading A3M file: {e}")
        raise

def create_control_file(source_msa: str, default_pdb: str, output_file: str, num_samples: int = 2, num_repeats: int = 10) -> None:
    """
    Create multiple control A3M files, each with a query and random sequences.

    Args:
        source_msa (str): Path to the A3M file to sample from.
        default_pdb (str): Path to the PDB file to extract query sequence.
        output_file (str): Base output path. Files will be saved as output_file_i.a3m
        num_samples (int): Number of random sequences per file.
        num_repeats (int): How many files to generate.
    """
    query_seq = get_protein_sequence(default_pdb)
    sequences = read_a3m_to_dict(source_msa)
    sequence_items = list(sequences.items())

    if len(sequence_items) < num_samples:
        logger.warning(f"Not enough sequences to sample {num_samples}. Using {len(sequence_items)}.")
        num_samples = len(sequence_items)

    for i in range(num_repeats):
        selected_items = random.sample(sequence_items, num_samples)
        output_path = f"{output_file}_{i+1}.a3m"

        with open(output_path, 'w') as f:
            f.write(f">query\n{query_seq}\n")
            for header, seq in selected_items:
                f.write(f"{header}\n{seq}\n")
        
        logger.info(f"Wrote control file: {output_path} with {num_samples} sequences")

# Example usage
source_msa = './AF_ClaSeq/case/CB1R/default/6n4b_R.a3m'
output_file = './AF_ClaSeq/case/CB1R/random_select_msa_num/random_select_msa_num20/random_select_msa_num20'
default_pdb = './alphaflow-master/case/CB1/predict_output/6n4b_R/6n4b_R_MODEL_0.pdb'

create_control_file(source_msa, default_pdb, output_file, num_samples=20, num_repeats=10)
