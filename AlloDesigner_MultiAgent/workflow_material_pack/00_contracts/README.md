# 00_contracts

放入并冻结：

- `stages.yaml` — 六阶段科学合同  
- `tool_registry.yaml` — 工具与成熟度  
- `reference_path.yaml` — 参考热启动路径  
- `*.schema.json` — ReasoningPlan / ExecutionNode / DecisionPacket / Stage6 return  

Agent 可读这些文件生成推理链，但**不可改写阶段 goal / 硬依赖**。
