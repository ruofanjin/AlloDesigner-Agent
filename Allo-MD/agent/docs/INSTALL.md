# GROMACS + PLUMED/SASA + fpocket 部署指南

本文说明如何在另一台 Linux 主机上部署本实验所需的软件栈。目标组合为：

| 组件 | 固定版本/要求 |
|---|---|
| GROMACS | 2024.3，mixed precision、external MPI、OpenMP |
| PLUMED | 2.9.3，shared patch，显式启用 `sasa` 模块 |
| OpenMPI | 5.0.1 |
| FFTW | 3.3.10，单精度 `libfftw3f` |
| CMake | 3.18.4 以上；包内提供 x86_64 的 3.31.5 |
| GPU | 生产 MD 必需 NVIDIA CUDA；驱动和 Toolkit 由目标主机提供 |
| fpocket/MDpocket | 官方 4.2.3，固定 commit `4bb0d8447f62fee77e2c3c29f54b5fcaf5e2c066` + 包内校验补丁 |
| Shell/工具 | Bash 4.3 以上；Linux GNU coreutils、`realpath`、`sha256sum` |

这里的“已固定”表示部署包保留了版本和输入，不表示目标主机上的构建、测试或性能验证已经通过。每台新主机都必须执行本页的验证步骤。

## 1. 安全边界

- 安装不会自动启动任何生产模拟。
- 不复制当前主机的 build tree、已安装动态库、CUDA 驱动/Toolkit 或 `.bashrc`。
- 不依赖 `alias gmx=...`；所有脚本使用真实程序名 `gmx_mpi`。
- shared patch 模式通常不设置 `PLUMED_KERNEL`，更不能复制形如 `$/usr/local/...` 的错误路径。
- 系统包和 NVIDIA 驱动安装可能需要管理员权限，应由目标系统管理员确认；Agent 不应静默执行 sudo。
- 源码、构建目录和安装前缀必须分离。不要以 root 身份编译或运行生产任务。

## 2. 校验部署包与源码

在部署包根目录执行：

```bash
./agentctl verify-bundle

cd install
sha256sum -c SHA256SUMS
cd ..
```

包内五个 GROMACS 栈源码归档的固定摘要为：

```text
bbda056ee59390be7d58d84c13a9ec0d4e3635617adf2eb747034922cba1f029  gromacs-2024.3.tar.gz
0abf3098d11a8720d6f8d0b65df6a8da5ccd013c7b4a8ddbbc86229066d7d640  plumed2-2.9.3.tar.gz
56c932549852cddcfafdab3820b0200c7742675be92179e59e6215b340e26467  fftw-3.3.10.tar.gz
e357043e65fd1b956a47d0dae6156a90cf0e378df759364936c1781f1a25ef80  openmpi-5.0.1.tar.bz2
2984e70515ff60c5e4a41922b5d715a8168a696a89721e3b114e36f453244f72  cmake-3.31.5-linux-x86_64.tar.gz
```

任一摘要不匹配时停止部署，不要重新生成摘要来掩盖差异。fpocket 源码没有打入这五个离线归档；独立安装器在 `--execute` 时从官方仓库获取固定 tag 和完整 commit，并拒绝 tag 漂移。若目标节点完全离线，应由管理员预先镜像同一 commit，再扩展安装器的来源接口并记录镜像摘要，不能改用浮动 `master`。

### 2.1 推荐使用打包安装器

`install/install_gmx_stack.sh` 把本页的核心构建顺序固化为脚本。它默认只渲染计划，不建目录、不编译：

```bash
./install/install_gmx_stack.sh \
  --mode gpu \
  --prefix /data/apps/gmx-stack \
  --work-root /data/build/gmx-stack-work \
  --cuda-prefix /usr/local/cuda \
  --jobs 8
```

CPU-only 时可显式使用 `--mode cpu`，无需 CUDA 参数，但它仅适合诊断/零步 smoke，不能执行本包标记为生产 MD 的 profile。可先单独执行只读校验：

```bash
./install/install_gmx_stack.sh --verify-sources
```

审阅 plan 并确认目标目录为空、编译器与 CUDA 兼容后，才在同一命令末尾加入 `--execute`。脚本从不调用 sudo、从不安装 CUDA、从不修改 `.bashrc`，且会拒绝覆盖已有组件前缀。成功后会生成 `PREFIX/env.sh`；仍须完成本页第 7 节的目标机验收。

安装器默认在末尾执行包内的 0 步 GROMACS→PLUMED→`SASA_HASEL` 联调。GPU 只在无 GPU 的构建节点编译时，可用 `--defer-runtime-smoke` 延后，但该安装在计算节点运行下列命令成功前不能标记为 production-ready：

```bash
GMX_ENV_SCRIPT=/data/apps/gmx-stack/env.sh \
./tests/smoke_gmx_plumed.sh \
  --mode gpu --work-dir /scratch/gmx-plumed-sasa-smoke --execute
```

测试的 TPR 为 `nsteps=0`，只初始化 GROMACS/PLUMED/SASA 耦合并计算初始 CV，不进行采样；证据会保留在显式 work-dir。

若生产配置使用多 rank，还应在分配到的计算节点另跑一次同样的耦合测试，例如：

```bash
GMX_ENV_SCRIPT=/data/apps/gmx-stack/env.sh \
./tests/smoke_gmx_plumed.sh --mode gpu \
  --launcher mpirun --mpi-ranks 2 \
  --work-dir /scratch/gmx-plumed-sasa-smoke-mpi2 --execute
```

Slurm 站点可将 launcher 改为 `srun`。不要在登录节点占用未分配的 CPU/GPU。

### 2.2 安装失败与半安装状态

安装器会把 OpenMPI、FFTW、PLUMED 和 GROMACS 逐个写入新的版本化 prefix，因此它不是可原子回滚的包管理器。任一构建、test、`ldd` 或联调失败后：

- 保留 console/build/test 日志，记录本次 prefix 和 work-root；
- 不要 source 隐藏的 `.env.sh.candidate`，也不要手工把它改名为 `env.sh`；
- 不得把已写入的部分组件宣称为可用安装；
- 修复原因后使用全新、空的版本化 prefix 和 work-root 重新执行，将旧树隔离待审计；安装器有意拒绝在非空树上续建。

只有所有请求的验证成功后，候选环境才会原子改名为 `PREFIX/env.sh`。显式使用 `--defer-runtime-smoke` 时会在其他验证通过后发布 `env.sh`，但在计算节点补做联调前仍不是 production-ready。

## 3. 选择目标路径和构建配置

以下是示例，请换成目标系统上的显式绝对路径；路径不要包含空格：

```bash
export STACK_SRC=/data/build/gmx-stack-src
export STACK_PREFIX=/data/apps/gmx-stack
export BUILD_JOBS=8

export MPI_PREFIX="$STACK_PREFIX/openmpi-5.0.1"
export FFTW_PREFIX="$STACK_PREFIX/fftw-3.3.10"
export PLUMED_PREFIX="$STACK_PREFIX/plumed-2.9.3-sasa"
export GMX_PREFIX="$STACK_PREFIX/gromacs-2024.3-plumed-2.9.3"

export STACK_CC=/usr/bin/gcc
export STACK_CXX=/usr/bin/g++
export STACK_FC=/usr/bin/gfortran

mkdir -p "$STACK_SRC" "$STACK_PREFIX"
```

`BUILD_JOBS`、MPI ranks 与 OpenMP threads 必须服从调度器或 cgroup 的实际配额，不能依据宿主机总线程数盲目设置。所有组件应使用同一套 C/C++ ABI 和同一套 MPI。

## 4. 系统依赖与 CUDA

Ubuntu/Debian 的参考依赖如下；执行前由管理员审核：

```bash
sudo apt-get update
sudo apt-get install -y \
  build-essential gfortran perl python3 pkg-config git libnetcdf-dev \
  wget ca-certificates tar gzip bzip2 xz-utils patch \
  libhwloc-dev libevent-dev libnuma-dev zlib1g-dev
```

Rocky/Alma/RHEL 使用对应的 Development Tools、`gcc-c++`、`gcc-gfortran`、`hwloc-devel`、`libevent-devel`、`numactl-devel`、`zlib-devel`、`git` 和 `netcdf-devel`。

Agent 编排器和标准库工具要求 Python 3.8 或更高版本；阶段脚本使用 Bash nameref，因此要求 Bash 4.3 以上，并假设 Linux GNU `realpath`/coreutils/`sha256sum` 语义。安装后用 `python3 --version`、`bash --version` 与 `./agentctl verify-bundle` 实测，不能只依据发行版包名判断。

本包的平衡及生产动力学阶段都声明 `requires_device=gpu`；前置 `steep` 能量最小化使用 GROMACS 支持的自动任务路径，不强塞 MD 专用 GPU 参数。部署前由管理员安装兼容的 NVIDIA 驱动和 CUDA Toolkit，再检查：

```bash
nvidia-smi
/usr/local/cuda/bin/nvcc --version
```

`nvidia-smi` 显示的是驱动可支持的 CUDA API 上限，`nvcc` 才是实际编译 Toolkit。还要核对 Toolkit 支持的 host compiler。CPU-only 构建可使用 `GMX_GPU=OFF` 做安装诊断，但 `agentctl` 会阻止它启动冻结的长生产 profile。

若系统 CMake 太旧，x86_64 主机可解压包内归档并把其 `bin/` 临时加入 PATH；非 x86_64 主机不得使用该预编译包，应安装适合本架构的 CMake。

## 5. 构建顺序

### 5.1 OpenMPI 5.0.1

```bash
cd "$STACK_SRC"
tar -xjf /path/to/agent/install/sources/openmpi-5.0.1.tar.bz2
cd openmpi-5.0.1

CC="$STACK_CC" CXX="$STACK_CXX" FC="$STACK_FC" \
./configure --prefix="$MPI_PREFIX"
make -j"$BUILD_JOBS"
make install

export PATH="$MPI_PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="$MPI_PREFIX/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
mpicxx --showme:command
```

若明确需要 CUDA-aware MPI，可在重新配置时增加 `--with-cuda=/path/to/cuda`，并单独验证网络栈与 CUDA 支持。不要混用 OpenMPI、MPICH 或不同 OpenMPI 前缀。

### 5.2 单精度 FFTW 3.3.10

```bash
cd "$STACK_SRC"
tar -xzf /path/to/agent/install/sources/fftw-3.3.10.tar.gz
cd fftw-3.3.10

./configure \
  --prefix="$FFTW_PREFIX" \
  --enable-float \
  --enable-sse2 \
  --enable-avx2 \
  CC="$STACK_CC" CXX="$STACK_CXX" \
  CFLAGS=-fPIC CXXFLAGS=-fPIC
make -j"$BUILD_JOBS"
make check
make install
test -f "$FFTW_PREFIX/lib/libfftw3f.a"
```

只有目标 CPU 支持 AVX2 时才使用上述 SIMD 选项；其他架构应重新选择，不能复制当前二进制。

### 5.3 PLUMED 2.9.3，启用 SASA

必须从全新解压目录完整构建，不能复用当前主机的增量构建对象：

```bash
cd "$STACK_SRC"
tar -xzf /path/to/agent/install/sources/plumed2-2.9.3.tar.gz
cd plumed2-2.9.3

CC="$STACK_CC" CXX="$MPI_PREFIX/bin/mpicxx" FC="$STACK_FC" \
./configure \
  --prefix="$PLUMED_PREFIX" \
  --enable-modules=sasa
make -j"$BUILD_JOBS"
make install

export PATH="$PLUMED_PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="$PLUMED_PREFIX/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
```

候选安装必须通过下列检查，不能只检查版本字符串：

```bash
plumed info --long-version
plumed config show | grep 'module sasa on'
plumed gentemplate --action SASA_HASEL >/dev/null
plumed --has-mpi
make -C "$STACK_SRC/plumed2-2.9.3/regtest/sasa/rt-sasa-hasel" test
make -C "$STACK_SRC/plumed2-2.9.3/regtest/sasa/rt-sasa-LCPO" test
```

`plumed --has-mpi` 以退出码 0 表示成功，通常没有文本输出。

### 5.4 Patch 并构建 GROMACS 2024.3

先 patch，后第一次 CMake：

```bash
cd "$STACK_SRC"
tar -xzf /path/to/agent/install/sources/gromacs-2024.3.tar.gz
cd gromacs-2024.3

"$PLUMED_PREFIX/bin/plumed" patch -l | grep gromacs-2024.3
"$PLUMED_PREFIX/bin/plumed" patch -p -e gromacs-2024.3 -m shared
```

GPU 构建示例：

```bash
cmake -S . -B build \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$GMX_PREFIX" \
  -DCMAKE_C_COMPILER="$STACK_CC" \
  -DCMAKE_CXX_COMPILER="$STACK_CXX" \
  -DBUILD_SHARED_LIBS=ON \
  -DGMX_MPI=ON \
  -DGMX_THREAD_MPI=OFF \
  -DGMX_OPENMP=ON \
  -DGMX_GPU=CUDA \
  -DCUDA_TOOLKIT_ROOT_DIR=/usr/local/cuda \
  -DCUDA_HOST_COMPILER="$STACK_CXX" \
  -DGMX_GPU_FFT_LIBRARY=cuFFT \
  -DGMX_BUILD_OWN_FFTW=OFF \
  -DGMX_FFT_LIBRARY=fftw3 \
  -DFFTWF_LIBRARY="$FFTW_PREFIX/lib/libfftw3f.a" \
  -DFFTWF_INCLUDE_DIR="$FFTW_PREFIX/include" \
  -DGMX_SIMD=AUTO \
  -DGMX_BUILD_UNITTESTS=ON \
  -DMPI_C_COMPILER="$MPI_PREFIX/bin/mpicc" \
  -DMPI_CXX_COMPILER="$MPI_PREFIX/bin/mpicxx" \
  -DMPIEXEC_EXECUTABLE="$MPI_PREFIX/bin/mpiexec"

cmake --build build --parallel "$BUILD_JOBS"
ctest --test-dir build --output-on-failure -j "$BUILD_JOBS"
cmake --install build
```

CPU-only 时删除全部 CUDA/cuFFT 项，并设置 `-DGMX_GPU=OFF`。PLUMED 2.9.3 的该 shared patch 要求 external MPI，因此必须保留 `GMX_MPI=ON` 与 `GMX_THREAD_MPI=OFF`。

若 ctest 或 PLUMED regtest 失败，应保存日志并修复原因，不得跳过后宣布安装成功。

## 6. 环境文件与站点配置

创建独立且可重复 source 的环境文件，例如 `/data/apps/gmx-stack/env.sh`：

```bash
unset PLUMED_KERNEL
if [ "${GLP1_GMX_ENV_PREFIX:-}" != /data/apps/gmx-stack ]; then
  export MPI_PREFIX=/data/apps/gmx-stack/openmpi-5.0.1
  export PLUMED_PREFIX=/data/apps/gmx-stack/plumed-2.9.3-sasa
  export GMX_PREFIX=/data/apps/gmx-stack/gromacs-2024.3-plumed-2.9.3
  export PATH="$MPI_PREFIX/bin:$PLUMED_PREFIX/bin:$PATH"
  export LD_LIBRARY_PATH="$MPI_PREFIX/lib:$PLUMED_PREFIX/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  source "$GMX_PREFIX/bin/GMXRC"
  export GLP1_GMX_ENV_PREFIX=/data/apps/gmx-stack
fi
```

GPU 站点还应按实际 Toolkit 路径加入 CUDA 的 `bin` 和 `lib64`。不要把环境只放进交互式 `.bashrc`；批处理 shell 可能在 early return 前退出。

复制站点模板到部署包之外并编辑：

```bash
cp config/site.env.example /data/config/glp1-agent.site.env
```

至少设置：

```text
GMX_ENV_SCRIPT=/data/apps/gmx-stack/env.sh
GMX_BIN=gmx_mpi
PLUMED_BIN=plumed
GMX_LAUNCHER=direct        # 或 mpirun / srun
MPI_RANKS=1
OMP_THREADS=8
GMX_DEVICE_MODE=gpu        # 本包生产 MD 的强制模式
```

站点配置会在 `prepare` 时求值，并把白名单内的有效键值规范化后冻结到运行目录（不保存注释或无关 shell 变量）。应先定稿再 prepare；为避免混淆，工作根目录始终显式传 `--work-root`。

## 7. 新系统验收

先执行只读检查：

```bash
./agentctl \
  --site-config /data/config/glp1-agent.site.env \
  doctor --strict --require-mdpocket
```

完整 distance 或 `standardized-sasa-*-full` 部署的验收至少包括；若本次只部署模拟层，可暂时去掉 `--require-mdpocket`：

- `gmx_mpi --version` 为 2024.3、mixed、external MPI、OpenMP；
- `gmx_mpi mdrun -h` 含 `-plumed`；
- `gmx_mpi sasa -h` 含 `-surface` 与 `-output`；
- PLUMED 为 2.9.3，SASA module 和 `SASA_HASEL` 可用；
- 多 rank 配置时 PLUMED 必须通过 `--has-mpi`；
- `ldd` 没有 `not found`，并且没有加载另一套 MPI/PLUMED；
- GPU profile 能识别目标 GPU，CPU/MPI/GPU 资源未超配；
- 冻结输入、SASA 原子数和 DAT 内容验证通过；
- 在隔离临时目录完成 CPU、所需 MPI/GPU 以及 PLUMED/SASA 零步或短步 smoke test。

`doctor` 成功只表示前置检查满足，不等于科学流程或长模拟已经完成。部署完成后先阅读 [实验工作流](EXPERIMENT_WORKFLOW.md) 与 [科学决策](SCIENTIFIC_DECISIONS.md)，再决定是否开启执行门闩。

## 8. 从官方 fpocket 部署 MDpocket

MDpocket 是 [Discngine/fpocket 官方仓库](https://github.com/Discngine/fpocket)中的同套程序之一，不属于 GROMACS/PLUMED 栈。原实验没有留下可恢复的历史 commit，因此本包选择一个新的、明确可审计的部署基线：fpocket 4.2.3、commit `4bb0d8447f62fee77e2c3c29f54b5fcaf5e2c066`。这表示部署实现，不宣称它就是历史原版本。

该固定上游源码的 `src/mdparams.c` 为每个 argv 只分配了指针大小，长参数可触发堆越界；安装器不会绕过验收，而是应用一行最小修复 `strlen(argv)+1`。补丁是本包的可审计部署输入，SHA-256 为 `6ed7a0e8280f10ae0d42c42d771b4a3083e7891d007898bc19f7148bb433481d`；安装器同时验证应用后源文件摘要及唯一 dirty 文件集。

安装器默认仅显示计划，不联网、不建目录：

```bash
./install/install_fpocket.sh \
  --prefix /data/apps/fpocket-4.2.3 \
  --work-root /data/build/fpocket-4.2.3
```

确认目标为 Linux x86_64，系统已提供 GCC/G++、GNU make、Git 和 NetCDF C 开发库，再追加 `--execute`。安装器会：

- 从官方仓库浅克隆 tag 4.2.3，并校验完整 commit；
- 在任何网络或写入前校验包内补丁 SHA-256，并应用、复核唯一预期源码变更；
- 使用串行 `make -j1`，规避上游 qhull/object 并行规则竞态；
- 在候选用户前缀构建并安装 `fpocket/tpocket/dpocket/mdpocket`，不使用 sudo；
- 检查 NetCDF 编译/链接/运行、MDpocket 所需参数、XTC CLI 接口声明和 `ldd`；
- 在官方 10-PDB 样例上实运 discovery 与 selected-pocket，验证 DX 以及 10 行连续 snapshot/严格 42 列有限数描述符；
- 生成 `PREFIX/env.sh` 与 `PREFIX/share/fpocket/BUILDINFO.tsv`。

安装成功后，把 `env.sh` 输出的两个值复制到包外 site 配置：

```text
MDPOCKET_BIN=/data/apps/fpocket-4.2.3/bin/mdpocket
MDPOCKET_PROVENANCE="Discngine/fpocket tag 4.2.3 commit 4bb0d8447f62fee77e2c3c29f54b5fcaf5e2c066 bundle-patch-sha256 6ed7a0e8280f10ae0d42c42d771b4a3083e7891d007898bc19f7148bb433481d"
```

不要使用程序帮助横幅中的 `fpocket 4.0` 判断版本；该上游横幅没有随 tag 更新。以固定 Git commit 和 `BUILDINFO.tsv` 为证据。完整 distance 或 SASA full run 必须在 `prepare` 前安装完成并使用绝对 `MDPOCKET_BIN`；`prepare` 会冻结该二进制和 BUILDINFO 的 SHA-256，后续漂移会阻断执行。

完整 `historical-distance-main` 或 `standardized-sasa-*-full` 之前，还必须至少确认：

- `mdpocket` 帮助中提供 `--pdb_list` 与 `--selected_pocket`；
- discovery 运行产生 `mdpout_dens_grid.dx`；
- selected-pocket 运行产生 `mdpout_descriptors.txt`，其表头及顺序与历史 42 列 schema 完全一致；
- 42 列每个值均可解析为数值；`snapshot` 和 `pock_volume` 必须有限，其他列的 NaN/Inf 必须写入 QC 且不得插值；
- distance 为 501 帧，SASA 10/100 ns 为 101/1001 帧；snapshot 连续且约定为 `snapshot 1 = frame0 = 0 ps`。

安装器证明了来源、补丁、构建、CLI 接口及官方 PDB-list 小样例，但不等于实际读取 XTC 或对本实验各长度的完整功能验收。真实 MDpocket stage 仍会要求 discovery DX、1 Å 选区、严格 42 列 schema、关键列有限、辅助非有限值 QC 和精确连续 snapshot。部署未完成时使用 simulation-only profile；不要仅因 `command -v mdpocket` 成功就声称完整后处理已经验收。
