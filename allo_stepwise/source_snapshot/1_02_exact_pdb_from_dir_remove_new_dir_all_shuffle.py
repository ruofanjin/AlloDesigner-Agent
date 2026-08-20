import os
import shutil

def move_pdb_files(src_folder, dst_folder):
    os.makedirs(dst_folder, exist_ok=True)

    pdb_files = [
        os.path.join(src_folder, f)
        for f in os.listdir(src_folder)
        if f.endswith(".pdb")
    ]

    for file in pdb_files:
        shutil.copy(file, os.path.join(dst_folder, os.path.basename(file)))

    print(f"[✓] 已复制 {len(pdb_files)} 个 .pdb 文件至: {dst_folder}")


base_dir = "./AF_ClaSeq/case/PCKS9/4ne9/run/02_m_fold_sampling/round_1/02_sampling"


for i in range(1, 38):
    src_folder = os.path.join(base_dir, f"sampling_{i}")
    dst_folder = os.path.join(base_dir, f"sampling_{i}_fpocket")

    if not os.path.exists(src_folder):
        continue

    move_pdb_files(src_folder, dst_folder)
