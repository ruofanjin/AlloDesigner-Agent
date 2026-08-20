# 01_taskspec

人类冻结的任务单。字段至少包含：

- `target` / `track` / `stages_enabled`
- `allowed_priors` / `forbidden_information`
- `human_approvals`（信息边界已批）
- `budget`（`max_md_ns`、`allow_external_vs`、`prefer_recompute`）

盲态轨：`answer_store_ref` 仅用于评价侧，不得注入 runtime 工具特征。
