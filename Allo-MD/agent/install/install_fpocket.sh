#!/usr/bin/env bash
# Install the official Discngine/fpocket suite, including mdpocket, into a
# user-owned prefix.  The default mode is deliberately a side-effect-free plan.

set -Eeuo pipefail
umask 022

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly BUNDLE_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"

# Pin both the public release tag and the object ID.  A moved/recreated tag is
# rejected instead of silently changing the analysis implementation.
readonly FPOCKET_VERSION="4.2.3"
readonly FPOCKET_TAG="4.2.3"
readonly FPOCKET_COMMIT="4bb0d8447f62fee77e2c3c29f54b5fcaf5e2c066"
readonly FPOCKET_REPOSITORY="https://github.com/Discngine/fpocket.git"
readonly FPOCKET_PATCH_NAME="fpocket-4.2.3-mdparams-argv-allocation.patch"
readonly FPOCKET_PATCH="$SCRIPT_DIR/patches/$FPOCKET_PATCH_NAME"
readonly FPOCKET_PATCH_SHA256="6ed7a0e8280f10ae0d42c42d771b4a3083e7891d007898bc19f7148bb433481d"
readonly PATCHED_MDPARAMS_SHA256="e2bff1096c833083567fd626319161f2b6e06e7d7878dc9c073c77ba4ea1d8c8"
readonly FPOCKET_PATCH_DESCRIPTION="fix mdparams argv-copy allocation to strlen(argv)+1"
readonly MDPOCKET_DESCRIPTOR_HEADER="snapshot pock_volume pock_asa pock_pol_asa pock_apol_asa pock_asa22 pock_pol_asa22 pock_apol_asa22 nb_AS mean_as_ray mean_as_solv_acc apol_as_prop mean_loc_hyd_dens hydrophobicity_score volume_score polarity_score charge_score prop_polar_atm as_density as_max_dst convex_hull_volume nb_abpa ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL"

execute=0
prefix="${FPOCKET_PREFIX:-}"
work_root="${FPOCKET_WORK_ROOT:-}"
cc="${FPOCKET_CC:-gcc}"
cxx="${FPOCKET_CXX:-g++}"

usage() {
    cat <<'EOF'
Usage:
  install/install_fpocket.sh [options]

Default: PLAN mode.  It prints the pinned source, requirements, paths, and
commands without creating a directory, accessing the network, or compiling.
Installation starts only with the explicit --execute flag.

Options:
  --execute          Clone the pinned source, build, validate, and install
  --plan, --dry-run  Print the plan only (default)
  --prefix PATH      Final user prefix ($HOME/opt/fpocket-4.2.3)
  --work-root PATH   New source/build directory
                     ($HOME/src/fpocket-4.2.3-build)
  --cc COMMAND       C compiler executable (gcc)
  --cxx COMMAND      C++ compiler executable (g++)
  -h, --help         Show this help

Pinned upstream:
  repository: https://github.com/Discngine/fpocket.git
  tag:        4.2.3
  commit:     4bb0d8447f62fee77e2c3c29f54b5fcaf5e2c066
  local patch: fpocket-4.2.3-mdparams-argv-allocation.patch
               sha256 6ed7a0e8280f10ae0d42c42d771b4a3083e7891d007898bc19f7148bb433481d

Target and dependency boundary:
  * Linux x86_64 only: the pinned source ships LINUXAMD64 molfile objects.
  * Required before --execute: git, GNU make, GCC/G++, and the NetCDF C
    development package (Debian/Ubuntu: libnetcdf-dev; RHEL: netcdf-devel).
  * No sudo, package-manager action, CUDA installation, or shell startup-file
    edit is performed.  fpocket/MDpocket is CPU post-processing software and
    is independent of the CUDA-enabled GROMACS simulation installation.
  * The upstream makefile is built serially (-j1); its qhull/object rules are
    not reliably parallel-safe.
  * A checksum-pinned one-line patch fixes an upstream argv-copy heap overflow;
    the patched source hash and functional MDpocket smoke are verified.

Installed entry points:
  PREFIX/bin/{fpocket,tpocket,dpocket,mdpocket}
  PREFIX/env.sh
  PREFIX/share/fpocket/BUILDINFO.tsv
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
        --prefix)
            need_arg "$@"; prefix=$2; shift
            ;;
        --work-root)
            need_arg "$@"; work_root=$2; shift
            ;;
        --cc)
            need_arg "$@"; cc=$2; shift
            ;;
        --cxx)
            need_arg "$@"; cxx=$2; shift
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

if [[ -z $prefix || -z $work_root ]]; then
    [[ -n ${HOME:-} ]] || die "HOME is unset; provide both --prefix and --work-root"
    [[ -n $prefix ]] || prefix="$HOME/opt/fpocket-${FPOCKET_VERSION}"
    [[ -n $work_root ]] || work_root="$HOME/src/fpocket-${FPOCKET_VERSION}-build"
fi

command -v realpath >/dev/null 2>&1 || die "realpath is required"
absolute_path() {
    realpath -m -- "$1"
}

prefix="$(absolute_path "$prefix")"
work_root="$(absolute_path "$work_root")"

validate_target_path() {
    local label=$1 value=$2
    [[ $value == /* ]] || die "$label must resolve to an absolute path"
    [[ $value != / ]] || die "$label must not be /"
    [[ $value != *[$'\n\r\t ']* ]] || die "$label must not contain whitespace: $value"
}

validate_target_path "prefix" "$prefix"
validate_target_path "work root" "$work_root"
[[ $cc != *[$'\n\r\t ']* && $cxx != *[$'\n\r\t ']* ]] ||
    die "compiler executable names must not contain whitespace"

paths_overlap() {
    local left=${1%/} right=${2%/}
    [[ $left == "$right" || $left == "$right"/* || $right == "$left"/* ]]
}

paths_overlap "$work_root" "$prefix" &&
    die "work root and install prefix must be separate, non-nested trees"
if paths_overlap "$work_root" "$BUNDLE_ROOT" || paths_overlap "$prefix" "$BUNDLE_ROOT"; then
    die "work/install targets must not overlap the immutable agent bundle"
fi
case "$prefix" in
    /usr|/usr/local|/opt|/var|/etc) die "refusing broad/system prefix: $prefix" ;;
esac
user_home="${HOME:-}"
if [[ -z $user_home || $prefix != "$user_home"/* ]]; then
    warn "prefix is outside HOME; this script still never invokes sudo: $prefix"
fi

readonly SOURCE_DIR="$work_root/fpocket-${FPOCKET_VERSION}-src"
readonly INSTALL_CANDIDATE="${prefix}.installing"
readonly HELP_RECORD="$work_root/mdpocket-help.txt"
readonly FUNCTIONAL_SMOKE_ROOT="$work_root/mdpocket-functional-smoke"

paths_overlap "$work_root" "$INSTALL_CANDIDATE" &&
    die "work root must not overlap the staged install path: $INSTALL_CANDIDATE"

print_command() {
    printf '  '
    printf '%q ' "$@"
    printf '\n'
}

printf 'Discngine/fpocket installation plan\n'
printf '  mode:        %s\n' "$([[ $execute == 1 ]] && printf EXECUTE || printf PLAN)"
printf '  repository:  %s\n' "$FPOCKET_REPOSITORY"
printf '  tag:         %s\n' "$FPOCKET_TAG"
printf '  commit:      %s\n' "$FPOCKET_COMMIT"
printf '  patch:       %s\n' "$FPOCKET_PATCH_NAME"
printf '  patch SHA:   %s\n' "$FPOCKET_PATCH_SHA256"
printf '  prefix:      %s\n' "$prefix"
printf '  work root:   %s\n' "$work_root"
printf '  C compiler:  %s\n' "$cc"
printf '  C++ compiler: %s\n' "$cxx"
printf '  build mode:  serial (-j1)\n'
printf '  dependency:  NetCDF C headers/library supplied by the target OS\n'
printf '  network:     required only in EXECUTE mode to clone the pinned commit\n'
printf 'Planned source acquisition and build:\n'
print_command git clone --depth 1 --branch "$FPOCKET_TAG" "$FPOCKET_REPOSITORY" "$SOURCE_DIR"
print_command git -C "$SOURCE_DIR" rev-parse HEAD
print_command sha256sum "$FPOCKET_PATCH"
print_command patch --forward --batch -d "$SOURCE_DIR" -p1 -i "$FPOCKET_PATCH"
print_command make -C "$SOURCE_DIR" -j1 \
    CC="$cc" CXX="$cxx" CCQHULL="$cc" LINKER="$cc" LINKERQHULL="$cc" all
printf 'Planned installation and validation:\n'
print_command make -C "$SOURCE_DIR" BINDIR="$INSTALL_CANDIDATE/bin/" \
    LIBDIR="$INSTALL_CANDIDATE/lib/" MANDIR="$INSTALL_CANDIDATE/share/man/man8/" install
print_command "$INSTALL_CANDIDATE/bin/mdpocket" --help
print_command ldd "$INSTALL_CANDIDATE/bin/mdpocket"
printf '  functional smoke: bundled upstream 10-PDB discovery + selected-pocket characterization\n'

if ((execute == 0)); then
    printf 'PLAN complete: no directory was created, no network request was made, and nothing was installed.\n'
    exit 0
fi

[[ $(uname -s) == Linux ]] || die "this audited installer currently supports Linux only"
case "$(uname -m)" in
    x86_64|amd64) ;;
    *) die "fpocket ${FPOCKET_VERSION} ships LINUXAMD64 molfile objects; unsupported architecture: $(uname -m)" ;;
esac

for required_command in git make mkdir mv grep ldd date uname mktemp find sha256sum patch ln awk; do
    command -v "$required_command" >/dev/null 2>&1 || die "missing required command: $required_command"
done
make_bin="$(command -v make)"
make_version="$("$make_bin" --version)"
grep -q 'GNU Make' <<<"$make_version" || die "GNU make is required"

# Verify the local corrective input before creating any directory, probing a
# compiler, or contacting the network.  The same digest is also recorded in
# install/SHA256SUMS and the final BUILDINFO.
[[ -f $FPOCKET_PATCH ]] || die "missing pinned fpocket patch: $FPOCKET_PATCH"
actual_patch_sha256="$(sha256sum "$FPOCKET_PATCH")"
actual_patch_sha256="${actual_patch_sha256%% *}"
[[ $actual_patch_sha256 == "$FPOCKET_PATCH_SHA256" ]] ||
    die "fpocket patch SHA-256 mismatch: got $actual_patch_sha256, expected $FPOCKET_PATCH_SHA256"

resolve_executable() {
    local requested=$1
    if [[ $requested == */* ]]; then
        [[ -x $requested ]] || die "compiler is not executable: $requested"
        absolute_path "$requested"
    else
        command -v "$requested" 2>/dev/null || die "cannot find compiler: $requested"
    fi
}

cc="$(resolve_executable "$cc")"
cxx="$(resolve_executable "$cxx")"
"$cc" --version >/dev/null 2>&1 || die "C compiler cannot run: $cc"
"$cxx" --version >/dev/null 2>&1 || die "C++ compiler cannot run: $cxx"

[[ ! -e $work_root ]] || die "work root already exists; refusing to reuse or overwrite it: $work_root"
[[ ! -e $prefix ]] || die "install prefix already exists; refusing to overwrite it: $prefix"
[[ ! -e $INSTALL_CANDIDATE ]] ||
    die "staged install already exists; inspect/remove it manually before retrying: $INSTALL_CANDIDATE"

printf '==> Validating the official NetCDF development dependency\n'
netcdf_probe="$(mktemp /tmp/fpocket-netcdf-probe.XXXXXX)"
cleanup_netcdf_probe() {
    if [[ -n ${netcdf_probe:-} && -e $netcdf_probe ]]; then
        find "$netcdf_probe" -maxdepth 0 -delete
    fi
}
trap cleanup_netcdf_probe EXIT
if ! printf '%s\n' '#include <netcdf.h>' \
        'int main(void) { return nc_inq_libvers() ? 0 : 1; }' \
        | "$cc" -x c - -lnetcdf -o "$netcdf_probe"; then
    die "cannot compile/link NetCDF C API; install libnetcdf-dev (Debian/Ubuntu) or netcdf-devel (RHEL)"
fi
"$netcdf_probe" || die "the linked NetCDF C library failed its runtime probe"
cleanup_netcdf_probe
netcdf_probe=""
trap - EXIT

mkdir -p -- "$work_root" "$(dirname -- "$prefix")"

printf '==> Cloning the pinned official source\n'
git clone --depth 1 --branch "$FPOCKET_TAG" "$FPOCKET_REPOSITORY" "$SOURCE_DIR"
actual_commit="$(git -C "$SOURCE_DIR" rev-parse HEAD)"
[[ $actual_commit == "$FPOCKET_COMMIT" ]] ||
    die "tag $FPOCKET_TAG resolved to unexpected commit $actual_commit (expected $FPOCKET_COMMIT)"
[[ -z $(git -C "$SOURCE_DIR" status --porcelain --untracked-files=no) ]] ||
    die "fresh fpocket checkout is unexpectedly dirty"

printf '==> Applying the checksum-pinned argv allocation fix\n'
patch --forward --batch -d "$SOURCE_DIR" -p1 -i "$FPOCKET_PATCH"
patched_mdparams_sha256="$(sha256sum "$SOURCE_DIR/src/mdparams.c")"
patched_mdparams_sha256="${patched_mdparams_sha256%% *}"
[[ $patched_mdparams_sha256 == "$PATCHED_MDPARAMS_SHA256" ]] ||
    die "patched src/mdparams.c has unexpected SHA-256: $patched_mdparams_sha256"
[[ $(git -C "$SOURCE_DIR" status --porcelain --untracked-files=no) == " M src/mdparams.c" ]] ||
    die "pinned patch changed an unexpected tracked-file set"
git -C "$SOURCE_DIR" diff --check

printf '==> Building fpocket/MDpocket serially\n'
# Command-line assignments override the upstream makefile's hard-coded
# compiler selection while retaining its LINUXAMD64 molfile/qhull layout.
"$make_bin" -C "$SOURCE_DIR" -j1 \
    CC="$cc" CXX="$cxx" CCQHULL="$cc" \
    LINKER="$cc" LINKERQHULL="$cc" all

for executable in fpocket tpocket dpocket mdpocket; do
    [[ -x "$SOURCE_DIR/bin/$executable" ]] || die "build did not produce bin/$executable"
done
[[ $(git -C "$SOURCE_DIR" status --porcelain --untracked-files=no) == " M src/mdparams.c" ]] ||
    die "build modified tracked files beyond the pinned mdparams patch"
post_build_mdparams_sha256="$(sha256sum "$SOURCE_DIR/src/mdparams.c")"
post_build_mdparams_sha256="${post_build_mdparams_sha256%% *}"
[[ $post_build_mdparams_sha256 == "$PATCHED_MDPARAMS_SHA256" ]] ||
    die "build changed the checksum-pinned patched mdparams source"

printf '==> Staging the upstream install into a user-owned prefix\n'
mkdir -p -- "$INSTALL_CANDIDATE/lib"
"$make_bin" -C "$SOURCE_DIR" \
    BINDIR="$INSTALL_CANDIDATE/bin/" \
    LIBDIR="$INSTALL_CANDIDATE/lib/" \
    MANDIR="$INSTALL_CANDIDATE/share/man/man8/" install

mkdir -p -- "$INSTALL_CANDIDATE/share/fpocket"
build_timestamp="$(date --iso-8601=seconds)"
compiler_report="$("$cc" --version)"
compiler_summary="${compiler_report%%$'\n'*}"
{
    printf 'field\tvalue\n'
    printf 'repository\t%s\n' "$FPOCKET_REPOSITORY"
    printf 'tag\t%s\n' "$FPOCKET_TAG"
    printf 'commit\t%s\n' "$FPOCKET_COMMIT"
    printf 'patch_name\t%s\n' "$FPOCKET_PATCH_NAME"
    printf 'patch_sha256\t%s\n' "$FPOCKET_PATCH_SHA256"
    printf 'patch_description\t%s\n' "$FPOCKET_PATCH_DESCRIPTION"
    printf 'patched_mdparams_sha256\t%s\n' "$PATCHED_MDPARAMS_SHA256"
    printf 'built_at\t%s\n' "$build_timestamp"
    printf 'platform\t%s\n' "$(uname -srvmo)"
    printf 'c_compiler\t%s\n' "$compiler_summary"
    printf 'build_mode\tGNU make -j1 all\n'
    printf 'netcdf_probe\tcompiled, linked, and executed\n'
} >"$INSTALL_CANDIDATE/share/fpocket/BUILDINFO.tsv"

provenance="Discngine/fpocket tag ${FPOCKET_TAG} commit ${FPOCKET_COMMIT} bundle-patch-sha256 ${FPOCKET_PATCH_SHA256}"
{
    printf '# Source this file before preparing an Agent run, or copy the two\n'
    printf '# MDPOCKET_* exports into the deployment site.env.\n'
    printf 'export FPOCKET_PREFIX=%q\n' "$prefix"
    printf 'export PATH="$FPOCKET_PREFIX/bin${PATH:+:$PATH}"\n'
    printf 'export MDPOCKET_BIN="$FPOCKET_PREFIX/bin/mdpocket"\n'
    printf 'export MDPOCKET_PROVENANCE=%q\n' "$provenance"
} >"$INSTALL_CANDIDATE/env.sh"

printf '==> Validating the installed MDpocket interface\n'
for executable in fpocket tpocket dpocket mdpocket; do
    [[ -x "$INSTALL_CANDIDATE/bin/$executable" ]] ||
        die "staged install is missing executable: $executable"
done
mdpocket_sha256="$(sha256sum "$INSTALL_CANDIDATE/bin/mdpocket")"
mdpocket_sha256="${mdpocket_sha256%% *}"
printf 'mdpocket_sha256\t%s\n' "$mdpocket_sha256" \
    >>"$INSTALL_CANDIDATE/share/fpocket/BUILDINFO.tsv"
"$INSTALL_CANDIDATE/bin/mdpocket" --help >"$HELP_RECORD" 2>&1 ||
    die "installed mdpocket --help failed"
for required_interface in --pdb_list --selected_pocket --trajectory_file --trajectory_format xtc; do
    grep -q -- "$required_interface" "$HELP_RECORD" ||
        die "installed MDpocket help lacks required interface token: $required_interface"
done
if ! ldd_report="$(ldd "$INSTALL_CANDIDATE/bin/mdpocket" 2>&1)"; then
    printf '%s\n' "$ldd_report" >&2
    die "ldd failed for the installed mdpocket"
fi
if grep -q 'not found' <<<"$ldd_report"; then
    printf '%s\n' "$ldd_report" >&2
    die "installed mdpocket has unresolved shared libraries"
fi

printf '==> Running the upstream 10-PDB MDpocket functional smoke\n'
sample_root="$SOURCE_DIR/data/sample/mdpocket"
for required_sample in \
    input.txt mdpout_dens_iso_8.pdb \
    2yex.pdb 3ot3.pdb 3pa3.pdb 3pa4.pdb 3tki.pdb \
    4hyi.pdb 4rvk.pdb 5opb.pdb 5opu.pdb 5oq5.pdb; do
    [[ -s "$sample_root/$required_sample" ]] ||
        die "pinned upstream functional-smoke input is missing: $required_sample"
done
mkdir -p -- "$FUNCTIONAL_SMOKE_ROOT/discovery" "$FUNCTIONAL_SMOKE_ROOT/selected"
for sample in \
    input.txt 2yex.pdb 3ot3.pdb 3pa3.pdb 3pa4.pdb 3tki.pdb \
    4hyi.pdb 4rvk.pdb 5opb.pdb 5opu.pdb 5oq5.pdb; do
    ln -s -- "$sample_root/$sample" "$FUNCTIONAL_SMOKE_ROOT/discovery/$sample"
    ln -s -- "$sample_root/$sample" "$FUNCTIONAL_SMOKE_ROOT/selected/$sample"
done
ln -s -- "$sample_root/mdpout_dens_iso_8.pdb" \
    "$FUNCTIONAL_SMOKE_ROOT/selected/mdpout_dens_iso_8.pdb"
(
    cd -- "$FUNCTIONAL_SMOKE_ROOT/discovery"
    "$INSTALL_CANDIDATE/bin/mdpocket" --pdb_list input.txt \
        >mdpocket.stdout 2>mdpocket.stderr
)
[[ -s "$FUNCTIONAL_SMOKE_ROOT/discovery/mdpout_dens_grid.dx" ]] ||
    die "MDpocket discovery smoke did not produce a nonempty density grid"
grep -q '^object 1 class gridpositions counts ' \
    "$FUNCTIONAL_SMOKE_ROOT/discovery/mdpout_dens_grid.dx" ||
    die "MDpocket discovery smoke produced an invalid density-grid header"
(
    cd -- "$FUNCTIONAL_SMOKE_ROOT/selected"
    "$INSTALL_CANDIDATE/bin/mdpocket" --pdb_list input.txt \
        --selected_pocket mdpout_dens_iso_8.pdb \
        >mdpocket.stdout 2>mdpocket.stderr
)
descriptor_file="$FUNCTIONAL_SMOKE_ROOT/selected/mdpout_descriptors.txt"
[[ -s $descriptor_file ]] ||
    die "MDpocket selected-pocket smoke did not produce nonempty descriptors"
IFS= read -r descriptor_header <"$descriptor_file"
[[ $descriptor_header == "$MDPOCKET_DESCRIPTOR_HEADER" ]] ||
    die "MDpocket functional smoke descriptor header is not the required 42-column schema"
awk '
    NR == 1 { if (NF != 42) exit 1; next }
    {
        if (NF != 42 || $1 != NR - 1) exit 1
        for (field = 1; field <= NF; field++) {
            if ($field !~ /^[-+]?[0-9]+([.][0-9]+)?([eE][-+]?[0-9]+)?$/) exit 1
        }
    }
    END { if (NR != 11) exit 1 }
' "$descriptor_file" ||
    die "MDpocket functional smoke requires 10 contiguous, finite, 42-column rows"
printf 'functional_smoke\t10-PDB discovery DX and selected-pocket 42-column descriptors passed\n' \
    >>"$INSTALL_CANDIDATE/share/fpocket/BUILDINFO.tsv"

printf '==> Publishing the validated installation\n'
[[ ! -e $prefix ]] || die "install prefix appeared during build; refusing unsafe publication: $prefix"
mv -T -- "$INSTALL_CANDIDATE" "$prefix"
[[ -x "$prefix/bin/mdpocket" ]] || die "published prefix is missing mdpocket"
published_sha256="$(sha256sum "$prefix/bin/mdpocket")"
published_sha256="${published_sha256%% *}"
[[ $published_sha256 == "$mdpocket_sha256" ]] || die "published mdpocket differs from validated candidate"

printf 'fpocket/MDpocket installation complete.\n'
printf '  Prefix:      %s\n' "$prefix"
printf '  MDpocket:    %s/bin/mdpocket\n' "$prefix"
printf '  Provenance:  %s\n' "$provenance"
printf '  Build info:  %s/share/fpocket/BUILDINFO.tsv\n' "$prefix"
printf '  Environment: source %s/env.sh\n' "$prefix"
printf 'The upstream 10-PDB functional smoke passed; the Agent MDpocket stage still\n'
printf 'validates the real 501-frame output and required descriptor schema.\n'
