# Workflow 2: 加入Tracker & 状态更新

## 加入Tracker

用户说"加入"/"保存"/"加入tracker"时：

1. **必须先执行 Workflow 1（JD评估）**，生成 10 维度评分和综合分
2. **必须将完整评估报告展示给用户**（包括10维度表格、综合评分、Gap和亮点），然后询问是否加入 Tracker。评估是给用户看的决策参考，不是内部静默步骤。
3. 用户确认后，追加一行到 `<USER>/tracker.csv`（`id` 自增，`score` 取评估综合分，`status` 默认 `evaluating`，`last_updated` 为当天）
4. 创建 `<USER>/jobs/{id:03d}_{company}_{role}/eval.md`（包含完整评估报告）
5. 创建 `<USER>/jobs/{id:03d}_{company}_{role}/timeline.md`，写入第一条记录

> **不可跳过评估**：即使用户同时说"加入tracker并标记为已投递"，也必须先完成并展示评估再追加记录。当用户在同一条消息中同时提供 JD 和"加入"指令时，流程不变——先展示评估，再加入。

## 更新状态

用户说"更新状态"/"面试了"/"拿到offer"/"被拒了"等触发：

1. 更新 `tracker.csv` 中对应行的 `status` 和 `last_updated`
2. 在 `timeline.md` 末尾追加一行新记录（日期 + 新状态 + 用户提供的备注）
3. 如用户提供了面试细节（问了什么、感受如何），一并记录在备注中

> **不覆盖历史** — tracker.csv 只反映当前状态，timeline.md 保留完整轨迹。

## Dashboard 刷新

每次 tracker 变更后（加入或更新状态），运行：

```
python util/gen_dashboard.py --user <username>
python util/gen_dashboard.py --user <username> --format html --vscode
```

默认生成 `<USER>/dashboard.md`，适用于 Obsidian、VS Code Markdown Preview 和其他标准 Markdown 阅读器；第二条命令生成可双击打开的 `<USER>/dashboard.html` 兼容视图。

## 新职位目录命名规则

新加入 tracker 的职位，目录名使用 `{id:03d}_{company}_{role}` 格式（如 `022_bytedance_ai_engineer`），其中 company 和 role 做路径安全规范化，优先使用小写英文/拼音，空格和特殊字符用下划线替代；需要保留原始职位名时可使用 Unicode。
