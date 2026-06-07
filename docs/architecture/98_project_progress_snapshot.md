# RM Reference Model 项目进展快照

## 1. 文档目的

本文档用于记录当前 RM Reference Model 多 Agent 工程的阶段性进展。

用途：

1. 新开 ChatGPT 对话时快速恢复上下文。
2. 避免忘记当前工程结构、已完成内容和下一步任务。
3. 作为阶段性 checkpoint 说明。
4. 帮助后续 Agent 理解当前项目状态。

本文档不是架构规范，架构规范仍以 `docs/architecture/` 下其他设计文档和各级 `AGENTS.md` 为准。

------

## 2. 当前项目定位

当前工程是一个重新搭建的 Python Reference Model 框架，用于通信链路 / FPGA / UVM 验证环境。

目标是搭建一套可扩展的 RM 框架：

```text
schema / user config
  -> resolved config
  -> validator
  -> optional packer
  -> core TestcaseConfig / PacketConfig / CellConfig
  -> RMContext / PacketContext / CellContext
  -> Algorithm.execute_cell
  -> result / trace / dump
```

工程要求兼容：

```text
Python 3.6.3
```

因此禁止使用：

```text
dataclasses
typing.Protocol
Literal
TypedDict
list[str]
dict[str, int]
X | Y
match/case
```

------

## 3. 当前工作区结构

主工作区：

```text
D:\labs\rm_ai_workspace\
```

主工程：

```text
D:\labs\rm_ai_workspace\rm_ref_main
```

推荐 worktree：

```text
rm_ref_main\          main 分支，只做集成
rm_ref_core\          codex/core
rm_ref_config\        codex/config
rm_ref_packer\        codex/packer
rm_ref_algo_demo\     codex/algo-demo
rm_ref_tests\         codex/tests
rm_ref_review\        codex/review
rm_ref_uvm_parser\    codex/uvm-parser
```

------

## 4. 当前主工程目录规划

```text
rm_ref_main/
├── AGENTS.md
├── agents/
├── docs/
│   ├── architecture/
│   ├── interface/
│   └── review/
├── doc/
│   └── ref_docs/
│       └── interface/
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
│   ├── fixtures/
│   ├── test_core/
│   ├── test_schema/
│   ├── test_config/
│   ├── test_validator/
│   ├── test_packer/
│   ├── test_algorithms/
│   ├── test_integration/
│   └── test_utils/
├── utils/
└── scripts/
```

------

## 5. 已完成的文档工作

已经补齐多级 `AGENTS.md`，包括：

```text
AGENTS.md
src/AGENTS.md
tests/AGENTS.md
docs/AGENTS.md
src/rm_ref/AGENTS.md
src/rm_ref/core/AGENTS.md
src/rm_ref/schema/AGENTS.md
src/rm_ref/config/AGENTS.md
src/rm_ref/validator/AGENTS.md
src/rm_ref/packer/AGENTS.md
src/rm_ref/algorithms/AGENTS.md
utils/AGENTS.md
scripts/AGENTS.md
doc/ref_docs/interface/AGENTS.md
```

已经补齐 Agent prompt，包括：

```text
agents/README.md
agents/arch_agent_prompt.md
agents/core_agent_prompt.md
agents/config_agent_prompt.md
agents/packer_agent_prompt.md
agents/tests_agent_prompt.md
agents/algo_demo_agent_prompt.md
agents/review_agent_prompt.md
agents/uvm_table_parser_agent_prompt.md
```

已经新增多 Agent 操作流程文档：

```text
docs/architecture/99_multi_agent_workflow.md
```

该文档记录了：

```text
worktree 创建
Agent 启动
Agent 合并
pytest 检查
冲突处理
.pyc 清理
AGENTS.md 修改原则
```

------

## 6. 已完成的实现阶段

### 6.1 Core Agent

Core Agent 已执行。

目标：

```text
TestcaseConfig
  -> RMContext
  -> PacketContext
  -> CellContext
  -> Algorithm.execute_cell
  -> RunResult
```

Core Agent 创建了 core 相关文件和测试。

涉及区域：

```text
src/rm_ref/core/
tests/test_core/
```

### 6.2 Tests Agent

Tests Agent 已执行。

创建或补充了 core 相关 pytest 测试。

涉及区域：

```text
tests/test_core/
```

### 6.3 Core / Tests 合并问题

合并 Core 和 Tests 分支时出现过测试文件冲突。

曾出现 Git 冲突标记：

```text
<<<<<<< HEAD
=======
>>>>>>> codex/tests
```

出现在：

```text
tests/test_core/test_config_context.py
tests/test_core/test_runner.py
```

已手动处理。

同时曾出现 `.pyc` 冲突，需要删除 `__pycache__` 并补充 `.gitignore`。

`.gitignore` 应包含：

```gitignore
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.idea/
.vscode/
```

------

## 7. Config Agent 阶段

Config 分支已经合并。

目标链路：

```text
schema dict
  -> schema object / registry
  -> UserConfig
  -> ResolvedConfig
  -> Validator
```

涉及区域：

```text
src/rm_ref/schema/
src/rm_ref/config/
src/rm_ref/validator/
schema_defs/
tests/test_schema/
tests/test_config/
tests/test_validator/
```

合并后建议确认：

```powershell
python -m pytest -q tests/test_core
python -m pytest -q tests/test_schema tests/test_config tests/test_validator
python -m pytest -q
```

------

## 8. 当前新增需求：UVM table printer 解析工具

当前已有接口参考资料：

```text
doc/ref_docs/interface/demo_interface_table.xlsx
doc/ref_docs/interface/uvm_table_print_demo.txt
```

其中 `uvm_table_print_demo.txt` 是 UVM table printer 的层次化输出样例，结构类似：

```text
packet_param
  header0
    word0
    packet_type
    fpga_link_id
    frame_num
    slot_num
  header1
    word0
    packet_type
    fpga_link_id
    frame_num
    slot_num
  word4
  Payload
```

注意：`header0` 和 `header1` 下有重复字段名，例如：

```text
packet_type
frame_num
slot_num
```

因此 parser 必须保留层次路径，例如：

```text
packet_param.header0.packet_type
packet_param.header1.packet_type
```

不能简单合并成：

```text
packet_type
```

测试样例建议放：

```text
tests/fixtures/uvm_table_print/demo_packet_param_table.txt
```

原始参考文件放：

```text
doc/ref_docs/interface/
```

工具实现位置：

```text
utils/parse_uvm_table_print.py
```

映射文件位置：

```text
schema_defs/uvm_table/demo_packet_param_mapping.py
```

测试位置：

```text
tests/test_utils/test_parse_uvm_table_print.py
```

设计说明位置：

```text
docs/interface/uvm_table_print_parser.md
```

------

## 9. UVM table parser 的目标

目标流程：

```text
uvm_table_printer txt
  -> parse hierarchical parameter paths
  -> convert values
  -> apply mapping
  -> generate Python para_get(parse) file
```

输出格式：

```python
# Auto-generated by utils/parse_uvm_table_print.py

def para_get(parse):
    parse.header0_packet_type = 0
    parse.header0_fpga_link_id = 0
    parse.header0_frame_num = 0
    parse.header0_slot_num = 0
    parse.header1_packet_type = 0
    parse.header1_fpga_link_id = 0
    parse.header1_frame_num = 0
    parse.header1_slot_num = 0
```

第一版应支持：

```text
1. 根据缩进解析层次路径。
2. 支持 SystemVerilog 十六进制值，例如 'h00、'h00000000。
3. 支持 decimal / hex / binary / negative int。
4. 支持 mapping.py。
5. 支持 KEEP_UNMAPPED。
6. 不允许重复最终 RM 参数名静默覆盖。
7. 生成 para_get(parse) Python 文件。
8. Python 3.6 兼容。
```

第一版不做：

```text
不解析 Excel
不接入 RM core
不生成 ResolvedConfig
不做业务合法性校验
不实现 SRS/PUSCH/PRACH
```

------

## 10. 下一步推荐动作

当前下一步建议优先做：

```text
UVM Table Parser Agent
```

而不是继续 Packer / Algo Demo。

原因：

```text
现在已经有真实 uvm_table_printer demo 文本。
解析工具需求清楚。
它不会污染 core/config/packer。
可以独立开发和测试。
```

推荐 worktree：

```powershell
cd D:\labs\rm_ai_workspace\rm_ref_main
git worktree add ..\rm_ref_uvm_parser -b codex/uvm-parser
```

启动：

```powershell
cd D:\labs\rm_ai_workspace\rm_ref_uvm_parser

$env:HTTP_PROXY="http://127.0.0.1:7897"
$env:HTTPS_PROXY="http://127.0.0.1:7897"
$env:ALL_PROXY="http://127.0.0.1:7897"

codex -c features.apps=false
```

发送给 Codex：

```text
Read AGENTS.md.
Read doc/ref_docs/interface/AGENTS.md.
Read utils/AGENTS.md.
Read tests/AGENTS.md.
Read agents/uvm_table_parser_agent_prompt.md.
Read docs/interface/uvm_table_print_parser.md.

You are the UVM Table Parser Agent.

Implement the uvm_table_printer hierarchical parser.

Use these reference files:
- doc/ref_docs/interface/demo_interface_table.xlsx
- doc/ref_docs/interface/uvm_table_print_demo.txt
- tests/fixtures/uvm_table_print/demo_packet_param_table.txt

Work only in:
- utils/
- schema_defs/uvm_table/
- tests/test_utils/
- tests/fixtures/uvm_table_print/
- docs/interface/

Do not modify:
- src/rm_ref/core/
- src/rm_ref/config/
- src/rm_ref/validator/
- src/rm_ref/packer/
- src/rm_ref/algorithms/

Required behavior:
1. Parse hierarchical uvm_table_printer text using indentation.
2. Preserve full paths such as packet_param.header0.packet_type.
3. Convert SystemVerilog hex values like 'h00 to integers.
4. Apply mapping from schema_defs/uvm_table/demo_packet_param_mapping.py.
5. Generate para_get(parse) Python source.
6. Add pytest coverage under tests/test_utils.
7. Add or update docs/interface/uvm_table_print_parser.md.

Run:
python -m pytest -q tests/test_utils
python utils/parse_uvm_table_print.py --help

Do not commit automatically.
Stop after reporting files changed, tests run, failures, and limitations.
```

------

## 11. 给新 ChatGPT 对话的启动提示

如果新开 ChatGPT 对话，可以粘贴这段：

```text
我正在做一个 Python 3.6.3 兼容的 RM Reference Model 多 Agent 工程，路径是 D:\labs\rm_ai_workspace\rm_ref_main。

请先阅读我项目中的：
- docs/architecture/98_project_progress_snapshot.md
- docs/architecture/99_multi_agent_workflow.md
- AGENTS.md
- agents/README.md

当前已经完成：
1. 多级 AGENTS.md 和 agents/*_prompt.md。
2. Core Agent 和 Tests Agent 初步完成并合并。
3. Config Agent 已合并，包含 schema/config/validator 初步链路。
4. 当前正在准备 UVM table printer 解析工具。
5. 原始资料在 doc/ref_docs/interface/。
6. UVM table printer demo 是层次化输出，parser 必须保留路径，例如 packet_param.header0.packet_type。

请基于这些文档继续指导我下一步，不要重新设计整套流程。
```

------

## 12. 给 Codex Agent 的通用启动提示

```text
Read AGENTS.md.
Read agents/README.md.
Read docs/architecture/98_project_progress_snapshot.md.
Read docs/architecture/99_multi_agent_workflow.md.
Then read your role-specific prompt under agents/.

Follow allowed file boundaries.
Do not commit automatically.
Run the focused tests specified in your prompt.
Stop after reporting files changed, tests run, failures, and known limitations.
```

------

## 13. 当前注意事项

1. 不要让多个 Agent 进入同一个 worktree。
2. 不要在 `rm_ref_main` 上让 Codex 大改。
3. 每个 Agent 完成后先人工看：

```powershell
git status
git diff --name-only
git diff --stat
```

1. 没有越界再提交。
2. 合并进 main 后立刻跑对应 pytest。
3. `.pyc` / `__pycache__` / `.idea` 不应进入 Git。
4. UVM parser 是 utility，不要改 core。
5. Excel 第一版只作为参考，不直接解析。