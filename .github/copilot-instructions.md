# Copilot / AI Agent 使用指南（项目专用）

本仓库为基于 Backtrader 的教学与示例代码集合（位于 `lessons/`），主要用于学习策略开发与回测。本文件为 AI 编码代理提供可立即使用的、面向实现的指导要点。

1) 项目大局
- 主要目录：
  - [lessons/01_basics/README.md](lessons/01_basics/README.md) — 教学说明与运行示例。
  - [lessons/01_basics/02_hello_world.py](lessons/01_basics/02_hello_world.py#L1-L300) — 最完整的可运行示例，演示数据生成、策略、回测、绘图。
  - [lessons/01_basics/01_first_strategy.py](lessons/01_basics/01_first_strategy.py#L1-L200) — 简单“买入并持有”示例，展示基础策略结构。
  - `data/` — 运行示例时脚本会写入 `data/sample_data.csv`（见 `02_hello_world.py` 中的 `df.to_csv('data/sample_data.csv')`）。

2) 核心架构与数据流（简明）
- 流程：生成/加载数据 -> 创建 `Cerebro` -> `addstrategy()` -> `adddata()` -> 设置 `broker` -> `addanalyzer()` -> `run()` -> `plot()`。
- 数据格式：CSV/ pandas.DataFrame，必须包含 datetime, open, high, low, close, volume（示例在 `02_hello_world.py` 中生成）。

3) 代码约定与常见模式（请严格遵守）
- 策略类结构：实现 `__init__()`（构建指标/引用数据）、`next()`（每条数据的主逻辑）、可选 `notify_order()` 用于订单回调。
  - 推荐的下单模式（见 `02_hello_world.py`）：
    1. 在 `next()` 中使用 `if self.order: return` 防止重复下单。
    2. 下单时保存 `self.order = self.buy()` / `self.sell()`。
    3. 在 `notify_order()` 中检查 `order.status` 并在完成后将 `self.order = None`。
- 数据索引访问：使用 `self.data.close[0]` 表示当前、`[-1]` 表示前一条数据；示例频繁使用此方式。
- 交易量/手数：示例直接使用 `size=` 指定手数（如 `size=10`、`size=100`）。

4) 运行与调试工作流（可复制的步骤）
- 运行示例（工作目录为仓库根）:

  python lessons/01_basics/02_hello_world.py

- 该脚本会在运行时生成 `data/sample_data.csv`，并在结束时调用 `cerebro.plot()` 绘图（可能需要图形环境）。
- 依赖项（在运行前确认安装）：`backtrader`, `pandas`, `matplotlib`。常用安装命令：`pip install backtrader pandas matplotlib`。

5) 设计/实现边界与约束
- 仓库为教学示例，代码通常将演示逻辑写成独立脚本而非库化函数。如果为生产化改造：把策略类保持为可复用模块，外部负责数据加载与 `Cerebro` 配置。
- 示例中不强制使用网络数据，优先采用脚本内生成或本地 CSV（注意 `01_first_strategy.py` 中对在线数据的降级逻辑）。

6) 对 AI 代理的具体行动建议（可直接执行的变更）
- 修改/添加策略：在 `lessons/` 下添加新脚本，遵循现有模式（`__init__`, `next`, `notify_order`），并在脚本顶部说明所需依赖与运行命令。
- 添加单元或集成示例：提供一个轻量 runner（例如 `scripts/run_example.py`），用于在 CI 或无图形环境下运行回测并保存分析器结果到 JSON/CSV。
- 修复/改进示例：优先在 `02_hello_world.py` 中保留现有打印语与 `df.to_csv` 行为；若改动数据输出，确保向 `data/` 写入并在 README 中同步说明。

7) 注意事项（不要做的事）
- 不要假设额外的配置文件或复杂 CI；当前仓库只有示例脚本与 `lessons/` 目录。
- 不要移除脚本中用于教学的打印或绘图语句，除非你同时提供替代的、机器可读取的输出（例如 JSON 报告）。

如果需要，我可以：
- 基于上述规则为仓库添加 `scripts/run_headless.py`（非图形环境运行并导出分析器结果），或
- 将此文件调整为更详细的 Agent 指令版本（包括检查点和示例变更）。

---
请审阅上述说明并指出需要补充或更准确引用的文件/位置。谢谢！
