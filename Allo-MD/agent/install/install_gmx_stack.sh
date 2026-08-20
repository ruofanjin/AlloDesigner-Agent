#!/usr/bin/env bash
# Build a relocatable, user-prefix GROMACS/PLUMED stack from the archives
# shipped beside this script.  The default mode is deliberately a dry-run.

set -Eeuo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly BUNDLE_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"

readonly OPENMPI_VERSION="5.0.1"
readonly FFTW_VERSION="3.3.10"
readonly PLUMED_VERSION="2.9.3"
readonly GROMACS_VERSION="2024.3"
readonly CMAKE_VERSION="3.31.5"

readonly OPENMPI_ARCHIVE="openmpi-${OPENMPI_VERSION}.tar.bz2"
readonly FFTW_ARCHIVE="fftw-${FFTW_VERSION}.tar.gz"
readonly PLUMED_ARCHIVE="plumed2-${PLUMED_VERSION}.tar.gz"
readonly GROMACS_ARCHIVE="gromacs-${GROMACS_VERSION}.tar.gz"
readonly CMAKE_ARCHIVE="cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz"

execute=0
verify_only=0
mode="gpu"
prefix="${GMX_STACK_PREFIX:-${HOME:?HOME is not set}/opt/gmx-stack}"
work_root="${GMX_STACK_WORK_ROOT:-}"
jobs="${GMX_STACK_JOBS:-}"
cc="${GMX_CC:-gcc}"
cxx="${GMX_CXX:-g++}"
fc="${GMX_FC:-gfortran}"
cuda_prefix="${GMX_CUDA_PREFIX:-}"
cuda_sm=""
fftw_simd="auto"
mpi_internal_deps=0
mpi_cuda_aware=0
run_runtime_smoke=1

usage() {
  cat <<'EOF'
Usage:
  install/install_gmx_stack.sh [options]

The default is PLAN mode: commands are printed, but no directory is created
and no compiler, installer, or test is run.  Installation starts only with
the explicit --execute flag.

Options:
  --execute                  Verify archives, compile, test, and install
  --plan, --dry-run          Print the plan only (default)
  --verify-sources           Verify SHA256SUMS only; never install
  --mode cpu|gpu             Build CPU-only or CUDA-enabled GROMACS (gpu)
  --prefix PATH              User installation root ($HOME/opt/gmx-stack)
  --work-root PATH           Disposable source/build workspace
                             ($HOME/src/gmx-stack-work)
  --jobs N                   Parallel build/test jobs
                             (Slurm allocation or min(nproc, 8))
  --cc COMMAND               C compiler (gcc)
  --cxx COMMAND              C++ compiler (g++)
  --fc COMMAND               Fortran compiler (gfortran)
  --fftw-simd auto|avx2|portable
                             FFTW float SIMD policy (auto)
  --cuda-prefix PATH         Existing CUDA toolkit root; no CUDA is installed
  --cuda-sm LIST             Optional GMX_CUDA_TARGET_SM, e.g. 80 or 80;90
  --openmpi-internal-deps    Build Open MPI's bundled hwloc/libevent/PMIx/PRRTE
  --openmpi-cuda-aware       Configure Open MPI with --with-cuda=CUDA_PREFIX
  --defer-runtime-smoke      Install without the zero-step coupled smoke;
                             it must be run later on a suitable compute node
  -h, --help                 Show this help

Local, immutable inputs:
  install/sources/{openmpi-5.0.1,fftw-3.3.10,plumed2-2.9.3,
                   gromacs-2024.3,cmake-3.31.5-linux-x86_64}.tar.*
  install/SHA256SUMS

Installed component prefixes:
  PREFIX/openmpi-5.0.1
  PREFIX/fftw-3.3.10
  PREFIX/plumed-2.9.3-sasa
  PREFIX/gromacs-2024.3-plumed-2.9.3
  PREFIX/env.sh
EOF
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

warn() {
  printf 'WARNING: %s\n' "$*" >&2
}

need_arg() {
  [[ $# -ge 2 && -n ${2:-} ]] || die "$1 requires a value"
}

while (($#)); do
  case "$1" in
    --execute)
      execute=1
      ;;
    --plan|--dry-run)
      execute=0
      ;;
    --verify-sources)
      verify_only=1
      ;;
    --mode)
      need_arg "$@"; mode="$2"; shift
      ;;
    --prefix)
      need_arg "$@"; prefix="$2"; shift
      ;;
    --work-root)
      need_arg "$@"; work_root="$2"; shift
      ;;
    --jobs)
      need_arg "$@"; jobs="$2"; shift
      ;;
    --cc)
      need_arg "$@"; cc="$2"; shift
      ;;
    --cxx)
      need_arg "$@"; cxx="$2"; shift
      ;;
    --fc)
      need_arg "$@"; fc="$2"; shift
      ;;
    --fftw-simd)
      need_arg "$@"; fftw_simd="$2"; shift
      ;;
    --cuda-prefix)
      need_arg "$@"; cuda_prefix="$2"; shift
      ;;
    --cuda-sm)
      need_arg "$@"; cuda_sm="$2"; shift
      ;;
    --openmpi-internal-deps)
      mpi_internal_deps=1
      ;;
    --openmpi-cuda-aware)
      mpi_cuda_aware=1
      ;;
    --defer-runtime-smoke)
      run_runtime_smoke=0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      (($# == 0)) || die "unexpected positional arguments: $*"
      break
      ;;
    *)
      die "unknown option: $1 (use --help)"
      ;;
  esac
  shift
done

[[ $mode == cpu || $mode == gpu ]] || die "--mode must be cpu or gpu"
[[ $fftw_simd == auto || $fftw_simd == avx2 || $fftw_simd == portable ]] ||
  die "--fftw-simd must be auto, avx2, or portable"
[[ -z $jobs || $jobs =~ ^[1-9][0-9]*$ ]] || die "--jobs must be a positive integer"
[[ -z $cuda_sm || $cuda_sm =~ ^[0-9]+([,;][0-9]+)*$ ]] ||
  die "--cuda-sm must be a number or comma/semicolon-separated number list"
# CMake list syntax is semicolon-separated.  Accept commas as CLI convenience,
# but never forward an ambiguous comma-delimited value.
cuda_sm="${cuda_sm//,/;}"
(( mpi_cuda_aware == 0 )) || [[ $mode == gpu ]] ||
  die "--openmpi-cuda-aware is meaningful only with --mode gpu"

if [[ -z $jobs ]]; then
  if [[ ${SLURM_CPUS_PER_TASK:-} =~ ^[1-9][0-9]*$ ]]; then
    jobs="$SLURM_CPUS_PER_TASK"
  elif command -v nproc >/dev/null 2>&1; then
    detected_jobs="$(nproc)"
    if ((detected_jobs > 8)); then
      jobs=8
    else
      jobs="$detected_jobs"
    fi
  else
    jobs=1
  fi
fi

absolute_path() {
  local value=$1
  command -v realpath >/dev/null 2>&1 || die "realpath is required"
  realpath -m -- "$value"
}

prefix="$(absolute_path "$prefix")"
work_root="$(absolute_path "${work_root:-$HOME/src/gmx-stack-work}")"

validate_target_path() {
  local label=$1 value=$2
  [[ $value == /* ]] || die "$label must resolve to an absolute path"
  [[ $value != / ]] || die "$label must not be /"
  [[ $value != *[$'\n\r\t ']* ]] || die "$label must not contain whitespace: $value"
}

validate_target_path "prefix" "$prefix"
validate_target_path "work root" "$work_root"
paths_overlap() {
  local left=${1%/} right=${2%/}
  [[ $left == "$right" || $left == "$right"/* || $right == "$left"/* ]]
}
if paths_overlap "$work_root" "$prefix"; then
  die "work root and install prefix must be separate, non-nested trees"
fi
if paths_overlap "$work_root" "$BUNDLE_ROOT" || paths_overlap "$prefix" "$BUNDLE_ROOT"; then
  die "work/install targets must not overlap the immutable agent bundle"
fi
case "$prefix" in
  /usr|/usr/local|/opt|/var|/etc) die "refusing broad/system prefix: $prefix" ;;
esac
if [[ $prefix != "$HOME"/* ]]; then
  warn "prefix is outside HOME; this script still never invokes sudo: $prefix"
fi

readonly SOURCES_DIR="$SCRIPT_DIR/sources"
readonly CHECKSUM_FILE="$SCRIPT_DIR/SHA256SUMS"

readonly MPI_PREFIX="$prefix/openmpi-${OPENMPI_VERSION}"
readonly FFTW_PREFIX="$prefix/fftw-${FFTW_VERSION}"
readonly PLUMED_PREFIX="$prefix/plumed-${PLUMED_VERSION}-sasa"
readonly GMX_PREFIX="$prefix/gromacs-${GROMACS_VERSION}-plumed-${PLUMED_VERSION}"
readonly ENV_SCRIPT="$prefix/env.sh"
readonly ENV_SCRIPT_CANDIDATE="$prefix/.env.sh.candidate"

readonly SRC_ROOT="$work_root/src"
readonly BUILD_ROOT="$work_root/build"
readonly PATCHED_ROOT="$work_root/patched-src"
readonly TOOLS_ROOT="$work_root/tools"
readonly MPI_SOURCE="$SRC_ROOT/openmpi-${OPENMPI_VERSION}"
readonly FFTW_SOURCE="$SRC_ROOT/fftw-${FFTW_VERSION}"
readonly PLUMED_SOURCE="$SRC_ROOT/plumed-${PLUMED_VERSION}"
readonly GMX_SOURCE="$SRC_ROOT/gromacs-${GROMACS_VERSION}"
readonly MPI_BUILD="$BUILD_ROOT/openmpi-${OPENMPI_VERSION}"
readonly FFTW_BUILD="$BUILD_ROOT/fftw-${FFTW_VERSION}"
readonly PLUMED_BUILD="$BUILD_ROOT/plumed-${PLUMED_VERSION}-sasa"
readonly GMX_PATCHED_SOURCE="$PATCHED_ROOT/gromacs-${GROMACS_VERSION}-plumed-${PLUMED_VERSION}"
readonly GMX_BUILD="$BUILD_ROOT/gromacs-${GROMACS_VERSION}-plumed-${PLUMED_VERSION}"
readonly CMAKE_ROOT="$TOOLS_ROOT/cmake-${CMAKE_VERSION}-linux-x86_64"
readonly CMAKE_BIN="$CMAKE_ROOT/bin/cmake"
readonly CTEST_BIN="$CMAKE_ROOT/bin/ctest"

for archive in \
  "$OPENMPI_ARCHIVE" "$FFTW_ARCHIVE" "$PLUMED_ARCHIVE" \
  "$GROMACS_ARCHIVE" "$CMAKE_ARCHIVE"; do
  [[ -r "$SOURCES_DIR/$archive" ]] || die "missing local archive: $SOURCES_DIR/$archive"
done
[[ -r $CHECKSUM_FILE ]] || die "missing checksum manifest: $CHECKSUM_FILE"

verify_sources() {
  command -v sha256sum >/dev/null 2>&1 || die "sha256sum is required"
  printf '==> Verifying bundled archives with %s\n' "$CHECKSUM_FILE"
  (cd -- "$SCRIPT_DIR" && sha256sum -c "$(basename -- "$CHECKSUM_FILE")")
}

if ((verify_only)); then
  verify_sources
  printf 'Source verification complete; no installation was attempted.\n'
  exit 0
fi

resolve_tool() {
  local tool=$1 found
  if found="$(command -v -- "$tool" 2>/dev/null)"; then
    absolute_path "$found"
  elif [[ $tool == */* ]]; then
    absolute_path "$tool"
  else
    printf '%s\n' "$tool"
  fi
}

cc="$(resolve_tool "$cc")"
cxx="$(resolve_tool "$cxx")"
fc="$(resolve_tool "$fc")"

tool_directory() {
  local tool=$1
  if [[ $tool == */* ]]; then
    printf '%s\n' "${tool%/*}"
  else
    printf '%s\n' /usr/bin
  fi
}

# Do not let an already loaded GROMACS/PLUMED stack in an interactive shell
# leak into the new build.  Custom compilers remain reachable by directory.
build_base_path="/usr/local/bin:/usr/bin:/bin"
for compiler in "$cc" "$cxx" "$fc"; do
  compiler_dir="$(tool_directory "$compiler")"
  case ":$build_base_path:" in
    *":$compiler_dir:"*) ;;
    *) build_base_path="$compiler_dir:$build_base_path" ;;
  esac
done
clean_env=(
  env
  -u CPATH
  -u C_INCLUDE_PATH
  -u CPLUS_INCLUDE_PATH
  -u LIBRARY_PATH
  -u PKG_CONFIG_PATH
  -u CMAKE_PREFIX_PATH
  -u PLUMED_KERNEL
)

if [[ $mode == gpu ]]; then
  if [[ -z $cuda_prefix ]]; then
    if nvcc_path="$(command -v nvcc 2>/dev/null)"; then
      cuda_prefix="$(cd -- "$(dirname -- "$nvcc_path")/.." && pwd -P)"
    elif [[ -x /usr/local/cuda/bin/nvcc ]]; then
      cuda_prefix="/usr/local/cuda"
    else
      cuda_prefix="/usr/local/cuda"
      warn "CUDA was not detected; supply --cuda-prefix before --execute"
    fi
  fi
  cuda_prefix="$(absolute_path "$cuda_prefix")"
  validate_target_path "CUDA prefix" "$cuda_prefix"
  build_base_path="$cuda_prefix/bin:$build_base_path"
fi

fftw_simd_args=()
case "$fftw_simd" in
  avx2)
    fftw_simd_args+=(--enable-sse2 --enable-avx2)
    ;;
  portable)
    ;;
  auto)
    if [[ $(uname -m) =~ ^(x86_64|amd64|i[3-6]86)$ ]] &&
       grep -qm1 -w avx2 /proc/cpuinfo 2>/dev/null; then
      fftw_simd_args+=(--enable-sse2 --enable-avx2)
    elif [[ $(uname -m) =~ ^(x86_64|amd64|i[3-6]86)$ ]] &&
         grep -qm1 -w sse2 /proc/cpuinfo 2>/dev/null; then
      fftw_simd_args+=(--enable-sse2)
    fi
    ;;
esac

mpi_configure_args=(
  "--prefix=$MPI_PREFIX"
  "--libdir=$MPI_PREFIX/lib"
)
if ((mpi_internal_deps)); then
  mpi_configure_args+=(
    --with-libevent=internal
    --with-hwloc=internal
    --with-pmix=internal
    --with-prrte=internal
  )
fi
if ((mpi_cuda_aware)); then
  mpi_configure_args+=("--with-cuda=$cuda_prefix")
fi

fftw_configure_args=(
  "--prefix=$FFTW_PREFIX"
  "--libdir=$FFTW_PREFIX/lib"
  --enable-float
  "${fftw_simd_args[@]}"
)

plumed_configure_args=(
  "--prefix=$PLUMED_PREFIX"
  "--libdir=$PLUMED_PREFIX/lib"
  --enable-modules=sasa
)

gmx_cmake_args=(
  -S "$GMX_PATCHED_SOURCE"
  -B "$GMX_BUILD"
  -DCMAKE_BUILD_TYPE=Release
  "-DCMAKE_INSTALL_PREFIX=$GMX_PREFIX"
  -DCMAKE_INSTALL_LIBDIR=lib
  "-DCMAKE_C_COMPILER=$cc"
  "-DCMAKE_CXX_COMPILER=$cxx"
  -DBUILD_SHARED_LIBS=ON
  -DGMX_MPI=ON
  -DGMX_THREAD_MPI=OFF
  -DGMX_OPENMP=ON
  -DGMX_BUILD_OWN_FFTW=OFF
  -DGMX_FFT_LIBRARY=fftw3
  "-DFFTWF_LIBRARY=$FFTW_PREFIX/lib/libfftw3f.a"
  "-DFFTWF_INCLUDE_DIR=$FFTW_PREFIX/include"
  -DGMX_SIMD=AUTO
  -DGMX_BUILD_UNITTESTS=ON
  -DGMX_DOWNLOAD_REGRESSIONTESTS=OFF
  "-DMPI_C_COMPILER=$MPI_PREFIX/bin/mpicc"
  "-DMPI_CXX_COMPILER=$MPI_PREFIX/bin/mpicxx"
  "-DMPIEXEC_EXECUTABLE=$MPI_PREFIX/bin/mpiexec"
  "-DCMAKE_PREFIX_PATH=$MPI_PREFIX;$FFTW_PREFIX;$PLUMED_PREFIX"
  "-DCMAKE_BUILD_RPATH=$MPI_PREFIX/lib;$PLUMED_PREFIX/lib"
  "-DCMAKE_INSTALL_RPATH=$MPI_PREFIX/lib;$PLUMED_PREFIX/lib"
)
if [[ $mode == gpu ]]; then
  gmx_cmake_args+=(
    -DGMX_GPU=CUDA
    "-DCUDA_TOOLKIT_ROOT_DIR=$cuda_prefix"
    "-DCUDA_HOST_COMPILER=$cxx"
    -DGMX_GPU_FFT_LIBRARY=cuFFT
  )
  [[ -z $cuda_sm ]] || gmx_cmake_args+=("-DGMX_CUDA_TARGET_SM=$cuda_sm")
else
  gmx_cmake_args+=(-DGMX_GPU=OFF)
fi

print_command() {
  printf '  '
  printf '%q ' "$@"
  printf '\n'
}

run_cmd() {
  print_command "$@"
  if ((execute)); then
    "$@"
  fi
}

run_in() {
  local directory=$1
  shift
  printf '  (cd %q && ' "$directory"
  printf '%q ' "$@"
  printf ')\n'
  if ((execute)); then
    (cd -- "$directory" && "$@")
  fi
}

extract_archive() {
  local archive=$1 destination=$2
  run_cmd mkdir -p -- "$destination"
  run_cmd tar -xf "$SOURCES_DIR/$archive" --strip-components=1 -C "$destination"
}

check_execute_prerequisites() {
  local tool
  [[ -z ${GMX_MAXCONSTRWARN:-} ]] ||
    die "refusing inherited GMX_MAXCONSTRWARN; fix constraint warnings instead"
  for tool in env tar gzip bzip2 make patch sha256sum realpath cp grep awk sed \
              pkg-config ldd perl python3; do
    command -v "$tool" >/dev/null 2>&1 || die "required command not found: $tool"
  done
  for tool in "$cc" "$cxx" "$fc"; do
    [[ -x $tool ]] || die "compiler is not executable: $tool"
  done
  [[ $(uname -m) =~ ^(x86_64|amd64)$ ]] ||
    die "the bundled CMake archive is x86_64; use this installer on x86_64"
  if [[ -e $work_root ]] &&
     find "$work_root" -mindepth 1 -maxdepth 1 -print -quit | grep -q .; then
    die "work root is not empty; choose a fresh --work-root: $work_root"
  fi
  local target
  for target in "$MPI_PREFIX" "$FFTW_PREFIX" "$PLUMED_PREFIX" "$GMX_PREFIX" \
                "$ENV_SCRIPT" "$ENV_SCRIPT_CANDIDATE"; do
    [[ ! -e $target ]] || die "refusing to overwrite existing installation: $target"
  done
  if [[ $mode == gpu ]]; then
    [[ -x $cuda_prefix/bin/nvcc ]] ||
      die "CUDA nvcc not found at $cuda_prefix/bin/nvcc; install/provide CUDA externally"
    if command -v nvidia-smi >/dev/null 2>&1; then
      printf '==> CUDA driver probe (informational; no driver/toolkit is installed)\n'
      nvidia-smi --query-gpu=name,driver_version --format=csv,noheader ||
        warn "nvidia-smi exists but no GPU is visible on this host"
    else
      warn "nvidia-smi is unavailable; compile may proceed, but test the driver on a GPU node"
    fi
    "$cuda_prefix/bin/nvcc" --version
  fi
  if ((EUID == 0)); then
    warn "building as root is discouraged; prefer an unprivileged account and user prefix"
  fi
}

write_env_script() {
  if ((!execute)); then
    printf '  stage environment candidate %q; publish %q only after validation\n' \
      "$ENV_SCRIPT_CANDIDATE" "$ENV_SCRIPT"
    return
  fi

  local tmp="$ENV_SCRIPT_CANDIDATE.tmp.$$"
  umask 022
  {
    printf '# Generated by install_gmx_stack.sh; source this file explicitly.\n'
    printf '# It deliberately defines no aliases and does not edit ~/.bashrc.\n'
    printf 'unset PLUMED_KERNEL\n'
    printf 'if [[ ${GMX_STACK_2024_3_PLUMED_2_9_3_PREFIX:-} != %q ]]; then\n' "$prefix"
    printf '  export GMX_MPI_PREFIX=%q\n' "$MPI_PREFIX"
    printf '  export GMX_FFTW_PREFIX=%q\n' "$FFTW_PREFIX"
    printf '  export GMX_PLUMED_PREFIX=%q\n' "$PLUMED_PREFIX"
    printf '  export GMX_INSTALL_PREFIX=%q\n' "$GMX_PREFIX"
    if [[ $mode == gpu ]]; then
      printf '  export GMX_CUDA_PREFIX=%q\n' "$cuda_prefix"
      printf '  export PATH="$GMX_INSTALL_PREFIX/bin:$GMX_PLUMED_PREFIX/bin:$GMX_MPI_PREFIX/bin:$GMX_CUDA_PREFIX/bin${PATH:+:$PATH}"\n'
      printf '  export LD_LIBRARY_PATH="$GMX_INSTALL_PREFIX/lib:$GMX_PLUMED_PREFIX/lib:$GMX_MPI_PREFIX/lib:$GMX_CUDA_PREFIX/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"\n'
    else
      printf '  export PATH="$GMX_INSTALL_PREFIX/bin:$GMX_PLUMED_PREFIX/bin:$GMX_MPI_PREFIX/bin${PATH:+:$PATH}"\n'
      printf '  export LD_LIBRARY_PATH="$GMX_INSTALL_PREFIX/lib:$GMX_PLUMED_PREFIX/lib:$GMX_MPI_PREFIX/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"\n'
    fi
    printf '  source "$GMX_INSTALL_PREFIX/bin/GMXRC"\n'
    printf '  export GMX_BIN="$GMX_INSTALL_PREFIX/bin/gmx_mpi"\n'
    printf '  export PLUMED_BIN="$GMX_PLUMED_PREFIX/bin/plumed"\n'
    printf '  export GMX_STACK_ENV_SCRIPT=%q\n' "$ENV_SCRIPT"
    printf '  export GMX_STACK_2024_3_PLUMED_2_9_3_PREFIX=%q\n' "$prefix"
    printf 'fi\n'
  } >"$tmp"
  chmod 0644 "$tmp"
  mv -- "$tmp" "$ENV_SCRIPT_CANDIDATE"
}

assert_output() {
  local pattern=$1
  shift
  printf '  '
  printf '%q ' "$@"
  printf '2>&1 | grep -E %q\n' "$pattern"
  if ((execute)); then
    local output
    if ! output="$("$@" 2>&1)"; then
      printf '%s\n' "$output" >&2
      die "validation command failed: $*"
    fi
    printf '%s\n' "$output"
    grep -Eq -- "$pattern" <<<"$output" || die "validation pattern not found: $pattern"
  fi
}

check_ldd() {
  local target=$1 loader_path=${2:-}
  printf '  ldd %q | assert-no-not-found\n' "$target"
  if ((execute)); then
    local output
    output="$(env "LD_LIBRARY_PATH=$loader_path" ldd "$target")"
    printf '%s\n' "$output"
    ! grep -q 'not found' <<<"$output" || die "missing dynamic library for $target"
  fi
}

validate_install() {
  local validation_path="$GMX_PREFIX/bin:$PLUMED_PREFIX/bin:$MPI_PREFIX/bin:$build_base_path"
  local validation_ld="$GMX_PREFIX/lib:$PLUMED_PREFIX/lib:$MPI_PREFIX/lib"
  [[ $mode == cpu ]] || validation_ld="$validation_ld:$cuda_prefix/lib64"
  local -a validation_env=(env "PATH=$validation_path" "LD_LIBRARY_PATH=$validation_ld")

  printf '\n==> Installed-stack validation\n'
  run_cmd bash -n "$ENV_SCRIPT_CANDIDATE"
  assert_output '2024\.3' env -u LD_LIBRARY_PATH -u GMX_STACK_2024_3_PLUMED_2_9_3_PREFIX \
    bash --noprofile --norc -c 'source "$1"; "$GMX_BIN" --version' _ "$ENV_SCRIPT_CANDIDATE"
  assert_output '5\.0\.1' "${validation_env[@]}" "$MPI_PREFIX/bin/mpirun" --version
  run_cmd "${validation_env[@]}" "$MPI_PREFIX/bin/mpicc" --showme
  run_cmd "${validation_env[@]}" "$MPI_PREFIX/bin/mpicxx" --showme
  assert_output '2\.9\.3' "${validation_env[@]}" "$PLUMED_PREFIX/bin/plumed" info --long-version
  assert_output 'module[[:space:]]+sasa[[:space:]]+on' "${validation_env[@]}" "$PLUMED_PREFIX/bin/plumed" config show
  assert_output 'SASA_(HASEL|LCPO)' "${validation_env[@]}" "$PLUMED_PREFIX/bin/plumed" gentemplate --list
  run_cmd "${validation_env[@]}" "$PLUMED_PREFIX/bin/plumed" gentemplate --action SASA_HASEL
  run_cmd "${validation_env[@]}" "$PLUMED_PREFIX/bin/plumed" gentemplate --action SASA_LCPO
  run_cmd "${validation_env[@]}" "$PLUMED_PREFIX/bin/plumed" --has-mpi
  assert_output '2024\.3' "${validation_env[@]}" "$GMX_PREFIX/bin/gmx_mpi" --version
  assert_output 'Precision:[[:space:]]*mixed' "${validation_env[@]}" "$GMX_PREFIX/bin/gmx_mpi" --version
  assert_output 'MPI library:|MPI support:' "${validation_env[@]}" "$GMX_PREFIX/bin/gmx_mpi" --version
  if [[ $mode == gpu ]]; then
    assert_output 'GPU support:[[:space:]]*(CUDA|enabled)' "${validation_env[@]}" "$GMX_PREFIX/bin/gmx_mpi" --version
  else
    assert_output 'GPU support:[[:space:]]*disabled' "${validation_env[@]}" "$GMX_PREFIX/bin/gmx_mpi" --version
  fi
  assert_output '(^|[[:space:]])-plumed([[:space:]]|$)' "${validation_env[@]}" "$GMX_PREFIX/bin/gmx_mpi" mdrun -h
  check_ldd "$GMX_PREFIX/bin/gmx_mpi" "$validation_ld"
  if ((execute)); then
    local plumed_library=""
    plumed_library="$(find "$PLUMED_PREFIX/lib" -maxdepth 1 -type f -name 'libplumed*.so*' -print -quit)"
    [[ -n $plumed_library ]] || die "installed PLUMED shared library was not found"
    check_ldd "$plumed_library" "$validation_ld"
  else
    printf '  ldd %q/lib/libplumed*.so* | assert-no-not-found\n' "$PLUMED_PREFIX"
  fi
}

printf 'GROMACS/PLUMED stack installer: %s\n' "$([[ $execute == 1 ]] && printf EXECUTE || printf PLAN)"
printf '  bundle:      %s\n' "$BUNDLE_ROOT"
printf '  mode:        %s\n' "$mode"
printf '  prefix:      %s\n' "$prefix"
printf '  work root:   %s\n' "$work_root"
printf '  jobs:        %s\n' "$jobs"
printf '  compilers:   CC=%s CXX=%s FC=%s\n' "$cc" "$cxx" "$fc"
printf '  FFTW SIMD:   %s (%s)\n' "$fftw_simd" "${fftw_simd_args[*]:-portable}"
if [[ $mode == gpu ]]; then
  printf '  CUDA:        %s (external; never installed by this script)\n' "$cuda_prefix"
  printf '  CUDA SM:     %s\n' "${cuda_sm:-auto-detect at CMake/runtime}"
fi
if ((!execute)); then
  printf '  safety:      dry-run; add --execute to permit filesystem/build changes\n'
fi

if ((execute)); then
  check_execute_prerequisites
  verify_sources
else
  printf '\n==> Archive integrity (planned before any mkdir/build)\n'
  print_command bash -c "cd $(printf '%q' "$SCRIPT_DIR") && sha256sum -c SHA256SUMS"
fi

printf '\n==> Create separated source/build/install layout\n'
run_cmd mkdir -p -- "$prefix" "$SRC_ROOT" "$BUILD_ROOT" "$PATCHED_ROOT" "$TOOLS_ROOT"

printf '\n==> Extract immutable source snapshots and bundled CMake\n'
extract_archive "$OPENMPI_ARCHIVE" "$MPI_SOURCE"
extract_archive "$FFTW_ARCHIVE" "$FFTW_SOURCE"
extract_archive "$PLUMED_ARCHIVE" "$PLUMED_SOURCE"
extract_archive "$GROMACS_ARCHIVE" "$GMX_SOURCE"
extract_archive "$CMAKE_ARCHIVE" "$CMAKE_ROOT"
assert_output "${CMAKE_VERSION//./\\.}" "$CMAKE_BIN" --version

printf '\n==> Build and install Open MPI %s\n' "$OPENMPI_VERSION"
run_cmd mkdir -p -- "$MPI_BUILD"
run_in "$MPI_BUILD" "${clean_env[@]}" "PATH=$build_base_path" "LD_LIBRARY_PATH=" \
  "CC=$cc" "CXX=$cxx" "FC=$fc" \
  "$MPI_SOURCE/configure" "${mpi_configure_args[@]}"
run_cmd "${clean_env[@]}" "PATH=$build_base_path" "LD_LIBRARY_PATH=" \
  make -C "$MPI_BUILD" -j"$jobs"
run_cmd "${clean_env[@]}" "PATH=$build_base_path" "LD_LIBRARY_PATH=" \
  make -C "$MPI_BUILD" install
assert_output '5\.0\.1' env "PATH=$MPI_PREFIX/bin:$build_base_path" \
  "LD_LIBRARY_PATH=$MPI_PREFIX/lib" "$MPI_PREFIX/bin/mpirun" --version
run_cmd env "PATH=$MPI_PREFIX/bin:$build_base_path" "LD_LIBRARY_PATH=$MPI_PREFIX/lib" \
  "$MPI_PREFIX/bin/mpicxx" --showme:command

printf '\n==> Build, check, and install single-precision FFTW %s\n' "$FFTW_VERSION"
run_cmd mkdir -p -- "$FFTW_BUILD"
run_in "$FFTW_BUILD" "${clean_env[@]}" "PATH=$build_base_path" "LD_LIBRARY_PATH=" \
  "CC=$cc" "CXX=$cxx" CFLAGS=-fPIC CXXFLAGS=-fPIC \
  "$FFTW_SOURCE/configure" "${fftw_configure_args[@]}"
run_cmd "${clean_env[@]}" "PATH=$build_base_path" "LD_LIBRARY_PATH=" \
  make -C "$FFTW_BUILD" -j"$jobs"
run_cmd "${clean_env[@]}" "PATH=$build_base_path" "LD_LIBRARY_PATH=" \
  make -C "$FFTW_BUILD" check -j"$jobs"
run_cmd "${clean_env[@]}" "PATH=$build_base_path" "LD_LIBRARY_PATH=" \
  make -C "$FFTW_BUILD" install
run_cmd test -f "$FFTW_PREFIX/lib/libfftw3f.a"

runtime_path="$MPI_PREFIX/bin:$build_base_path"
runtime_ld="$MPI_PREFIX/lib"
[[ $mode == cpu ]] || runtime_ld="$runtime_ld:$cuda_prefix/lib64"

printf '\n==> Build PLUMED %s with MPI and the SASA module\n' "$PLUMED_VERSION"
# PLUMED's recursive makefiles expect an in-tree layout.  Build only in a
# disposable copy, leaving SRC_ROOT pristine and INSTALL_PREFIX separate.
run_cmd mkdir -p -- "$PLUMED_BUILD"
run_cmd cp -a -- "$PLUMED_SOURCE/." "$PLUMED_BUILD/"
run_in "$PLUMED_BUILD" "${clean_env[@]}" "PATH=$runtime_path" "LD_LIBRARY_PATH=$runtime_ld" \
  "CC=$cc" "CXX=$MPI_PREFIX/bin/mpicxx" "FC=$fc" \
  ./configure "${plumed_configure_args[@]}"
run_cmd "${clean_env[@]}" "PATH=$runtime_path" "LD_LIBRARY_PATH=$runtime_ld" \
  make -C "$PLUMED_BUILD" -j"$jobs"
run_cmd "${clean_env[@]}" "PATH=$runtime_path" \
  "LD_LIBRARY_PATH=$PLUMED_BUILD/src/lib:$runtime_ld" \
  "PLUMED_PREPEND_PATH=$PLUMED_BUILD/src/lib" \
  make -C "$PLUMED_BUILD/regtest/sasa/rt-sasa-hasel" test
run_cmd "${clean_env[@]}" "PATH=$runtime_path" \
  "LD_LIBRARY_PATH=$PLUMED_BUILD/src/lib:$runtime_ld" \
  "PLUMED_PREPEND_PATH=$PLUMED_BUILD/src/lib" \
  make -C "$PLUMED_BUILD/regtest/sasa/rt-sasa-LCPO" test
run_cmd "${clean_env[@]}" "PATH=$runtime_path" "LD_LIBRARY_PATH=$runtime_ld" \
  make -C "$PLUMED_BUILD" install

runtime_path="$PLUMED_PREFIX/bin:$MPI_PREFIX/bin:$build_base_path"
runtime_ld="$PLUMED_PREFIX/lib:$MPI_PREFIX/lib"
[[ $mode == cpu ]] || runtime_ld="$runtime_ld:$cuda_prefix/lib64"

assert_output '2\.9\.3' env "PATH=$runtime_path" "LD_LIBRARY_PATH=$runtime_ld" \
  "$PLUMED_PREFIX/bin/plumed" info --long-version
assert_output 'module[[:space:]]+sasa[[:space:]]+on' env \
  "PATH=$runtime_path" "LD_LIBRARY_PATH=$runtime_ld" \
  "$PLUMED_PREFIX/bin/plumed" config show
run_cmd env "PATH=$runtime_path" "LD_LIBRARY_PATH=$runtime_ld" \
  "$PLUMED_PREFIX/bin/plumed" --has-mpi
assert_output 'gromacs-2024\.3' env "PATH=$runtime_path" "LD_LIBRARY_PATH=$runtime_ld" \
  "$PLUMED_PREFIX/bin/plumed" patch -l

printf '\n==> Create a writable GROMACS source copy and apply PLUMED shared patch\n'
run_cmd mkdir -p -- "$GMX_PATCHED_SOURCE"
run_cmd cp -a -- "$GMX_SOURCE/." "$GMX_PATCHED_SOURCE/"
run_in "$GMX_PATCHED_SOURCE" "${clean_env[@]}" "PATH=$runtime_path" "LD_LIBRARY_PATH=$runtime_ld" \
  "$PLUMED_PREFIX/bin/plumed" patch -p -e "gromacs-${GROMACS_VERSION}" -m shared

printf '\n==> Configure, build, test, and install GROMACS %s\n' "$GROMACS_VERSION"
run_cmd mkdir -p -- "$GMX_BUILD"
run_cmd "${clean_env[@]}" "PATH=$runtime_path" "LD_LIBRARY_PATH=$runtime_ld" \
  "$CMAKE_BIN" "${gmx_cmake_args[@]}"
run_cmd "${clean_env[@]}" "PATH=$runtime_path" "LD_LIBRARY_PATH=$runtime_ld" \
  "$CMAKE_BIN" --build "$GMX_BUILD" --parallel "$jobs"
run_cmd "${clean_env[@]}" "PATH=$runtime_path" "LD_LIBRARY_PATH=$runtime_ld" \
  "$CTEST_BIN" --test-dir "$GMX_BUILD" --output-on-failure -j "$jobs"
run_cmd "${clean_env[@]}" "PATH=$runtime_path" "LD_LIBRARY_PATH=$runtime_ld" \
  "$CMAKE_BIN" --install "$GMX_BUILD"

printf '\n==> Generate an independent runtime environment\n'
write_env_script

validate_install

if ((run_runtime_smoke)); then
  printf '\n==> Zero-step GROMACS -> PLUMED -> SASA integration smoke\n'
  run_cmd env "GMX_ENV_SCRIPT=$ENV_SCRIPT_CANDIDATE" "GMX_DEVICE_MODE=$mode" \
    "$BUNDLE_ROOT/tests/smoke_gmx_plumed.sh" --execute --mode "$mode" \
    --work-dir "$work_root/smoke-gmx-plumed-sasa"
else
  warn "coupled runtime smoke deferred; installation is not production-ready until tests/smoke_gmx_plumed.sh passes"
fi

printf '\n==> Publish runtime environment only after requested validation\n'
run_cmd mv -- "$ENV_SCRIPT_CANDIDATE" "$ENV_SCRIPT"

if ((execute)); then
  printf '\nInstallation complete.  Activate it with:\n  source %q\n' "$ENV_SCRIPT"
  printf 'Then validate the deployment bundle with:\n'
  printf '  GMX_ENV_SCRIPT=%q GMX_DEVICE_MODE=%q %q/agentctl doctor --strict\n' \
    "$ENV_SCRIPT" "$mode" "$BUNDLE_ROOT"
else
  printf '\nPLAN complete: nothing was installed or modified.\n'
  printf 'Review the paths/options above, then rerun with --execute.\n'
fi
