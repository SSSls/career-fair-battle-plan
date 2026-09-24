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
- **TypeSafe Jev：**在配置真实 API 后，返回原子化、带类型的 Choice、Score 和 Noul 判断。
- **确定性 Python：**处理硬约束、权重、置信度门槛、证据完整性、Fair 容量和 Session 冲突。
- **只读浏览器访问：**用户本人登录后，读取可见的 Handshake 页面；不处理密码、MFA 或 CAPTCHA。

## 所需输入

- 简历或等效的背景材料；
- 学校、学位/项目、毕业时间和目标岗位类型；
- 目标方向、转向方向和明确避开的方向；
- 工作授权和 Sponsorship 需求；
- 地点、Salary 和 Headcount 偏好；
- Fair 名称、日期、时区、形式、链接，以及已有公司和 Session 数据。

在开始公司研究和排名前，用户必须明确确认候选人画像。

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

## 快速开始

```bash
python3 career-fair-battle-plan/scripts/assess_intake.py intake.json

python3 career-fair-battle-plan/scripts/rank_battle_plan.py \
  career-fair-battle-plan/examples/sample_input.json \
  -o career-fair-battle-plan/examples/sample_output.json

python3 career-fair-battle-plan/scripts/run_scenario_matrix.py \
  career-fair-battle-plan/examples/scenario_matrix.json \
  -o career-fair-battle-plan/examples/scenario_matrix_results.json

python3 -m unittest discover -s tests -v
```

确定性脚本只使用 Python 标准库。

## Jev 访问

真实 Jev 判断需要有效的 TypeSafe API 访问权限和 `TYPESAFE_API_KEY`。仓库不包含任何凭据。确定性 Demo 不能证明真实 Jev 已连通；由于 API 可能变化，集成前需要重新查看 TypeSafe 官方文档。

## 隐私与权限

- 只向 Jev 发送经过确认的压缩画像，不发送完整简历。
- API Key 和登录凭据不得进入版本控制。
- 密码和 MFA 由用户本人输入和完成。
- 不绕过认证，不访问隐藏的私有接口。
- 注册、候补、消息、邮件、投递、上传、Follow、Save 和修改资料，都必须在执行前获得用户明确确认。

## 验证情况

- 36 个确定性行为测试；
- 22 个可编辑参数化场景；
- 10 个独立 Agent 模拟：3 个无 Skill baseline 和 7 个使用 Skill 的 forward test；
- 官方 `quick_validate.py` 包结构验证。

已经人工验证 Handshake 登录后的只读访问。仓库尚未验证真实 Jev API 连通性。

## 当前范围

当前已实现的认证数据源是 Handshake，同时支持公开网页和用户提供的导出文件。LinkedIn、学校招聘门户和公司 ATS 目前是设计目标，尚未成为已完成的适配器。

## 许可证

[MIT](LICENSE)
