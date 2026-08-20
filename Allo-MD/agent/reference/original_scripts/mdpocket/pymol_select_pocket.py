from Bio.PDB import PDBParser, PDBIO
import numpy as np

# 输入文件
grid_pdb = "mdpout_dens_8.pdb"  # 网格点文件
ref_pdb = "reference.pdb"        # 参考蛋白结构
residues = [100, 101, ..., 120]  # 目标残基编号列表

# 解析参考蛋白，获取目标残基的坐标
parser = PDBParser()
ref_structure = parser.get_structure("ref", ref_pdb)
target_coords = []
for residue in ref_structure.get_residues():
    if residue.get_id()[1] in residues:  # 检查残基编号
        for atom in residue:
            target_coords.append(atom.coord)

# 解析网格点文件，筛选附近的虚原子
grid_structure = parser.get_structure("grid", grid_pdb)
selected_dummies = []
for atom in grid_structure.get_atoms():
    if atom.get_resname() == "DUM":  # 虚原子
        for coord in target_coords:
            distance = np.linalg.norm(atom.coord - coord)
            if distance < 5.0:  # 5Å 阈值
                selected_dummies.append(atom)
                break

# 保存筛选后的虚原子
io = PDBIO()
class DummySelector:
    def accept_atom(self, atom):
        return atom in selected_dummies
io.set_structure(grid_structure)
io.save("selected_pocket.pdb", DummySelector())