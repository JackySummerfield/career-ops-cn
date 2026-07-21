# Workflow 4: 面试准备

触发词："面试准备""准备面试""interview prep""模拟面试""预测问题"。

## Input

用户指定一个 tracker 中的职位（通过 id、公司名或角色名），或直接提供 JD。

## Steps

1. **读取上下文** — 加载：
   - `<USER>/resume/cv_master.md`（特别是"三 → B. 个人故事"部分）
   - `<USER>/resume/interview_playbook.md`（如存在，复用已确认的自我介绍和标准答法）
   - `<USER>/jobs/{id:03d}_{company}_{role}/eval.md`（了解 gap 和亮点）
   - 对应 JD 原文
   - 如有 `cv_suggestions.md` 或 `cv_cn.md`，也读取

2. **预测面试问题** — 基于 JD 要求和用户背景，分类生成：
   - 行为面试题（STAR类）：预测 5-8 题，标注对应维度
   - 技术/专业题：预测 3-5 题
   - 动机/文化题：预测 2-3 题（为什么这家公司/这个岗位）
   - 压力/挑战题：预测 1-2 题（gap相关、转型理由等）

3. **匹配已有故事** — 将预测问题与母版简历中已有的个人故事匹配：
   - 有现成故事可用 → 标注故事编号 + 建议微调方向
   - 无现成故事 → 标注为"需准备"，建议从哪段经历中提炼

4. **生成推荐回答框架** — 对每个预测问题输出：
   - 推荐回答要点（bullet形式，非逐字稿）
   - 应避免的陷阱
   - 可加分的细节

5. **输出并保存** — 同时保存两种格式：
   - `<USER>/jobs/{id:03d}_{company}_{role}/interview_prep.md`：标准 Markdown 源文件，便于编辑、版本管理和跨阅读器迁移
   - 从 skill 根目录运行 `python util/render_markdown.py "<USER>/jobs/{id:03d}_{company}_{role}/interview_prep.md" --output "<USER>/jobs/{id:03d}_{company}_{role}/interview_prep.html"`
   - 该命令生成 `<USER>/jobs/{id:03d}_{company}_{role}/interview_prep.html`：自包含 HTML 伴随文件，便于电脑和手机浏览器直接打开
   - 不要手工维护 HTML 正文；Markdown 是唯一可维护源文件，重新运行脚本即可同步 HTML

## Output format

```markdown
# 面试准备：[公司] [职位]

## 预测问题与推荐回答

### 行为面试题

#### Q1: [问题]
- **维度**: 领导力
- **匹配故事**: 故事3（母版简历）
- **推荐回答要点**:
  - ...
- **避免**: ...
- **加分细节**: ...

### 技术/专业题
...

### 动机/文化题
...

### 压力/挑战题
...

## 需额外准备的故事
| 维度 | 缺口 | 建议从哪段经历提炼 |
|------|------|---------------------|
| ... | ... | ... |
```

## HTML companion requirements

- 使用响应式布局，适配桌面和手机屏幕
- 使用清晰的目录导航和页内锚点，方便面试现场快速定位
- 使用信息卡片、引用框、提醒框和 STAR 标签区分内容层次
- HTML 必须是单文件、无外部网络请求、无运行时服务，双击即可在浏览器打开
- 不依赖 Obsidian 专属语法；Markdown 源文件只使用标准标题、列表、表格、引用和链接
