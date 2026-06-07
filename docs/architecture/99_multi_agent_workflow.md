# 多 Agent 协同开发流程

## 1. 文档目的

本文档记录本项目使用多个 Codex Agent 协同开发的标准流程。

目标是避免以后忘记：

- 如何创建和同步 worktree；
- 如何启动不同 Agent；
- 如何检查 Agent 是否越界修改；
- 如何合并分支；
- 如何处理冲突；
- 如何更新 `AGENTS.md` 和 agent prompt；
- 每一轮开发应该按什么顺序推进。

本文档是操作手册，不是架构设计文档。

------

## 2. 基本原则

本项目采用：

```text
main 主工程
  + 多个 Git worktree
  + 多个 Codex Agent
  + AGENTS.md 约束
  + agents/*_prompt.md 任务说明
```

核心原则：

```text
一个 Agent 一个 worktree
一个 Agent 一个 branch
main 只做集成
Agent 不直接在 main 上大改
每次合并后都跑 pytest
```

不要让多个 Agent 同时进入同一个目录。

不要让多个 Agent 同时修改同一个文件。

------

## 3. 推荐目录布局

工作区：

```text
D:\labs\rm_ai_workspace\
```

主工程和各 worktree：

```text
rm_ref_main\          main 分支，只做集成
rm_ref_core\          codex/core
rm_ref_config\        codex/config
rm_ref_packer\        codex/packer
rm_ref_algo_demo\     codex/algo-demo
rm_ref_tests\         codex/tests
rm_ref_review\        codex/review
```

主工程目录结构：

```text
rm_ref_main/
├── AGENTS.md
├── agents/
├── docs/
├── src/
│   └── rm_ref/
│       ├── core/
│       ├── schema/
│       ├── config/
│       ├── validator/
│       ├── packer/
│       ├── io/
│       ├── observability/
│       └── algorithms/
├── schema_defs/
├── tests/
├── utils/
└── scripts/
```

------

## 4. AGENTS.md 与 prompt 的职责

### 4.1 AGENTS.md

`AGENTS.md` 是长期规则。

它用于告诉 Codex：

- 项目边界；
- Python 版本约束；
- 哪些目录能改；
- 哪些目录不能改；
- 哪些依赖方向禁止；
- 测试命令是什么。

常见位置：

```text
AGENTS.md
src/AGENTS.md
src/rm_ref/core/AGENTS.md
src/rm_ref/config/AGENTS.md
src/rm_ref/packer/AGENTS.md
tests/AGENTS.md
```

### 4.2 agents/*_prompt.md

`agents/*_prompt.md` 是某类 Agent 的任务说明。

例如：

```text
agents/core_agent_prompt.md
agents/config_agent_prompt.md
agents/packer_agent_prompt.md
agents/tests_agent_prompt.md
agents/review_agent_prompt.md
```

它们用于告诉 Codex：

- 当前 Agent 是什么角色；
- 本轮应该做什么；
- 允许改哪些文件；
- 禁止改哪些文件；
- 跑哪些测试；
- 完成时汇报什么。

### 4.3 修改原则

长期规则改 `AGENTS.md`。

本轮任务改 `agents/*_prompt.md`。

架构决策写到 `docs/architecture/`。

不要把一次性任务写进根目录 `AGENTS.md`。

------

## 5. 第一次创建 worktree

在主工程执行：

```powershell
cd D:\labs\rm_ai_workspace\rm_ref_main
```

创建 worktree：

```powershell
git worktree add ..\rm_ref_core -b codex/core
git worktree add ..\rm_ref_config -b codex/config
git worktree add ..\rm_ref_packer -b codex/packer
git worktree add ..\rm_ref_algo_demo -b codex/algo-demo
git worktree add ..\rm_ref_tests -b codex/tests
git worktree add ..\rm_ref_review -b codex/review
```

查看 worktree：

```powershell
git worktree list
```

------

## 6. 已有 worktree 时同步 main

当 main 更新后，进入对应 worktree：

```powershell
cd D:\labs\rm_ai_workspace\rm_ref_core
git merge main
```

其他 worktree 同理：

```powershell
cd D:\labs\rm_ai_workspace\rm_ref_config
git merge main

cd D:\labs\rm_ai_workspace\rm_ref_packer
git merge main

cd D:\labs\rm_ai_workspace\rm_ref_algo_demo
git merge main

cd D:\labs\rm_ai_workspace\rm_ref_tests
git merge main
```

如果 merge 出现冲突，先解决冲突再继续启动 Agent。

------

## 7. 启动 Codex 的通用方式

进入对应 worktree：

```powershell
cd D:\labs\rm_ai_workspace\rm_ref_core
```

如需代理：

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7897"
$env:HTTPS_PROXY="http://127.0.0.1:7897"
$env:ALL_PROXY="http://127.0.0.1:7897"
```

启动 Codex：

```powershell
codex -c features.apps=false
```

通用启动提示：

```text
Read AGENTS.md.
Read src/AGENTS.md.
Read src/rm_ref/AGENTS.md.
Read the nearest package AGENTS.md.
Read the corresponding agents/*_prompt.md.

Follow the allowed file boundaries.
Do not commit automatically.
Stop after reporting files changed, tests run, failures, known limitations.
```

------

## 8. Core Agent 流程

目录：

```powershell
cd D:\labs\rm_ai_workspace\rm_ref_core
codex -c features.apps=false
```

发送：

```text
Read AGENTS.md.
Read src/AGENTS.md.
Read src/rm_ref/AGENTS.md.
Read src/rm_ref/core/AGENTS.md.
Read agents/core_agent_prompt.md.

You are the Core Agent.

Implement or refine the minimal reusable RM execution core.

Work only in:
- src/rm_ref/core/
- tests/test_core/
- tiny pytest.ini/setup.py import fixes only if necessary

Do not modify schema/config/validator/packer/algorithms.

Run:
python -m pytest -q tests/test_core

Do not commit automatically.
Stop after reporting files changed, tests run, current failures, known limitations.
```

完成后人工检查：

```powershell
git status
git diff --name-only
git diff --stat
python -m pytest -q tests/test_core
```

确认没越界后提交：

```powershell
git add .
git commit -m "agent core: add minimal core execution framework"
```

------

## 9. Config Agent 流程

目录：

```powershell
cd D:\labs\rm_ai_workspace\rm_ref_config
codex -c features.apps=false
```

发送：

```text
Read AGENTS.md.
Read src/AGENTS.md.
Read src/rm_ref/AGENTS.md.
Read src/rm_ref/schema/AGENTS.md.
Read src/rm_ref/config/AGENTS.md.
Read src/rm_ref/validator/AGENTS.md.
Read agents/config_agent_prompt.md.

You are the Config Agent.

Implement or refine:
schema dict
  -> schema object / registry
  -> UserConfig
  -> ResolvedConfig
  -> Validator

Work only in:
- src/rm_ref/schema/
- src/rm_ref/config/
- src/rm_ref/validator/
- schema_defs/
- tests/test_schema/
- tests/test_config/
- tests/test_validator/

Do not modify:
- src/rm_ref/core/
- src/rm_ref/packer/
- src/rm_ref/algorithms/

Run:
python -m pytest -q tests/test_schema tests/test_config tests/test_validator
python -m pytest -q tests/test_core

Do not commit automatically.
Stop after reporting files changed, tests run, current failures, known limitations.
```

检查：

```powershell
git status
git diff --name-only
git diff --stat
python -m pytest -q tests/test_schema tests/test_config tests/test_validator
python -m pytest -q tests/test_core
```

提交：

```powershell
git add .
git commit -m "agent config: add schema config validator flow"
```

------

## 10. Packer Agent 流程

目录：

```powershell
cd D:\labs\rm_ai_workspace\rm_ref_packer
codex -c features.apps=false
```

发送：

```text
Read AGENTS.md.
Read src/AGENTS.md.
Read src/rm_ref/AGENTS.md.
Read src/rm_ref/packer/AGENTS.md.
Read agents/packer_agent_prompt.md.

You are the Packer Agent.

Implement or refine the hardware word packer.

Work only in:
- src/rm_ref/packer/
- tests/test_packer/
- docs/architecture/08_packer.md only if necessary

Do not modify:
- src/rm_ref/core/
- src/rm_ref/schema/
- src/rm_ref/config/
- src/rm_ref/validator/
- src/rm_ref/algorithms/

Run:
python -m pytest -q tests/test_packer
python -m pytest -q tests/test_schema tests/test_config tests/test_validator

Do not commit automatically.
Stop after reporting files changed, tests run, current failures, known limitations.
```

检查：

```powershell
git status
git diff --name-only
git diff --stat
python -m pytest -q tests/test_packer
```

提交：

```powershell
git add .
git commit -m "agent packer: add hardware word packer"
```

------

## 11. Algo Demo Agent 流程

目录：

```powershell
cd D:\labs\rm_ai_workspace\rm_ref_algo_demo
codex -c features.apps=false
```

发送：

```text
Read AGENTS.md.
Read src/AGENTS.md.
Read src/rm_ref/AGENTS.md.
Read src/rm_ref/algorithms/AGENTS.md.
Read agents/algo_demo_agent_prompt.md.

You are the Algo Demo Agent.

Implement a small demo echo algorithm.

Work only in:
- src/rm_ref/algorithms/
- tests/test_algorithms/
- tests/test_integration/ only if needed

Do not implement SRS/PUSCH/PRACH.
Do not modify schema/config/validator/packer.
Do not redesign core.

Run:
python -m pytest -q tests/test_algorithms
python -m pytest -q tests/test_core

Do not commit automatically.
Stop after reporting files changed, tests run, current failures, known limitations.
```

检查：

```powershell
git status
git diff --name-only
git diff --stat
python -m pytest -q tests/test_algorithms
python -m pytest -q tests/test_core
```

提交：

```powershell
git add .
git commit -m "agent algo-demo: add demo echo algorithm"
```

------

## 12. Tests Agent 流程

目录：

```powershell
cd D:\labs\rm_ai_workspace\rm_ref_tests
codex -c features.apps=false
```

发送：

```text
Read AGENTS.md.
Read src/AGENTS.md.
Read tests/AGENTS.md.
Read agents/tests_agent_prompt.md.

You are the Tests Agent.

Build or refine pytest coverage.

Work mainly in:
- tests/
- pytest.ini only if needed
- setup.py only if needed

Do not rewrite source implementation.

Run:
python -m pytest -q

Do not commit automatically.
Stop after reporting files changed, tests run, current failures, known limitations.
```

检查：

```powershell
git status
git diff --name-only
git diff --stat
python -m pytest -q
```

提交：

```powershell
git add .
git commit -m "agent tests: add pytest coverage"
```

------

## 13. Review Agent 流程

目录：

```powershell
cd D:\labs\rm_ai_workspace\rm_ref_review
codex -c features.apps=false
```

发送：

```text
Read AGENTS.md.
Read agents/review_agent_prompt.md.

You are the Review Agent.

Review the repository and write:
docs/review/review_report.md

Do not modify source code.
Do not modify tests.
Do not commit automatically.

Focus on:
- Python 3.6 compatibility
- layering violations
- missing tests
- unclear errors
- core pollution
- config/runtime mixing
```

检查：

```powershell
git status
git diff --name-only
git diff --stat
```

提交：

```powershell
git add docs/review/review_report.md
git commit -m "agent review: add review report"
```

------

## 14. main 合并流程

回主工程：

```powershell
cd D:\labs\rm_ai_workspace\rm_ref_main
```

推荐合并顺序：

```powershell
git merge codex/core
python -m pytest -q tests/test_core

git merge codex/config
python -m pytest -q tests/test_schema tests/test_config tests/test_validator
python -m pytest -q tests/test_core

git merge codex/packer
python -m pytest -q tests/test_packer

git merge codex/algo-demo
python -m pytest -q tests/test_algorithms
python -m pytest -q tests/test_core

git merge codex/tests
python -m pytest -q

git merge codex/review
```

每次 merge 后都跑对应测试。

不要一次性合并多个分支后才测试。

------

## 15. 冲突处理原则

### 15.1 Python 源码冲突

看到：

```text
<<<<<<< HEAD
=======
>>>>>>> branch
```

需要手工处理。

处理原则：

```text
1. 删除冲突标记。
2. 保留正确 import。
3. 去掉重复测试函数。
4. 尽量保留双方有价值的测试。
5. 如果测试调用不存在 API，先按当前 API 修改。
```

查找冲突标记：

```powershell
Select-String -Path .\**\*.py -Pattern "<<<<<<<|=======|>>>>>>>" -ErrorAction SilentlyContinue
```

### 15.2 .pyc 冲突

`.pyc` 是 Python 缓存，不应该进 Git。

如果出现 `.pyc` 冲突，直接删除：

```powershell
git rm -r -f --ignore-unmatch -- src/rm_ref/__pycache__
git rm -r -f --ignore-unmatch -- src/rm_ref/core/__pycache__
git rm -r -f --ignore-unmatch -- tests/test_core/__pycache__

Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
```

确认 `.gitignore` 包含：

```gitignore
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.idea/
.vscode/
```

检查仍未解决的冲突：

```powershell
git diff --name-only --diff-filter=U
```

没有输出才说明冲突清完。

------

## 16. 每轮完成后的 checkpoint

当某一阶段稳定后，建议打 tag：

```powershell
git tag checkpoint-core-v0
git tag checkpoint-config-v0
git tag checkpoint-packer-v0
git tag checkpoint-demo-v0
```

查看 tag：

```powershell
git tag
```

如果后面改乱了，可以回看：

```powershell
git log --oneline --decorate
```

------

## 17. 新需求来了怎么处理

新需求分三类。

### 17.1 长期规则

例如：

```text
所有错误必须带 field/value/rule
core 不能依赖 schema
禁止提交 pycache
```

修改：

```text
AGENTS.md
src/AGENTS.md
对应包的 AGENTS.md
```

提交：

```powershell
git add AGENTS.md src/AGENTS.md
git commit -m "docs: update agent rules"
```

然后同步到相关 worktree：

```powershell
cd D:\labs\rm_ai_workspace\rm_ref_core
git merge main
```

### 17.2 本轮任务

例如：

```text
本轮只实现 unsigned word packing
暂不支持 signed field
```

修改或补充：

```text
agents/packer_agent_prompt.md
```

也可以直接在启动 Codex 时补充。

### 17.3 架构决策

例如：

```text
Algorithm 不返回 dict，只写 cell_ctx.output
pipeline 统一 build result
```

修改：

```text
docs/architecture/
```

如果会影响 Agent 行为，再同步修改：

```text
对应 AGENTS.md
对应 agents/*_prompt.md
```

------

## 18. 不推荐的做法

不要：

```text
多个 Agent 进入同一个 worktree
多个 Agent 同时改同一个文件
在 main 上让 Codex 大改
一次性 merge 多个分支后才测试
把一次性任务写进根 AGENTS.md
提交 .pyc / __pycache__ / .idea
失败测试不看原因就继续开新 Agent
```

------

## 19. 当前推荐开发节奏

第一阶段：

```text
Core Agent
Tests Agent
```

目标：

```text
TestcaseConfig
  -> RMContext
  -> PacketContext
  -> CellContext
  -> Algorithm.execute_cell
  -> RunResult
```

第二阶段：

```text
Config Agent
```

目标：

```text
schema dict
  -> UserConfig
  -> ResolvedConfig
  -> Validator
```

第三阶段：

```text
Packer Agent
Algo Demo Agent
```

目标：

```text
ResolvedConfig / schema fields
  -> hardware words

core runner
  -> demo echo algorithm
  -> run result
```

第四阶段：

```text
Tests Agent
Review Agent
```

目标：

```text
补测试
查架构风险
收敛问题
```

------

## 20. 常用命令速查

查看状态：

```powershell
git status
```

查看改了哪些文件：

```powershell
git diff --name-only
git diff --stat
```

查看未解决冲突：

```powershell
git diff --name-only --diff-filter=U
```

查冲突标记：

```powershell
Select-String -Path .\**\*.py -Pattern "<<<<<<<|=======|>>>>>>>" -ErrorAction SilentlyContinue
```

跑测试：

```powershell
python -m pytest -q
```

跑 core 测试：

```powershell
python -m pytest -q tests/test_core
```

清理 pycache：

```powershell
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
```

提交：

```powershell
git add .
git commit -m "message"
```

合并：

```powershell
git merge codex/core
```

查看 worktree：

```powershell
git worktree list
```

创建 worktree：

```powershell
git worktree add ..\rm_ref_core -b codex/core
```

同步 main：

```powershell
git merge main
```