# Career Fair Battle Plan

[English](README.md) | [简体中文](README.zh-CN.md)

这是一个开源 Codex Skill，用于帮助求职者在时间有限的 Career Fair 中，对公司、具体岗位和 Session 进行优先级分配。它支持转行、相邻专业转换、Sponsorship 限制、目标方向不确定，以及线上和线下 Career Fair。

## 优化目标

项目回答的是 **“有限的 Career Fair 时间应该花在哪里？”**，而不只是“要不要申请”。最终输出四种可审计结果：

- `MUST_VISIT`
- `IF_TIME`
- `APPLY_ONLINE`
- `SKIP`

## 系统架构

- **LLM/Codex：**理解简历、生成经用户确认的候选人画像、总结证据，并编写面向用户的建议。
- **TypeSafe Jev：**在配置真实 API 访问和可调用集成后，返回原子化、带类型的 Choice、Score 和 Noul 判断。
- **确定性 Python：**处理硬约束、权重、置信度门槛、证据完整性、Fair 容量和 Session 冲突。
- **只读浏览器访问：**用户本人登录后，读取可见的 Handshake 页面；不处理密码、MFA 或 CAPTCHA。

## 当前范围

当前已实现的认证数据源是 Handshake。公开网页，以及用户提供的导出文件、截图、PDF、CSV 和复制文本，也可以作为证据来源。

LinkedIn、学校招聘门户和公司 ATS 可以通过用户可见的公开页面或经用户授权的浏览器访问进行研究，但本仓库目前**没有**专用的 LinkedIn、学校门户或 ATS 适配器，也不会自动执行注册、发送消息、投递或其他账号写入操作。

## 环境要求

根据你的使用方式准备对应环境：

| 使用方式 | 必需条件 | 可选条件 |
| --- | --- | --- |
| 在 Codex 中安装并调用完整工作流 | 支持 Skill 的 ChatGPT Desktop Codex、Codex CLI 或 Codex IDE Extension | Git；如果下载 ZIP 则不需要 |
| 运行确定性 Intake/Ranking 脚本 | Python 3.10 或更高版本 | Git |
| 研究公开公司和岗位页面 | 能访问 Web 的 Codex 环境 | Fair 导出文件或截图 |
| 读取实时 Handshake Fair | Handshake 账号、Codex 可查看的浏览器界面，以及用户授予的只读授权 | 已有公司/Session 导出文件 |
| 运行真实 Jev 判断 | 当前有效的 TypeSafe/Jev 服务权限、`TYPESAFE_API_KEY` 和可调用的 Jev 集成 | 确定性 Demo 不需要 Jev |
| 开发和验证本仓库 | Python 3.10+、Git | 使用 Codex `skill-creator` 校验器时需要 PyYAML |

运行时脚本只使用 Python 标准库。运行 `assess_intake.py`、`rank_battle_plan.py`、场景矩阵和单元测试，不需要执行任何 `pip install`。

## 安装

### 方式 A——安装为 Codex Skill

如果你希望 Codex 引导完成候选人信息收集、画像确认、证据研究、类型化判断、确定性排名和最终 Fair 作战计划，推荐使用这种方式。

#### A1. 使用 Codex Skill Installer

在 Codex 对话中调用内置安装器，并要求它从本仓库安装：

```text
$skill-installer Install the career-fair-battle-plan skill from https://github.com/SSSls/career-fair-battle-plan.
```

安装器要求审阅源码时请先检查内容。Codex 通常会自动发现新安装的 Skill；如果没有出现，请重启 Codex。最新的发现与安装规则以 [OpenAI 官方 Skill 文档](https://learn.chatgpt.com/docs/build-skills)为准。

#### A2. macOS 或 Linux 手动全局安装

Codex 会从 `$HOME/.agents/skills` 读取个人 Skill。克隆仓库，然后把仓库内部的 Skill 文件夹链接进去：

```bash
git clone https://github.com/SSSls/career-fair-battle-plan.git
cd career-fair-battle-plan
mkdir -p "$HOME/.agents/skills"
ln -s "$PWD/career-fair-battle-plan" \
  "$HOME/.agents/skills/career-fair-battle-plan"
```

使用软链接后，之后执行 `git pull` 就会更新已安装 Skill。如果希望安装独立副本，把 `ln -s` 替换为：

```bash
cp -R "$PWD/career-fair-battle-plan" "$HOME/.agents/skills/"
```

#### A3. Windows PowerShell 手动全局安装

```powershell
git clone https://github.com/SSSls/career-fair-battle-plan.git
Set-Location career-fair-battle-plan
New-Item -ItemType Directory -Force "$HOME\.agents\skills" | Out-Null
Copy-Item -Recurse -Force ".\career-fair-battle-plan" "$HOME\.agents\skills\"
```

复制后如果 Skill 没有出现，请重启 Codex。

#### A4. 只在某个仓库中安装

如果只希望这个 Skill 在特定项目中可用，请在目标项目根目录执行：

```bash
mkdir -p .agents/skills
cp -R /absolute/path/to/career-fair-battle-plan/career-fair-battle-plan \
  .agents/skills/career-fair-battle-plan
```

Codex 会从当前工作目录向上扫描到仓库根目录中的 `.agents/skills`。

#### A5. 不使用 Git 安装

1. 打开 [GitHub 仓库](https://github.com/SSSls/career-fair-battle-plan)。
2. 选择 **Code → Download ZIP** 并解压。
3. 把解压后内部的 `career-fair-battle-plan` 文件夹——即包含 `SKILL.md` 的那一层——复制到 `$HOME/.agents/skills/career-fair-battle-plan`。
4. 如果 Skill 没有自动出现，请重启 Codex。

下载 ZIP 得到的是一个静态快照。以后更新时，需要重新下载 ZIP，并只替换这个已安装 Skill 目录。

#### 验证 Skill 是否安装成功

新建一个 Codex 对话并显式调用：

```text
$career-fair-battle-plan
```

然后尝试：

```text
$career-fair-battle-plan 帮我准备 Career Fair。先收集我的 CV、学校、目标岗位、
Sponsorship 需求、其他约束和 Fair 来源。在研究或排名公司前，停下来让我确认候选人画像。
```

正确安装后，Skill 应当从 Intake 开始，不会索要密码，也不会声称已经完成注册或投递。

### 方式 B——不安装 Skill，直接运行确定性工具

这种方式适合本地测试、CI、自定义集成，或者已经有其他 Agent 能生成所需 JSON Contract 的情况。

```bash
git clone https://github.com/SSSls/career-fair-battle-plan.git
cd career-fair-battle-plan
python3 --version
python3 -m unittest discover -s tests -v
```

运行仓库自带的 Ranking 示例：

```bash
python3 career-fair-battle-plan/scripts/rank_battle_plan.py \
  career-fair-battle-plan/examples/sample_input.json \
  -o battle_plan.json
```

运行 57 个场景的 Scenario Matrix：

```bash
python3 career-fair-battle-plan/scripts/run_scenario_matrix.py \
  career-fair-battle-plan/examples/scenario_matrix.json \
  -o scenario_matrix_results.json
```

这些命令只执行确定性政策和排名逻辑。它们本身不会读取简历、浏览 Fair、调用 Jev，也不会执行任何外部操作。

可直接复制执行的完整 Smoke Test（特意保持单行命令）：

```bash
python3 career-fair-battle-plan/scripts/assess_intake.py career-fair-battle-plan/examples/sample_input.json
python3 career-fair-battle-plan/scripts/run_scenario_matrix.py career-fair-battle-plan/examples/scenario_matrix.json
python3 /Users/sunchunxuan/.codex/skills/.system/skill-creator/scripts/quick_validate.py career-fair-battle-plan
```

这里展示的是 macOS Codex 默认校验器路径；如果你的安装位置不同，请替换为本机的 `quick_validate.py` 路径。

## V2 决策状态与信息边界

四种来源模式是 `UPLOAD`、`PUBLIC_WEB`、`PUBLIC_PREVIEW` 和 `AUTHENTICATED_READ_ONLY`。`PUBLIC_PREVIEW` 不要求注册活动，也可以做初步匹配，但往往只有公司卡片或岗位标题片段，不能证明公司名单完整、JD 完整、Sponsor 政策或 Session 仍有空位。

登录状态、活动注册状态、只读授权和写入权限分别记录。`AUTHENTICATED_READ_ONLY` 表示用户自己完成登录，并授权读取当前可见页面。工作流不会注册活动或 Session、加入候补、投递或发送消息；也就是它**不会注册**，不会修改账号。

每个机会都会输出 `STOP / PARTIAL / FULL`。公司卡片等不完整线索只能得到 preliminary priority 和置信度上限；最终 Tier 需要具体岗位判断，时间表只接收已经验证的访问路线。

Jev 的成本控制顺序是：先用确定性规则过滤，再只为剩余语义问题生成类型化请求。每个结果都必须带 `live`、`fixture`、`fallback` 或 `cache` provenance、request hash 和 telemetry。本仓库不内置 Jev Client 或 Key。建议把本地 cache 放在 `.cache/career-fair-battle-plan/jev/`，并排除在 Git 外，因为压缩后的候选人信息仍可能敏感。

不使用 Git 时，选择 **Code → Download ZIP**，解压后按上文复制包含 `SKILL.md` 的内层目录。

## 准备输入

### 使用 Codex 引导工作流时

准备以下信息中你已经拥有的部分。允许暂时缺失，但缺失项必须保留为 `unknown`：

- 简历/CV、LinkedIn 导出、Portfolio 或其他背景材料；
- 学校、学位/项目、毕业时间和目标岗位类型；
- 希望从事、希望转入和明确避开的方向；
- 当前工作授权，以及现在或未来是否需要 Sponsorship；
- 地点/搬迁限制、Salary 偏好，以及 Salary 是否为硬约束；
- 你对“确认有活跃 HC”的重视程度；
- Fair 名称、日期、时区、形式和活动链接；
- 已有的公司名单、JD、Session 信息、导出文件、截图或复制文本。

不要把密码、MFA 验证码、API Key 或其他私密凭据写进文件或聊天。开始研究和排名前，系统必须向你展示候选人画像，并获得你的明确确认。

### 使用确定性脚本时

两类主要输入是：

- 供 `assess_intake.py` 使用的 **Intake JSON**；
- 符合 [`examples/sample_input.json`](career-fair-battle-plan/examples/sample_input.json) 的 **Ranking JSON**。

最小 Intake 示例：

```json
{
  "candidate_profile": {
    "approved": true,
    "cv_present": true,
    "school": "Example University",
    "degree": "MS",
    "graduation_date": "2027-05",
    "role_types": ["internship"],
    "target_areas": ["backend-swe"],
    "needs_sponsorship": true
  },
  "fair": {
    "name": "Example Fair",
    "platform": "handshake",
    "date": "2026-10-01",
    "timezone": "America/New_York",
    "format": "virtual",
    "url": "https://example.edu/fair",
    "source_mode": "AUTHENTICATED_READ_ONLY",
    "company_list_present": true
  },
  "access": {
    "user_logged_in": true,
    "authorization_scope": "read_only",
    "credentials_shared": false
  }
}
```

保存为 `intake.json`，然后运行：

```bash
python3 career-fair-battle-plan/scripts/assess_intake.py \
  intake.json -o intake_status.json
```

可能返回的 Gate State 包括 `PROFILE_REVIEW`、`NEED_FAIR_SOURCE`、`NEED_USER_LOGIN`、`NEED_READ_ONLY_AUTHORIZATION` 和 `READY_FOR_INGESTION`。创建生产输入前，请阅读 [`references/intake-and-access.md`](career-fair-battle-plan/references/intake-and-access.md) 和 [`references/data-contracts.md`](career-fair-battle-plan/references/data-contracts.md)。

## 第一次运行

1. 调用 `$career-fair-battle-plan`，提供 CV/背景、学校、求职目标、约束条件和 Fair 来源。
2. 检查系统生成的候选人画像和 Area Preference。纠正错误后，明确确认画像。
3. 如果使用导出文件，直接提供截图、PDF、CSV 或复制文本；读取这些用户提供的材料不需要平台登录。
4. 如果 Fair 位于 Handshake，请由你本人打开页面并登录。不要发送凭据。登录完成后告诉 Codex，并明确授权它只读查看当前可见的 Fair 页面。
5. 工作流将收集公司、具体岗位、Sponsorship、HC、Salary、Eligibility 和 Session 证据，并记录来源和日期；缺失信息保持为 `unknown`。
6. 如果环境中存在可调用的 Jev 集成，则运行原子化类型判断；否则必须报告 `READY_FOR_JEV`，或仅在获得你同意后使用明确标注的 Fallback。
7. 确定性 Python 生成 `MUST_VISIT`、`IF_TIME`、`APPLY_ONLINE`、`SKIP`、不确定性标记和满足时间限制的到访顺序。
8. 复核作战计划。注册、候补、邮件、消息、投递、上传、Save、Follow 和修改资料，都需要在实际执行前再次确认。

推荐的第一次使用 Prompt：

```text
$career-fair-battle-plan
我会提供 CV 和 Career Fair 链接。我找 Internship，需要未来 Sponsorship，地点偏好
New York 或 Remote，比 Salary 更重视确认存在的 HC。请先构建候选人画像并等待我确认。
我登录 Fair 后，只查看可见页面，不要替我注册任何 Session。
```

## Jev 访问

Jev 是可选项。确定性 Demo 和测试不需要 Jev。

运行真实 Jev 判断需要同时具备：

1. 当前有效的 TypeSafe/Jev 服务权限；
2. 存放在版本控制之外的有效 `TYPESAFE_API_KEY`；
3. 执行环境中可调用的 Jev Client/Tool。

本仓库提供 Jev 问题 Contract 和预期的类型化输出，但不包含 TypeSafe SDK Client。只设置 `TYPESAFE_API_KEY` 并不能证明已经连通。声称使用 Jev 前，需要重新核对当前 TypeSafe 文档并验证真实调用。

## 隐私与权限

- 只向 Jev 发送经确认的压缩画像，不发送完整简历。
- API Key、CV、导出文件、Session Cookie 和登录凭据不得进入版本控制。
- 密码和 MFA 由用户本人输入和完成。
- 不绕过认证、不处理 CAPTCHA、不访问隐藏的私有接口。
- 只读授权仅允许查看当前可见页面。
- 注册、候补、消息、邮件、投递、上传、Follow、Save 和修改资料，都必须在执行前获得用户明确确认。

## 更新

如果使用软链接安装，只需要更新 Clone：

```bash
cd /path/to/career-fair-battle-plan
git pull --ff-only
```

如果使用复制安装，请拉取或下载新版本，然后替换 `$HOME/.agents/skills` 下的 `career-fair-battle-plan` 目录。如果新指令没有被发现，请重启 Codex。

## 卸载

只删除本 Skill 的安装目录或软链接：

```bash
rm "$HOME/.agents/skills/career-fair-battle-plan"
```

如果安装的是复制目录而不是软链接，请通过文件管理器或范围明确的递归删除命令移除这个准确目录。删除已安装 Skill 不会删除单独的仓库 Clone、CV 或已经生成的计划。

Windows 用户可以在 File Explorer 中打开 `$HOME\.agents\skills`，并且只删除 `career-fair-battle-plan` 文件夹。卸载后如果它仍然出现在 Skill 选择器中，请重启 Codex。

也可以不删除文件，而是在 `~/.codex/config.toml` 中为该 `SKILL.md` 路径添加 `[[skills.config]]` 并禁用它。配置格式请以当前 [OpenAI 官方 Skill 文档](https://learn.chatgpt.com/docs/build-skills)为准。

## 常见问题

### Codex 找不到 Skill

- 确认 `$HOME/.agents/skills/career-fair-battle-plan/SKILL.md` 存在；如果使用项目级安装，则检查当前仓库中的 `.agents/skills/career-fair-battle-plan/SKILL.md`。
- 确保复制的是仓库内部的 `career-fair-battle-plan` 文件夹，而不是只复制外层仓库。
- 如果自动发现没有刷新，请重启 Codex。
- 使用 `$career-fair-battle-plan` 显式调用，不要只依赖隐式匹配。

### 缺少 `python3` 或版本过低

安装 Python 3.10 或更高版本，然后运行 `python3 --version`。Windows 上命令可能是 `py -3`；运行脚本和测试时请始终使用同一个解释器。

### Intake 停在某个 Gate

这是预期的安全行为。请根据返回状态处理：

- `PROFILE_REVIEW`：补全或明确确认候选人画像；
- `NEED_FAIR_SOURCE`：提供导出文件、公开 URL 或已登录页面；
- `NEED_USER_LOGIN`：由你本人完成登录；
- `NEED_READ_ONLY_AUTHORIZATION`：明确授权查看可见页面。

### Handshake 信息不完整

工作流只能读取已登录用户能够看到的内容。必要时打开公司、岗位和 Session 页面。缺失项必须保持为 `unknown`；Skill 不得推断隐藏名额、Recruiter 姓名或招聘结论。

### Jev 没有运行

分别检查服务权限、Key 配置和可调用 Client/Tool。本仓库的 Python 脚本是确定性的，不会发起 Jev API 调用。仅在本地设置 Key 不能证明连通成功。

### Ranking 拒绝 JSON

把输入与 [`examples/sample_input.json`](career-fair-battle-plan/examples/sample_input.json) 和完整的 [`data-contracts.md`](career-fair-battle-plan/references/data-contracts.md) 对照。明确的 Sponsorship、Salary、HC 和岗位 Claim 必须引用有效 Evidence ID。

## 仓库结构

```text
career-fair-battle-plan/
├── SKILL.md
├── agents/openai.yaml
├── examples/
├── references/
└── scripts/
tests/
```

可安装 Skill 的入口文件是 [`career-fair-battle-plan/SKILL.md`](career-fair-battle-plan/SKILL.md)。

## 工作流程

1. 检查候选人信息和 Fair 数据是否完整。
2. 在线读取 Handshake 前，要求用户本人登录并授权只读查看。
3. 构建并确认候选人画像和目标方向集合。
4. 将 Fair 标准化为 `公司 × 具体岗位`。
5. 先做低成本筛选，再对候选公司深度研究。
6. 收集岗位、Sponsorship、HC、Salary、Eligibility 和 Session 的可追溯证据。
7. 运行 Jev 类型化判断；如果 Jev 不可用，则明确说明没有运行。
8. 使用确定性代码排名，并生成满足时间约束的 Career Fair 作战计划。

缺失或冲突的证据保持为 `unknown`；历史 H-1B/PERM 活动不能证明当前岗位提供 Sponsorship。

## 验证情况

- 85 个确定性和文档行为测试；
- 57 个可编辑参数化场景；
- 10 个独立 Agent 模拟：3 个无 Skill baseline 和 7 个使用 Skill 的 forward test；
- 官方 `quick_validate.py` 包结构验证。

已经人工验证 Handshake 登录后的只读访问。仓库尚未验证真实 Jev API 连通性。

## 许可证

[MIT](LICENSE)
