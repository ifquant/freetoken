# 单次任务粒度与顺序/并行对照

后端：codebuddy。每种条件仅一个样本；先粒度、再顺序、最后并行，未随机化顺序。模型、每轮状态及用量见 summary.json 和 *-usage.json。

| 条件 | 全流程成功 | 总秒数 | 工人报告字节 |
|---|---|---:|---:|
| coarse | True | 33.205 | 1031 |
| fine | False | 62.231 | 2964 |
| serial-log | True | 30.080 | 1246 |
| serial-path | True | 31.447 | 961 |
| parallel-log | True | 25.171 | 967 |
| parallel-path | True | 25.386 | 822 |

顺序两任务墙钟 61.654s；并行两任务墙钟 25.452s。

总时间包括工人控制、检查及结果记录；验收耗时字段不包含全部 Codex 阅读/思考。报告字节是协调信息量代理，不是 token。顺序/并行计时另包含夹具创建和基线提交。

每个条件使用独立 Git 基线与新会话；fine 在同一会话调查、实现、检查，共三轮。第一轮只读检查通过。新会话不代表冷缓存；后端缓存、上游负载、启动成本和顺序效应未控制，不据此宣称稳定加速或节省比例。

CodeBuddy 使用 deepseek-v4.1-flash；dsh 使用 deepseek-official/deepseek-v4-flash，模型不同，不跨后端比较 harness 优劣。工人自检后由控制端运行冻结的 checks.py；源码范围无越界。

fine 第三轮上游返回 502 Socket is closed，CLI exit=0 但 result.is_error=true，runner 正确记录 failed。独立功能检查通过仍不把完整交卷闭环算作成功。原始失败保留，后续恢复作为单独实验，不计入本次对照。

result.usage 有累计特征，modelUsage 与 usage 字段不能直接相加；reported_cost_usd=0 不能证明免费。
