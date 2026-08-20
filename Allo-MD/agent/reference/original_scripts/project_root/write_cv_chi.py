from Bio.PDB import PDBParser
from collections import defaultdict

# 氨基酸的 chi torsion 定义（可继续扩展）
# chi_torsions = {
#     "ARG": [["N", "CA", "CB", "CG"],
#             ["CA", "CB", "CG", "CD"],
#             ["CB", "CG", "CD", "NE"],
#             ["CG", "CD", "NE", "CZ"]],
#     "LYS": [["N", "CA", "CB", "CG"],
#             ["CA", "CB", "CG", "CD"],
#             ["CB", "CG", "CD", "CE"],
#             ["CG", "CD", "CE", "NZ"]],
#     "GLU": [["N", "CA", "CB", "CG"],
#             ["CA", "CB", "CG", "CD"],
#             ["CB", "CG", "CD", "OE1"]],
#     "GLN": [["N", "CA", "CB", "CG"],
#             ["CA", "CB", "CG", "CD"],
#             ["CB", "CG", "CD", "OE1"]],
#     "ILE": [["N", "CA", "CB", "CG1"],
#             ["CA", "CB", "CG1", "CD1"]],
#     "LEU": [["N", "CA", "CB", "CG"],
#             ["CA", "CB", "CG", "CD1"]],
#     "MET": [["N", "CA", "CB", "CG"],
#             ["CA", "CB", "CG", "SD"],
#             ["CB", "CG", "SD", "CE"]],
#     "PHE": [["N", "CA", "CB", "CG"],
#             ["CA", "CB", "CG", "CD1"]],
#     "TYR": [["N", "CA", "CB", "CG"],
#             ["CA", "CB", "CG", "CD1"]],
#     "TRP": [["N", "CA", "CB", "CG"],
#             ["CA", "CB", "CG", "CD1"]],
#     "ASN": [["N", "CA", "CB", "CG"],
#             ["CA", "CB", "CG", "OD1"]],
#     "ASP": [["N", "CA", "CB", "CG"],
#             ["CA", "CB", "CG", "OD1"]],
#     "SER": [["N", "CA", "CB", "OG"]],
#     "THR": [["N", "CA", "CB", "OG1"]],
#     "CYS": [["N", "CA", "CB", "SG"]],
#     "VAL": [["N", "CA", "CB", "CG1"]],
#     "HIS": [["N", "CA", "CB", "CG"],
#             ["CA", "CB", "CG", "ND1"]],
#     "PRO": [["N", "CA", "CB", "CG"],
#             ["CA", "CB", "CG", "CD"]]
# }

chi_torsions = {
    'ALA': [],  # 无侧链二面角
    'ARG': [['N', 'CA', 'CB', 'CG'],          # chi1
            ['CA', 'CB', 'CG', 'CD'],         # chi2
            ['CB', 'CG', 'CD', 'NE'],         # chi3
            ['CG', 'CD', 'NE', 'CZ'],         # chi4
            ['CD', 'NE', 'CZ', 'NH1']],       # chi5
    'ASN': [['N', 'CA', 'CB', 'CG'],          # chi1
            ['CA', 'CB', 'CG', 'OD1']],       # chi2
    'ASP': [['N', 'CA', 'CB', 'CG'],
            ['CA', 'CB', 'CG', 'OD1']],
    'CYS': [['N', 'CA', 'CB', 'SG']],
    'GLN': [['N', 'CA', 'CB', 'CG'],
            ['CA', 'CB', 'CG', 'CD'],
            ['CB', 'CG', 'CD', 'OE1']],
    'GLU': [['N', 'CA', 'CB', 'CG'],
            ['CA', 'CB', 'CG', 'CD'],
            ['CB', 'CG', 'CD', 'OE1']],
    'GLY': [],
    'HIS': [['N', 'CA', 'CB', 'CG'],
            ['CA', 'CB', 'CG', 'ND1']],
    'ILE': [['N', 'CA', 'CB', 'CG1'],
            ['CA', 'CB', 'CG1', 'CD1']],
    'LEU': [['N', 'CA', 'CB', 'CG'],
            ['CA', 'CB', 'CG', 'CD1']],
    'LYS': [['N', 'CA', 'CB', 'CG'],
            ['CA', 'CB', 'CG', 'CD'],
            ['CB', 'CG', 'CD', 'CE'],
            ['CG', 'CD', 'CE', 'NZ']],
    'MET': [['N', 'CA', 'CB', 'CG'],
            ['CA', 'CB', 'CG', 'SD'],
            ['CB', 'CG', 'SD', 'CE']],
    'PHE': [['N', 'CA', 'CB', 'CG'],
            ['CA', 'CB', 'CG', 'CD1']],
    'PRO': [['N', 'CA', 'CB', 'CG'],
            ['CA', 'CB', 'CG', 'CD']],
    'SER': [['N', 'CA', 'CB', 'OG']],
    'THR': [['N', 'CA', 'CB', 'OG1']],
    'TRP': [['N', 'CA', 'CB', 'CG'],
            ['CA', 'CB', 'CG', 'CD1']],
    'TYR': [['N', 'CA', 'CB', 'CG'],
            ['CA', 'CB', 'CG', 'CD1']],
    'VAL': [['N', 'CA', 'CB', 'CG1']],
}

def get_atom_serial(residue, atom_name):
    try:
        return residue[atom_name].get_serial_number()
    except KeyError:
        return None

def collect_chi_data(pdb_file):
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("prot", pdb_file)

    # chi_index -> list of (chi_label, [atom_serials], resid)
    chi_groups = defaultdict(list)

    for model in structure:
        for chain in model:
            for residue in chain:
                resname = residue.get_resname()
                resid = residue.get_id()[1]
                chain_id = chain.id
                if resname in chi_torsions:
                    for chi_idx, atom_names in enumerate(chi_torsions[resname], start=1):
                        serials = [get_atom_serial(residue, a) for a in atom_names]
                        if None in serials:
                            continue
                        chi_label = f"chi{chi_idx}_{resid}"
                        chi_groups[chi_idx].append((chi_label, serials, resid))
    return chi_groups

def write_plumed_by_chi_type(chi_groups, output="plumed_sorted_chi.dat"):
    print_args = []

    with open(output, "w") as f:
        for chi_idx in sorted(chi_groups):
            # f.write(f"\n# ---------- chi{chi_idx} ----------\n")
            for chi_label, serials, resid in chi_groups[chi_idx]:
                f.write(f"{chi_label}: TORSION ATOMS={','.join(map(str, serials))}\n")

                sc_name = f"sc{chi_idx}_r{resid}"
                cc_name = f"cc{chi_idx}_r{resid}"

                f.write(f"{sc_name}: CUSTOM ARG={chi_label} VAR={chi_label} FUNC=sin({chi_label}) PERIODIC=NO\n")
                f.write(f"{cc_name}: CUSTOM ARG={chi_label} VAR={chi_label} FUNC=cos({chi_label}) PERIODIC=NO\n")

                print_args.extend([sc_name, cc_name])  # 收集变量名

        f.write(f"PRINT ARG={','.join(print_args)} STRIDE=1 FILE=COLVARS.dat\n")

# 主入口
def generate_sorted_chi_plumed(pdb_file, output_file="/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed/plumed_chi_defined.dat"):
    chi_groups = collect_chi_data(pdb_file)
    write_plumed_by_chi_type(chi_groups, output_file)


generate_sorted_chi_plumed("/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/step5_input2.pdb")
