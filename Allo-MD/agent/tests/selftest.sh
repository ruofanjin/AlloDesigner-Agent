#!/usr/bin/env bash
set -Eeuo pipefail

bundle_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
failures=0

ok() { printf 'OK: %s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; failures=$((failures + 1)); }

if (( BASH_VERSINFO[0] > 4 || (BASH_VERSINFO[0] == 4 && BASH_VERSINFO[1] >= 3) )); then
    ok "Bash supports the required 4.3+ nameref interface"
else
    fail "Bash 4.3 or newer is required"
fi

for command_name in bash python3 sha256sum find; do
    command -v "$command_name" >/dev/null 2>&1 || fail "missing self-test command: $command_name"
done
(( failures == 0 )) || exit 1

if ! find "$bundle_root" -type f \( -name '*.pyc' -o -name '*.pyo' \) -print -quit | grep -q . \
   && ! find "$bundle_root" -type d -name '__pycache__' -print -quit | grep -q .; then
    ok "bundle contains no generated Python bytecode/cache"
else
    fail "bundle contains generated __pycache__/pyc artifacts"
fi

permissions_ok=1
[[ $(stat -c '%a' "$bundle_root/manifests/MANIFEST.sha256") == 644 ]] || permissions_ok=0
for executable in "$bundle_root/agentctl" "$bundle_root/tests/selftest.sh" "$bundle_root"/stages/*.sh; do
    [[ -x "$executable" ]] || permissions_ok=0
done
for directory in "$bundle_root/reference/original_scripts" \
    "$bundle_root/reference/original_scripts/mdpocket" \
    "$bundle_root/reference/original_scripts/deal_md" \
    "$bundle_root/reference/original_scripts/project_root"; do
    [[ -x "$directory" ]] || permissions_ok=0
done
if (( permissions_ok == 1 )); then
    ok "deployment entry points and reference directories have usable modes"
else
    fail "deployment file/directory modes are invalid"
fi

if [[ -s "$bundle_root/manifests/MANIFEST.sha256" ]]; then
    if python3 - "$bundle_root" <<'PY'
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]).resolve()
manifest = root / "manifests/MANIFEST.sha256"
declared = []
for line_number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
    match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
    assert match, f"invalid manifest line {line_number}"
    relative = Path(match.group(2))
    assert not relative.is_absolute() and ".." not in relative.parts
    rendered = relative.as_posix()
    normalized = rendered[2:] if rendered.startswith("./") else rendered
    declared.append(normalized)
assert len(declared) == len(set(declared)), "duplicate path in bundle manifest"
expected = {
    path.relative_to(root).as_posix()
    for path in root.rglob("*")
    if path.is_file() and path != manifest
}
assert set(declared) == expected, (
    f"bundle manifest path set differs: missing={sorted(expected - set(declared))}, "
    f"extra={sorted(set(declared) - expected)}"
)
PY
    then
        ok "deployment manifest covers every regular bundle file exactly once"
    else
        fail "deployment manifest path coverage validation failed"
    fi
    if (
        cd "$bundle_root"
        sha256sum --check --quiet manifests/MANIFEST.sha256
    ); then
        ok "complete deployment bundle matches its recorded SHA-256 manifest"
    else
        fail "deployment bundle checksum verification failed"
    fi
else
    fail "missing manifests/MANIFEST.sha256"
fi

if (
    cd "$bundle_root/install"
    sha256sum --check SHA256SUMS
); then
    ok "bundled source archives match their recorded SHA-256"
else
    fail "source archive checksum verification failed"
fi

if [[ -s "$bundle_root/manifests/input_checksums.sha256" ]]; then
    if (
        cd "$bundle_root"
        sha256sum --check manifests/input_checksums.sha256
    ); then
        ok "frozen scientific inputs match their recorded SHA-256"
    else
        fail "scientific input checksum verification failed"
    fi
else
    fail "missing manifests/input_checksums.sha256"
fi

if python3 "$bundle_root/tools/validate_inputs.py" --bundle-root "$bundle_root"; then
    ok "scientific structure, groups, MDPs, and PLUMED inputs are internally valid"
else
    fail "scientific input validation failed"
fi

syntax_failed=0
while IFS= read -r -d '' shell_file; do
    bash -n "$shell_file" || syntax_failed=1
done < <(find "$bundle_root/stages" "$bundle_root/install" "$bundle_root/scheduler" "$bundle_root/tests" \
    -type f -name '*.sh' -print0)
if (( syntax_failed == 0 )); then
    ok "all runnable shell files pass bash -n"
else
    fail "shell syntax validation failed"
fi

if python3 - "$bundle_root" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
paths = [root / "agentctl", *sorted((root / "tools").glob("*.py"))]
for path in paths:
    source = path.read_text(encoding="utf-8")
    compile(source, str(path), "exec")
print(f"compiled {len(paths)} Python entry points without writing bytecode")
PY
then
    ok "all Python entry points compile"
else
    fail "Python syntax validation failed"
fi

if python3 - "$bundle_root" <<'PY'
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
mdp = (root / "tests/fixtures/smoke.mdp").read_text(encoding="utf-8")
plumed = (root / "tests/fixtures/plumed_sasa_smoke.dat").read_text(encoding="utf-8")
plumed_actions = "\n".join(line.split("#", 1)[0] for line in plumed.splitlines())

def value(name: str) -> str:
    match = re.search(rf"(?mi)^\s*{re.escape(name)}\s*=\s*([^;#\s]+)", mdp)
    assert match, f"missing smoke MDP key: {name}"
    return match.group(1).lower()

assert value("integrator") == "md"
assert value("nsteps") == "0"
assert value("tcoupl") == "no"
assert value("pcoupl") == "no"
assert value("constraints") == "none"
assert re.search(r"(?m)^\s*(?:\w+:\s*)?SASA_HASEL\b", plumed_actions)
assert not re.search(r"(?m)^\s*(?:\w+:\s*)?METAD\b", plumed_actions)
assert not re.search(r"(?m)^\s*(?:\w+:\s*)?BIASVALUE\b", plumed_actions)
assert "FILE=COLVAR_smoke" in plumed_actions
print("validated zero-step smoke fixture semantics")
PY
then
    ok "zero-step smoke fixture cannot advance dynamics or apply a production bias"
else
    fail "zero-step smoke fixture semantic validation failed"
fi

descriptor_tmp="$(mktemp -d "${TMPDIR:-/tmp}/glp1-descriptor-qc.XXXXXX")"
if python3 - "$bundle_root" "$descriptor_tmp" <<'PY'
from pathlib import Path
import json
import subprocess
import sys

root = Path(sys.argv[1])
tmp = Path(sys.argv[2])
header = (
    "snapshot pock_volume pock_asa pock_pol_asa pock_apol_asa pock_asa22 "
    "pock_pol_asa22 pock_apol_asa22 nb_AS mean_as_ray mean_as_solv_acc "
    "apol_as_prop mean_loc_hyd_dens hydrophobicity_score volume_score "
    "polarity_score charge_score prop_polar_atm as_density as_max_dst "
    "convex_hull_volume nb_abpa ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE "
    "LEU LYS MET PHE PRO SER THR TRP TYR VAL"
).split()
rows = []
for snapshot, volume in ((1, 0.0), (2, 12.5)):
    fields = ["0"] * len(header)
    fields[header.index("snapshot")] = str(snapshot)
    fields[header.index("pock_volume")] = str(volume)
    rows.append(fields)
rows[0][header.index("as_density")] = "nan"
good = tmp / "good.txt"
good.write_text(" ".join(header) + "\n" + "\n".join(" ".join(row) for row in rows) + "\n")
command = [
    sys.executable, str(root / "tools/plot_pocket_volume.py"),
    "--input", str(good), "--csv-output", str(tmp / "volume.csv"),
    "--qc-output", str(tmp / "qc.json"), "--frame-interval-ps", "100",
    "--expected-count", "2", "--require-historical-schema",
]
subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
qc = json.loads((tmp / "qc.json").read_text())
assert qc["row_count"] == 2
assert qc["frame"]["last_time_ps"] == 100
assert qc["nonfinite"]["by_column"] == {"as_density": 1}
bad_rows = [row[:] for row in rows]
bad_rows[1][header.index("pock_volume")] = "nan"
bad = tmp / "bad.txt"
bad.write_text(" ".join(header) + "\n" + "\n".join(" ".join(row) for row in bad_rows) + "\n")
bad_command = command[:]
bad_command[bad_command.index(str(good))] = str(bad)
assert subprocess.run(bad_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0
PY
then
    ok "MDpocket QC reports auxiliary NaN but rejects non-finite pocket volume"
else
    fail "MDpocket descriptor/QC functional test failed"
fi
find "$descriptor_tmp" -depth -delete

restart_validator=(
    python3 "$bundle_root/tools/validate_plumed_restart.py"
    --plumed "$bundle_root/tests/fixtures/plumed_restart.dat"
    --base-dir "$bundle_root/tests/fixtures/restart_series"
    --dt 0.2
)
if "${restart_validator[@]}" --checkpoint-time 2 >/dev/null \
    && ! "${restart_validator[@]}" --checkpoint-time 1 >/dev/null 2>&1 \
    && ! "${restart_validator[@]}" --checkpoint-time 3 >/dev/null 2>&1; then
    ok "PLUMED restart validator accepts aligned series and rejects ahead/missing rows"
else
    fail "PLUMED restart validator functional tests failed"
fi

em_guard_tmp="$(mktemp -d "${TMPDIR:-/tmp}/glp1-em-guard.XXXXXX")"
{
    printf '%s\n' '#!/usr/bin/env bash' 'set -Eeuo pipefail'
    printf '%s\n' '[[ ${1:-} == dump ]] || exit 9'
    printf '%s\n' 'output=' 'input=' 'while (($#)); do'
    printf '%s\n' '  if [[ $1 == -om ]]; then output=$2; shift 2; continue; fi'
    printf '%s\n' '  if [[ $1 == -s ]]; then input=$2; shift 2; continue; fi' '  shift' 'done'
    printf '%s\n' '[[ -n $output && -n $input ]] || exit 9'
    printf '%s\n' 'if [[ ${input##*/} == md.tpr ]]; then'
    printf '%s\n' "  printf 'integrator = md\\n' > \"\$output\""
    printf '%s\n' 'else'
    printf '%s\n' "  printf 'integrator = steep\\nemtol = 1000\\nnsteps = 5000\\n' > \"\$output\""
    printf '%s\n' 'fi'
} >"$em_guard_tmp/mock-gmx"
chmod 700 "$em_guard_tmp/mock-gmx"
printf '%s\n' 'mock TPR' >"$em_guard_tmp/em.tpr"
printf '%s\n' 'mock TPR' >"$em_guard_tmp/md.tpr"
printf '%s\n' 'Steepest Descents converged to Fmax < 1000 in 2723 steps' >"$em_guard_tmp/em.log"
if (
    export AGENT_BUNDLE_ROOT="$bundle_root"
    export GMX_BIN="$em_guard_tmp/mock-gmx"
    export GMX_MDRUN_MAXH=1
    export AGENT_COMMAND_FILE=/dev/null AGENT_CONSOLE_LOG=/dev/null
    # shellcheck source=../stages/lib/common.sh
    source "$bundle_root/stages/lib/common.sh"
    assert_checkpoint_reached_tpr_end "$em_guard_tmp/em" >/dev/null || exit 1
    command=("$GMX_BIN" mdrun)
    append_mdrun_tuning command "$em_guard_tmp/em" >/dev/null || exit 1
    [[ " ${command[*]} " != *" -maxh "* ]] || exit 1
    md_command=("$GMX_BIN" mdrun)
    append_mdrun_tuning md_command "$em_guard_tmp/md" >/dev/null || exit 1
    [[ " ${md_command[*]} " == *" -maxh 1 "* ]] || exit 1
    printf '%s\n' 'Finished mdrun' >"$em_guard_tmp/em.log"
    if assert_checkpoint_reached_tpr_end "$em_guard_tmp/em" >/dev/null 2>&1; then
        exit 1
    fi
); then
    ok "minimization guard requires Fmax convergence and limits -maxh to MD"
else
    fail "minimization completion/maxh guard functional test failed"
fi
find "$em_guard_tmp" -depth -delete

if python3 - "$bundle_root" <<'PY'
from pathlib import Path
import json
import sys

root = Path(sys.argv[1])
data = json.loads((root / "manifests/stages.json").read_text(encoding="utf-8"))
input_policy = json.loads((root / "manifests/input_policy.json").read_text(encoding="utf-8"))
membrane_contract = json.loads((root / "manifests/membrane_build_contract.json").read_text(encoding="utf-8"))
assert input_policy["current_mode"] == "frozen_current_reproduction_snapshot"
assert input_policy["immutable"] is True
assert input_policy["future_full_flow_planner"]["implemented"] is False
assert membrane_contract["implemented"] is False
assert membrane_contract["default_route"] == "charmm_gui_membrane_builder"
assert "packaged_254_atom_sasa_mapping" in membrane_contract["forbidden_reuse"]
ids = [item["id"] for item in data["stages"]]
assert len(ids) == len(set(ids)), "duplicate stage id"
known = set(ids)
for item in data["stages"]:
    script = root / item["script"]
    assert script.is_file(), f"missing stage script: {script}"
    assert script.stat().st_mode & 0o111, f"stage script is not executable: {script}"
    assert all(dep in known for dep in item.get("deps", [])), f"unknown dependency in {item['id']}"
    assert all(not Path(rel).is_absolute() and ".." not in Path(rel).parts for rel in item.get("expected", []))
    for specification in item.get("indexed_files", []):
        directory = Path(specification["directory"])
        assert not directory.is_absolute() and ".." not in directory.parts
        assert isinstance(specification["count"], int) and specification["count"] > 0
        assert specification["prefix"] and specification["suffix"]
simulation_ids = {
    "equilibration", "normal_10ns", "normal_50ns", "normal_100ns",
    "normal_200ns_from_100ns", "distance_monitor_50ns", "distance_metad_50ns",
    "distance_metad_100ns_new_bias", "sasa_site_10ns", "sasa_pocket_10ns",
    "sasa_pocket_100ns",
}
assert all(
    next(item for item in data["stages"] if item["id"] == stage)["requires_device"] == "gpu"
    for stage in simulation_ids
), "every packaged production simulation must require CUDA"
minimization = next(item for item in data["stages"] if item["id"] == "minimization")
assert "requires_device" not in minimization, "steep minimization must not force MD-only GPU flags"
analysis_ids = {
    "postprocess_distance_50ns", "mdpocket_distance_50ns",
    "postprocess_sasa_site_10ns", "mdpocket_sasa_site_10ns",
    "postprocess_sasa_pocket_10ns", "mdpocket_sasa_pocket_10ns",
    "postprocess_sasa_pocket_100ns", "mdpocket_sasa_pocket_100ns",
}
assert all(
    next(item for item in data["stages"] if item["id"] == stage)["protocol_class"]
    == "standardized-analysis" for stage in analysis_ids
)
assert all(
    "requires_device" not in next(item for item in data["stages"] if item["id"] == stage)
    for stage in analysis_ids
), "analysis stages must not require a live GPU"
assert data["profiles"]["historical-sasa-biased-main"][-2:] == [
    "sasa_site_10ns", "sasa_pocket_100ns"
], "SASA main must retain two parallel scientific branches"
assert data["profiles"]["standardized-sasa-biased-main"][-4:] == [
    "postprocess_sasa_site_10ns", "mdpocket_sasa_site_10ns",
    "postprocess_sasa_pocket_100ns", "mdpocket_sasa_pocket_100ns",
], "standardized SASA main must include both complete analysis branches"
for profile, selected in data["profiles"].items():
    assert all(stage in known for stage in selected), f"unknown stage in profile {profile}"
print(f"validated {len(ids)} stages and {len(data['profiles'])} profiles")
PY
then
    ok "DAG references are safe and complete"
else
    fail "DAG validation failed"
fi

snapshot_qc_tmp="$(mktemp -d "${TMPDIR:-/tmp}/glp1-snapshot-qc.XXXXXX")"
mkdir -p "$snapshot_qc_tmp/good" "$snapshot_qc_tmp/bad"
{
    printf 'TITLE     frame t=   0.00000 step= 0\n'
    printf 'ATOM  %5d  C   TST A   1    %8.3f%8.3f%8.3f\n' 1 1 2 3
    printf 'ATOM  %5d  O   TST A   1    %8.3f%8.3f%8.3f\n' 2 2 3 4
    printf 'ENDMDL\n'
} >"$snapshot_qc_tmp/good/frame0.pdb"
printf 'ATOM' >"$snapshot_qc_tmp/bad/frame0.pdb"
if python3 "$bundle_root/tools/make_snapshot_list.py" \
        --frames-dir "$snapshot_qc_tmp/good" --output "$snapshot_qc_tmp/good/list.txt" \
        --expected-count 1 --expected-atoms 2 --frame-interval-ps 100 >/dev/null \
   && ! python3 "$bundle_root/tools/make_snapshot_list.py" \
        --frames-dir "$snapshot_qc_tmp/bad" --output "$snapshot_qc_tmp/bad/list.txt" \
        --expected-count 1 --expected-atoms 2 --frame-interval-ps 100 >/dev/null 2>&1; then
    ok "snapshot QC accepts complete PDB frames and rejects truncated nonempty files"
else
    fail "snapshot PDB integrity validation failed"
fi
find "$snapshot_qc_tmp" -depth -delete

if [[ -x "$bundle_root/agentctl" && -x "$bundle_root/tests/selftest.sh" ]] \
    && "$bundle_root/agentctl" list >/dev/null \
    && "$bundle_root/agentctl" plan --profile historical-distance-main | grep -q 'device=gpu' \
    && "$bundle_root/agentctl" plan --profile historical-sasa-biased-main | grep -q 'sasa_pocket_100ns' \
    && "$bundle_root/agentctl" plan --profile standardized-sasa-biased-main \
        | grep -q 'class=standardized-analysis'; then
    ok "agentctl expands distance/SASA profiles and exposes device/protocol classes"
else
    fail "agentctl plan/list failed"
fi

dry_root="${TMPDIR:-/tmp}/glp1-agent-dryrun-${PPID}-$$"
if [[ -e "$dry_root" ]]; then
    fail "unexpected dry-run test path already exists: $dry_root"
elif "$bundle_root/agentctl" --work-root "$dry_root" run \
        --profile historical-distance-main --run-id selftest >/dev/null \
    && [[ ! -e "$dry_root" ]]; then
    ok "default run is side-effect-free dry-run"
else
    fail "dry-run failed or created a work directory"
fi

smoke_dry_root="${TMPDIR:-/tmp}/gmx-plumed-smoke-dryrun-${PPID}-$$"
if [[ -e "$smoke_dry_root" ]]; then
    fail "unexpected smoke dry-run path already exists: $smoke_dry_root"
elif env -u PLUMED_KERNEL -u GMX_MAXCONSTRWARN \
        "$bundle_root/tests/smoke_gmx_plumed.sh" --mode cpu \
        --work-dir "$smoke_dry_root" >/dev/null \
    && [[ ! -e "$smoke_dry_root" ]]; then
    ok "zero-step integration smoke is side-effect-free by default"
else
    fail "smoke dry-run failed or created its work directory"
fi

fpocket_dry_root="${TMPDIR:-/tmp}/fpocket-installer-dryrun-${PPID}-$$"
if [[ -e "$fpocket_dry_root" ]]; then
    fail "unexpected fpocket dry-run path already exists: $fpocket_dry_root"
elif env -u HOME "$bundle_root/install/install_fpocket.sh" \
        --prefix "$fpocket_dry_root/prefix" \
        --work-root "$fpocket_dry_root/work" >/dev/null \
    && [[ ! -e "$fpocket_dry_root" ]]; then
    ok "pinned fpocket installer is side-effect-free by default"
else
    fail "fpocket installer plan failed or created a directory"
fi

mdpocket_bind_root="$(mktemp -d "${TMPDIR:-/tmp}/fpocket-bind.XXXXXX")"
if (
    mkdir -p "$mdpocket_bind_root/fpocket/bin" "$mdpocket_bind_root/fpocket/share/fpocket" || exit 1
    printf '%s\n' '#!/usr/bin/env bash' \
        'echo --pdb_list --selected_pocket --trajectory_file --trajectory_format xtc' \
        >"$mdpocket_bind_root/fpocket/bin/mdpocket" || exit 1
    chmod 755 "$mdpocket_bind_root/fpocket/bin/mdpocket" || exit 1
    binary_hash="$(sha256sum "$mdpocket_bind_root/fpocket/bin/mdpocket")" || exit 1
    binary_hash="${binary_hash%% *}"
    printf 'field\tvalue\nrepository\thttps://github.com/Discngine/fpocket.git\ntag\t4.2.3\ncommit\t4bb0d8447f62fee77e2c3c29f54b5fcaf5e2c066\npatch_name\tfpocket-4.2.3-mdparams-argv-allocation.patch\npatch_sha256\t6ed7a0e8280f10ae0d42c42d771b4a3083e7891d007898bc19f7148bb433481d\npatched_mdparams_sha256\te2bff1096c833083567fd626319161f2b6e06e7d7878dc9c073c77ba4ea1d8c8\nfunctional_smoke\t10-PDB discovery DX and selected-pocket 42-column descriptors passed\nmdpocket_sha256\t%s\n' \
        "$binary_hash" >"$mdpocket_bind_root/fpocket/share/fpocket/BUILDINFO.tsv" || exit 1
    printf 'GMX_DEVICE_MODE=gpu\nMDPOCKET_BIN=%q\nMDPOCKET_PROVENANCE=%q\n' \
        "$mdpocket_bind_root/fpocket/bin/mdpocket" \
        'Discngine/fpocket tag 4.2.3 commit 4bb0d8447f62fee77e2c3c29f54b5fcaf5e2c066 bundle-patch-sha256 6ed7a0e8280f10ae0d42c42d771b4a3083e7891d007898bc19f7148bb433481d' \
        >"$mdpocket_bind_root/site.env" || exit 1
    "$bundle_root/agentctl" --site-config "$mdpocket_bind_root/site.env" \
        --work-root "$mdpocket_bind_root/runs" prepare --run-id binding >/dev/null || exit 1
    python3 - "$mdpocket_bind_root/runs/binding/.agent/run.json" "$binary_hash" <<'PY' || exit 1
import json
import sys
metadata = json.load(open(sys.argv[1], encoding="utf-8"))
assert metadata["mdpocket_binary_sha256"] == sys.argv[2]
assert metadata["mdpocket_buildinfo_sha256"]
PY
    printf '# drift\n' >>"$mdpocket_bind_root/fpocket/bin/mdpocket" || exit 1
    if "$bundle_root/agentctl" --site-config "$mdpocket_bind_root/site.env" \
        --work-root "$mdpocket_bind_root/runs" run --profile historical-distance-main \
        --run-id binding --execute --allow-long-md \
        >"$mdpocket_bind_root/rejection.log" 2>&1; then
        exit 1
    fi
    grep -q 'binary.*changed' "$mdpocket_bind_root/rejection.log" || exit 1
); then
    ok "prepare freezes the pinned MDpocket binary/BUILDINFO and rejects drift"
else
    fail "MDpocket binary provenance binding test failed"
fi
find "$mdpocket_bind_root" -depth -delete

if PLUMED_KERNEL=/wrong/kernel \
        "$bundle_root/tests/smoke_gmx_plumed.sh" --mode cpu >/dev/null 2>&1; then
    fail "integration smoke accepted an ambient PLUMED_KERNEL override"
else
    ok "integration smoke rejects an ambient PLUMED_KERNEL override"
fi

if GMX_MAXCONSTRWARN=-1 env -u PLUMED_KERNEL \
        "$bundle_root/tests/smoke_gmx_plumed.sh" --mode cpu >/dev/null 2>&1; then
    fail "integration smoke accepted GMX_MAXCONSTRWARN=-1"
else
    ok "integration smoke rejects GMX_MAXCONSTRWARN=-1"
fi

stage_guard_root="${TMPDIR:-/tmp}/glp1-stage-guard-${PPID}-$$"
stage_guard_env=(
    env -u PLUMED_KERNEL -u GMX_MAXCONSTRWARN
    AGENT_BUNDLE_ROOT="$bundle_root"
    AGENT_RUN_DIR="$stage_guard_root/run"
    AGENT_STAGE_ID=equilibration
    AGENT_EXECUTE=1
    AGENT_ALLOW_LONG_MD=1
)
if "${stage_guard_env[@]}" "$bundle_root/stages/20_equilibration.sh" >/dev/null 2>&1; then
    fail "stage entry accepted a direct non-orchestrated invocation"
elif "${stage_guard_env[@]}" AGENT_ORCHESTRATED=1 AGENT_REQUIRED_DEVICE=gpu \
        GMX_DEVICE_MODE=cpu "$bundle_root/stages/20_equilibration.sh" >/dev/null 2>&1; then
    fail "CUDA production stage accepted CPU device mode"
elif [[ ! -e "$stage_guard_root" ]]; then
    ok "stage boundary rejects direct calls and CUDA-to-CPU downgrade before writes"
else
    fail "stage boundary negative tests created output"
fi

runnable_paths=(
    "$bundle_root/agentctl"
    "$bundle_root/stages"
    "$bundle_root/tools"
    "$bundle_root/install/install_gmx_stack.sh"
    "$bundle_root/install/install_fpocket.sh"
    "$bundle_root/scheduler"
)
if grep -RInE '/root/(data1|lnq)|GMX_MAXCONSTRWARN[[:space:]]*=[[:space:]]*-1|alias[[:space:]]+gmx=' "${runnable_paths[@]}"; then
    fail "runnable files contain a forbidden machine path, warning bypass, or gmx alias"
else
    ok "runnable files contain no legacy absolute path, constraint-warning bypass, or gmx alias"
fi

for excluded in \
    inputs/plumed_distance_atoms_wrong \
    inputs/plumed_sasa_atoms_wrong \
    inputs/plumed/sasa_ce; do
    if [[ -e "$bundle_root/$excluded" ]]; then
        fail "excluded branch is present: $excluded"
    fi
done

if find "$bundle_root/reference/original_scripts" -type f -perm /111 -print -quit | grep -q .; then
    fail "reference-only historical scripts must not be executable"
else
    ok "historical scripts are quarantined as non-executable reference files"
fi

printf 'Self-test summary: failures=%d\n' "$failures"
(( failures == 0 ))
