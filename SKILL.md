---
name: career-ops-cn
description: 'China job-search workflow for AI coding assistants: acquire job descriptions from text, URLs, or screenshots; evaluate JDs with 10-dimension scoring; manage tracker.csv; tailor resumes; structure STAR stories; prepare interviews; and debrief with audio transcription. Use for 评估JD, 看岗位, JD截图, 抓取职位链接, SPA招聘页面, job evaluation, 加入tracker, 定制简历, tailored resume, STAR, 面试故事, 求职, job search, 保存JD, 更新母版简历, master resume, 面试准备, interview prep, 面试复盘, 录音整理, and debrief.'
---

# Career Optimization Copilot

求职全流程助手：JD评估 → Tracker管理 → 简历定制 → 面试准备 → 面试复盘。

Auto-switch response language based on user input language.

---

## Workflow Routing

根据用户意图，读取对应 workflow 文件获取详细指令：

| 意图关键词 | Workflow | 文件 |
|-----------|----------|------|
| 初始化/新用户/开始求职 | W0: 初始化 | [workflows/w0-init.md](workflows/w0-init.md) |
| 补充简历/STAR/添加故事/添加项目/更新简历 | W0.5: 母版迭代 | [workflows/w0.5-master-iter.md](workflows/w0.5-master-iter.md) |
| 评估JD/看岗位/JD截图/抓取职位 | W1: JD评估 | [workflows/w1-jd-eval.md](workflows/w1-jd-eval.md) |
| 加入tracker/保存/更新状态/面试了/被拒/offer | W2: Tracker管理 | [workflows/w2-tracker.md](workflows/w2-tracker.md) |
| 定制简历/生成版本/适配/投递方向/采纳建议 | W3: 简历版本与适配 | [workflows/w3-resume-tailor.md](workflows/w3-resume-tailor.md) |
| 面试准备/准备面试/模拟面试/预测问题 | W4: 面试准备 | [workflows/w4-interview-prep.md](workflows/w4-interview-prep.md) |
| 面试复盘/录音整理/debrief/面试反馈 | W5: 面试复盘 | [workflows/w5-debrief.md](workflows/w5-debrief.md) |

> **使用方式**：识别用户意图后，用 `read_file` 加载对应 workflow 文件，按其中的 Steps 执行。多个 workflow 联动时（如 W2 依赖 W1），按依赖顺序加载。

---

## Shared Conventions

以下约定被所有 workflow 共享，不重复写入各 workflow 文件。

### Multi-user & Workspace

公共 Skill 仓库只保存通用代码和 workflow。用户数据必须位于仓库外的私有数据仓库；本 Skill
不会通过扫描自身目录或当前工作目录来猜测用户，也不会在公共仓库内创建 `users/` 副本。

- 本地模式：通过 `CAREER_OPS_DATA_ROOT` 或 CLI 的 `--data-root` 显式指定私有数据仓库根目录。
- 云端模式：通过 GitHub 插件显式访问运行时授权的 `<PRIVATE_DATA_REPOSITORY>`。
- 云端默认拒绝公共程序仓库和任何未列入私有授权配置的数据仓库；其他用户数据不连接 ChatGPT。
- 未配置数据边界时停止并请求配置，禁止回退到另一个用户或旧目录。

### 目录结构

```
career-ops-cn/
├── SKILL.md                          # 本文件（路由 + 共享约定）
├── workflows/                        # 各 workflow 详细指令
│   ├── w0-init.md
│   ├── w0.5-master-iter.md
│   ├── w1-jd-eval.md
│   ├── w2-tracker.md
│   ├── w3-resume-tailor.md
│   ├── w4-interview-prep.md
│   └── w5-debrief.md
├── references/                       # 公开参考资料
├── util/                             # 工具脚本
└── tests/                            # 仅合成数据夹具

career-ops-data-<user>/                # 外部私有数据仓库
├── profile/
├── tracker/tracker.csv
├── resumes/
│   ├── cv_master.md
│   ├── direction_diagnosis.md
│   └── versions/
└── jobs/{id:03d}_{company}_{role}/
    ├── eval.md
    ├── timeline.md
    ├── cv_suggestions.md
    ├── cv_cn.md / cv_en.md
    ├── interview_prep.md
    └── interview_debrief_r{N}.md
```

### 路径约定

以下用 `<DATA_ROOT>` 表示外部私有数据仓库根目录：

| 用途 | 路径 |
|------|------|
| 个人百科全书/母版简历 | `<DATA_ROOT>/resumes/cv_master.md` |
| 面试策略手册 | `<DATA_ROOT>/resumes/interview_playbook.md` |
| 方向诊断 | `<DATA_ROOT>/resumes/direction_diagnosis.md` |
| 稳定投递版本 | `<DATA_ROOT>/resumes/versions/{direction}_cn.md` / `{direction}_en.md` |
| 追踪表 | `<DATA_ROOT>/tracker/tracker.csv` |
| 职位目录 | `<DATA_ROOT>/jobs/{id:03d}_{company}_{role}/` |

### 数据边界识别

1. 本地运行先读取显式的 `CAREER_OPS_DATA_ROOT`，并确认它位于 Skill 仓库之外。
2. 云端运行先确认 GitHub 插件当前仓库等于私有配置中的 `CAREER_OPS_ALLOWED_DATA_REPOSITORY`，再读取目标文件。
3. 如果没有配置、仓库不匹配或存在并发 SHA 变化，停止读写并要求重新确认。
4. 不通过列出公共仓库目录来选择用户；新用户初始化应创建对应的私有数据仓库。

### Status 值（tracker.csv）

| 状态 | 含义 |
|------|------|
| `evaluating` | 评估中，尚未投递 |
| `applied` | 已投递 |
| `interviewing` | 面试中（具体轮次见 timeline.md） |
| `offer` | 已收到offer |
| `rejected` | 被拒 |
| `closed` | 职位已被公司关闭、下线或招满 |
| `withdrawn` | 主动放弃 |

### timeline.md 格式

```markdown
# Timeline: [公司] [职位]

| 日期 | 事件 | 备注 |
|------|------|------|
| 2026-06-20 | 评估 | 综合分4.2 |
| 2026-06-25 | 面试-第1轮 | HR电话面 |
| 2026-07-05 | offer | 薪资确认 |
```

### 命名规范

- 私有数据仓库按用户分离，例如 `career-ops-data-<user>`；不要在公共程序仓库内创建用户目录。
- 职位子目录：`{id:03d}_{company}_{role}`；Tracker ID 是稳定前缀，公司和职位部分做路径安全规范化，优先使用小写英文/拼音，必要时可保留 Unicode 职位名。
