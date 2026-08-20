# Runtime binaries (site-local; not vendored in this pack)

| Binary / stack | Typical path on this site | Required for |
|---|---|---|
| Python >=3.10 + pyyaml/pydantic | env with `pip install -e AlloDesigner_MultiAgent` | Orchestrator |
| GROMACS+PLUMED | `/home/ubuntu/opt/gmx-stack/env.sh` | Stage4 recompute |
| fpocket/mdpocket | `/home/ubuntu/opt/fpocket-4.2.3/bin/` | Stage5 geometry |
| AutoDock Vina | operator PATH | Stage6 real docking (optional) |
| Schrödinger Glide | licensed site | Stage6 real docking (optional) |
| Allo-MD agentctl | `AlloDesigner/Allo-MD` | Stage4 job execution |
