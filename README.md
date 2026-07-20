<div align="center">

# 💼 Career Ops CN

#### 国内求职全流程 AI Skill —— JD抓取、10维评估、Tracker管理、简历定制、面试准备

![VS Code 1.99+](https://img.shields.io/badge/VS_Code-1.99+-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white)
![GitHub Copilot](https://img.shields.io/badge/GitHub_Copilot-Skill-000?style=for-the-badge&logo=githubcopilot&logoColor=white)
![OpenAI Codex](https://img.shields.io/badge/OpenAI_Codex-Compatible-111?style=for-the-badge&logo=openai&logoColor=white)
![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

[为什么做这个](#-为什么做这个) · [它能做什么](#-它能做什么) · [快速开始](#-快速开始) · [Workflow](#-workflow-overview)

中文 · [English](README.en.md)

</div>

---

## 🤔 为什么做这个

本项目 inspired by [career-ops](https://github.com/santifer/career-ops)，面向**国内求职场景**，适配 GitHub Copilot 和 OpenAI Codex 等主流 AI 编程助手：

- **多平台兼容** — 不写死客户端专用工具；Copilot Chat、Codex CLI、Claude Code 等均可使用
- **国内招聘平台适配** — Boss直聘、猎聘、拉勾等 SPA 页面抓取；截图直接识别 JD
- **10 维度 JD 评估** — 角色匹配、技能覆盖、成长空间、薪资、地理位置等维度独立打分，辅助投递决策
- **面试材料生成** — STAR 素材结构化 + HTML 面试手册（公司背景、高频问题、反问清单）
- **多用户隔离** — `users/<name>/` 独立工作区，个人数据 gitignore，Skill 可公开共享
- **诊断式简历定制** — 母版简历保持大而全事实库，先推荐投递方向并生成稳定版本，再对具体JD给轻量适配建议，用户确认后才落盘
- **分层 JD 抓取** — 静态读取、搜索恢复、已登录浏览器 DOM、用户协助和文本粘贴逐级回退

## 📋 它能做什么

| 功能 | 触发语 | 说明 |
|------|--------|------|
| 评估 JD | `评估这个JD：[文本]` | 10 维度打分 + 综合评分 + Gap 分析 |
| 管理 Tracker | `加入tracker` | CSV 格式职位追踪，自增 ID，状态管理 |
| 简历方向诊断 | `根据母版推荐投递方向` | 基于母版简历分析可投方向，让用户确认主攻/过渡/保底方向 |
| 生成稳定简历版本 | `生成AI解决方案版简历` | 按用户确认的投递方向，从母版事实库裁剪生成稳定投递版本 |
| JD轻量适配 | `针对#6给我定制建议` | 只输出关键词、排序、表达建议；用户确认采纳后才生成最终简历 |
| 面试准备 | `面试准备` / `准备面试` | 基于 JD 预测问题 + 匹配已有 STAR 故事 + 生成回答框架 |
| 面试复盘 | `面试复盘` / `录音整理` | 音频转录 → 逐题分析 → 模式识别 → 反哺母版简历 |
| 母版迭代 | `补充简历` / `添加故事` / `STAR` | 随时补充经历到母版事实库，自动结构化为 STAR 格式 |
| 获取 JD | `抓取这个链接：[URL]` / 发送截图 | 分层读取招聘页面；被反自动化阻断时直接识别截图，无需用户 OCR |

## 🚀 快速开始

**1. 安装 Skill**

```bash
# Windows (放入 .agents/skills 或 .copilot/skills 均可)
git clone https://github.com/jackysummerfield/career-ops-cn.git "%USERPROFILE%\.agents\skills\career-ops-cn"

# macOS / Linux
git clone https://github.com/jackysummerfield/career-ops-cn.git ~/.agents/skills/career-ops-cn
```

**2. 初始化工作区**

在 Codex 或 Copilot Chat 里输入 `初始化求职工作区`，按提示填入简历内容。

**3. 验证**

输入 `评估这个JD：[粘贴任意JD]`，看到 10 维度评分表格就说明装好了。

> 💡 支持任何具备文件读写能力的 AI 助手（Copilot Chat、Codex、Claude Code 等）。如客户端支持浏览器控制能力，可直接读取 SPA 招聘页面；否则通过截图识别或文本粘贴兜底。详见 [references/jd-fetching.md](references/jd-fetching.md)。

## ⚙️ Workflow Overview

```mermaid
flowchart TD
    subgraph W0 ["W0 初始化"]
        A["📝 初版简历 + 补充信息"] --> B["📚 母版事实库"]
    end

    subgraph W3A ["W3 方向诊断"]
        B --> C["🎯 投递方向诊断"]
        C --> D["✅ 用户确认方向"]
        D --> E["📄 稳定投递版本"]
    end

    subgraph W1W2 ["W1 JD评估 + W2 Tracker"]
        F["🔍 获取 JD"] --> G["📊 10维度评估"]
        G --> H{"≥ 3.5?"}
        H -->|"✅ 值得投"| I["📌 加入 Tracker"]
        H -->|"❌ 跳过"| F
    end

    subgraph W3C ["W3 简历适配"]
        I --> J["💡 JD轻量适配建议"]
        J --> K["👤 用户确认采纳"]
        K --> L["📨 最终简历"]
    end

    subgraph W4W5 ["W4 面试准备 + W5 复盘"]
        L --> M["🎭 面试准备"]
        M --> N["💬 面试复盘"]
    end

    E --> F
    N -.->|"🔄 反哺母版"| B

    style W0 fill:#e8f4fd,stroke:#4a90d9
    style W3A fill:#e8fde8,stroke:#4a9a4a
    style W1W2 fill:#fff3e0,stroke:#e6930a
    style W3C fill:#fde8f4,stroke:#d94a90
    style W4W5 fill:#f3e8fd,stroke:#904ad9
```

> 💡 母版简历是一个持续积累的事实库，不直接投递；稳定版本用于某个投递方向，具体JD只做轻量建议并等待用户确认。面试复盘会自动反哺母版简历，形成闭环。

## 📄 输出示例

<details>
<summary><b>母版简历</b></summary>

```markdown
# 张三 | 高级产品经理

## 基本信息
- 电话：138-xxxx-xxxx | 邮箱：zhangsan@email.com
- 坐标：北京 | 期望薪资：80-100w

## 求职意向
AI产品总监 / AI平台产品负责人

## 职业摘要
6年产品经验，专注AI/数据中台方向，擅长从0-1搭建产品并规模化落地。

## 核心技能
- 产品规划与路线图制定
- LLM/NLP 应用落地
- 跨部门协作与团队管理（8人）
- A/B 实验体系搭建
- 数据驱动决策

## 工作经历

### 高级产品经理 | ABC科技 | 2022.03 - 至今
- 负责 AI 中台产品从 0-1 搭建，DAU 从 0 增长至 5万
- 管理 8 人产品团队，主导跨部门协作
- 推动 LLM 落地，上线智能客服模块，人工介入率降低 40%

### 产品经理 | DEF互联网 | 2019.06 - 2022.02
- 负责电商搜索推荐模块，GMV 提升 15%
- 设计 A/B 实验平台，支撑 200+ 实验并行

## 教育背景
- 硕士 | XX大学 计算机科学 | 2017-2019
- 学士 | XX大学 软件工程 | 2013-2017

## 项目亮点 / STAR 素材库
（详见 cv_master.md 的个人故事部分）

## 证书 & 其他
- PMP 认证
- 英语 流利（雅思7.5）
```

</details>

<details>
<summary><b>10维度评估表</b></summary>

```markdown
## 评估：ABC科技 AI产品总监（北京）

| 维度 | 分数 | 说明 |
|------|------|------|
| 角色匹配 | 4.5 | 当前岗位自然升级路径 |
| 技能覆盖 | 4.0 | LLM落地经验高度匹配，缺商业化P&L |
| 经验年限 | 4.0 | 要求5年+，实际6年 |
| 行业契合 | 3.5 | AI方向一致，但to B → to C有跨度 |
| 成长空间 | 4.5 | 汇报VP，有团队扩张计划 |
| 薪资范围 | 4.0 | 80-120w，符合预期 |
| 公司规模 | 3.5 | B轮，有不确定性 |
| 地理位置 | 5.0 | 本地 |
| 文化匹配 | 4.0 | 扁平、技术驱动 |
| 竞争难度 | 3.0 | 岗位已开放3周，竞争激烈 |

**综合评分：4.05 / 5.0**

**关键Gap**: 缺乏P&L独立负责经验
**差异化亮点**: LLM落地实战 + A/B实验平台搭建
```

</details>

<details>
<summary><b>面试准备材料</b></summary>

```markdown
# 面试准备：ABC科技 AI产品总监

## 公司背景
- ABC科技，B轮，AI SaaS 赛道，2023年融资2亿
- 核心产品：企业级AI中台，服务金融/零售行业
- 团队规模：~200人，产品团队20人

## 岗位关键信息
- 汇报对象：产品VP
- 团队：直管5人，虚线8人
- 核心KPI：AI模块商业化收入、客户续费率

## STAR 素材（按JD要求匹配）

### 素材1：推动LLM智能客服上线（匹配"AI落地经验"）
**S**: 客服团队30人，日均2000+工单，人力成本高
**T**: Q3上线智能客服，降低人工介入率
**A**: 调研供应商 → 混合方案设计 → 三方对齐 → 灰度放量
**R**: 人工介入率72%→40%，月省45万

### 素材2：搭建A/B实验平台（匹配"数据驱动"）
**S**: 各团队实验流程混乱，结果不可信
**T**: 搭建统一实验平台
**A**: 定义指标体系 → 开发分流引擎 → 建立评审机制
**R**: 支撑200+并行实验，决策效率提升60%

## 高频问题准备
- Q: 你如何推动一个跨部门项目？
- Q: 描述一次产品决策失误及复盘
- Q: 如何衡量AI产品的ROI？

## 反问清单
- 这个岗位未来6个月最重要的3件事是什么？
- 团队目前的技术债/组织债是什么？
- 汇报线和决策流程是怎样的？
- AI模块目前的商业化阶段？
```

</details>

## 🌟 References & Credits

- [career-ops](https://github.com/santifer/career-ops) — 项目灵感来源
- [Playwright](https://playwright.dev/) — 无受支持浏览器控制能力时的 SPA 抓取兜底
- [955.WLB](https://github.com/formulahendry/955.WLB) / [996.ICU](https://github.com/996icu/996.ICU) — WLB 参考数据
