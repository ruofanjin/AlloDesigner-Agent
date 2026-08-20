from Bio import PDB
import os

def align_structure_and_save(ref_pdb, target_pdb, output_pdb):
    parser = PDB.PDBParser(QUIET=True)
    ref_structure = parser.get_structure("ref", ref_pdb)
    target_structure = parser.get_structure("target", target_pdb)

    ref_atoms = []
    target_atoms = []

    for ref_res, target_res in zip(ref_structure[0].get_residues(), target_structure[0].get_residues()):
        if "CA" in ref_res and "CA" in target_res:
            ref_atoms.append(ref_res["CA"])
            target_atoms.append(target_res["CA"])

    if len(ref_atoms) == 0 or len(target_atoms) == 0:
        raise ValueError("wrong Cα")
    
    super_imposer = PDB.Superimposer()
    super_imposer.set_atoms(ref_atoms, target_atoms)
    super_imposer.apply(target_structure.get_atoms())  


    io = PDB.PDBIO()
    io.set_structure(target_structure)
    io.save(output_pdb)


ref_pdb = "./deepallo-main/source_data/data/find_pocket/case/GLP1/GLP-1R-NNC0640/5vex_chianR_covert_apo.pdb"
target_pdb = "./AF_ClaSeq/case/GPL1/6x18_chianR_R/run/01_iterative_shuffling/Iteration_1/shuffle_1_fpocket/group_29_unrelaxed_rank_001_alphafold2_ptm_model_1_seed_042.pdb"
output_pdb = "./AF_ClaSeq/case/GPL1/6x18_chianR_R/run/01_iterative_shuffling/Iteration_1/shuffle_1_group_29_aligned_output.pdb"

align_structure_and_save(ref_pdb, target_pdb, output_pdb)

