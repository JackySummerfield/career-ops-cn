# SPA页面抓取经验 & WLB参考资源

## SPA抓取限制

### Boss直聘 (zhipin.com) — 旧 Playwright 方案失败
*Source: 2026-06-03 — job search session*

Boss直聘检测CDP（Chrome DevTools Protocol）连接本身，属于深层反爬机制：
- headed Playwright 访问职位详情页 → 仍跳转 about:blank
- 复用 Edge User Data → 冲突（about:blank）
- 独立 profile → 仍被检测

**当前结论**：旧的独立 Playwright + Edge 方案和当前 Codex 浏览器控制均会触发阻断。保留低频、只读的运行时验证，但默认把截图直读作为 Boss 详情页的可靠路径。不要绕过验证码、安全挑战或读取会话秘密。

#### 2026-07-12/13 Codex 实测

- 职位列表页和具体职位页在普通 Chrome 中能显示正确标题与 URL；浏览器控制接管后出现空白 viewport / 空 DOM。
- Codex 应用内浏览器访问相同页面同样返回空 DOM。
- 对桌面域名和移动域名进行无 Cookie 的普通 HTTP GET，均先 `302` 到 `/web/passport/zp/security.html`，最终只返回约 42KB 的 JavaScript 安全检查页，不包含 JD。
- 搜索引擎能索引具体职位标题和少量职责/要求摘要，但转载页可能过期，摘要不足以替代完整 JD。
- `robots.txt` 没有全面禁止无查询参数的哈希职位详情 URL，但这不代表授权绕过运行时安全检查。
- 官方 BossHi 开放平台需要应用权限和 access token，面向 BossHi 应用能力，不是面向个人求职者的公开职位数据 API。
- Boss 用户协议禁止未经许可的插件/第三方工具接入、爬虫和规避技术措施；不集成依赖 Cookie、私有 API 或安全挑战规避的社区工具。

**稳定处理方式**：低频尝试普通读取、搜索摘要和受支持浏览器；遇到安全检查或空 DOM 后立即停止，接受用户截图并直接视觉识别。截图只保留标题、薪资、地点、职责和要求，长页面使用 2–4 张略有重叠的截图。不要要求用户先做 OCR。

参考：
- [BOSS直聘 robots.txt](https://www.zhipin.com/robots.txt)
- [BOSS直聘用户协议](https://www.zhipin.com/web/common/protocol/protocol-2019-09-30.html)
- [BossHi 开放平台概述](https://histatic.zhipin.com/front/bosshi-mp-docs/service/ready/overview.html)
- [boss-agent-cli](https://github.com/can4hou6joeng4/boss-agent-cli)（社区实现，仅用于调研其能力与风险边界，不纳入本 Skill）

### 可成功抓取的平台
- ✅ 阿里云招聘 (careers.aliyun.com) — 静态渲染
- ✅ 猎聘 (liepin.com) — 静态渲染
- ✅ Workday系统 (如液化空气) — 静态渲染
- ⚠️ Boss直聘 — Playwright 与 Codex 浏览器控制均触发阻断；搜索摘要不完整，截图直读最稳定
- ❌ 蚂蚁招聘 — SPA（未尝试Playwright）
- ❌ 西门子 — SPA（未尝试Playwright）
- ❌ Bosch — SPA（未尝试Playwright）

### fetch_jd.py 兜底脚本
- 跨平台使用 Playwright Chromium，也可显式选择本机 Chrome 或 Edge channel
- 启动独立浏览器 context，不读取用户浏览器 profile
- 验证码处理：检测内容长度 < 200字符 → 暂停等待用户手动处理 → 用户按Enter继续
- 不注入 stealth 脚本，也不修改浏览器指纹；遇到验证码或安全挑战时停止并改用用户截图

---

## GitHub WLB参考项目
*Source: 2026-06-03 — job search session*

| 项目 | 内容 | 链接 |
|------|------|------|
| **955.WLB** | 955公司白名单（相对不加班） | [formulahendry/955.WLB](https://github.com/formulahendry/955.WLB) |
| **996.ICU** | 996公司黑名单（含证据） | [996icu/996.ICU](https://github.com/996icu/996.ICU) |

**使用建议**：
- 作为求职时WLB的辅助参考，不作为评分维度（同公司不同BU差异大）
- 脉脉/看准网/Glassdoor 等点评网站可能有反爬；按 [jd-fetching.md](jd-fetching.md) 的分层策略现场验证
- 训练数据中的公开信息（截止2025年）可给出大致WLB估计+置信度
