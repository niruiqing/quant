# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供在此仓库中工作的指导。

## 项目概述

这是一个 **Backtrader 学习项目**，用于研究量化交易策略。仓库采用渐进式教程结构，从基础概念逐步进阶到复杂策略。

**语言**: 所有交流和文档应使用简体中文。

**作者**: niruiqing

## 依赖安装

运行示例前请先安装必需的包：

```bash
pip install backtrader pandas matplotlib
pip install tushare  # 可选，用于获取中国股市数据
```

## 运行示例

每课都包含可执行的 Python 脚本。运行课程示例：

```bash
# 从项目根目录运行
python lessons\01_basics\02_hello_world.py
python lessons/04_strategies/01_dual_ma.py
```

Hello World 示例（`lessons/01_basics/02_hello_world.py`）是完全自包含的，会生成自己的模拟数据，是最佳起点。

## 目录结构

```
D:\quant\
├── lessons/              # 学习课程目录
│   ├── 01_basics/        # 第一课：核心概念（Cerebro, Strategy, Data等）
│   ├── 02_data/          # 第二课：数据加载与处理
│   ├── 03_indicators/    # 第三课：技术指标
│   ├── 04_strategies/    # 第四课：经典策略实现
│   └── 05_analysis/      # 第五课：回测分析与优化
├── data/                 # 数据文件存放目录（运行时生成）
└── logs/                 # 运行日志和回测结果
```

## Backtrader 架构

### 核心组件流程

```
Cerebro (引擎)
    ↓
├─ Strategy (交易逻辑)
│   ├─ __init__(): 初始化指标
│   ├─ next(): 每个交易日调用，编写买卖逻辑
│   └─ notify_order(): 订单状态回调
├─ Data Feeds (价格数据)
├─ Broker (模拟券商)
├─ Indicators (技术指标)
├─ Observers (观察回测过程)
└─ Analyzers (计算策略表现)
```

### 策略类模式

所有策略继承自 `bt.Strategy` 并实现：

- `__init__()`: 定义指标和引用
- `next()`: 核心交易逻辑（每根 K 线调用）
- `notify_order()`: 处理订单状态变化
- `notify_trade()`: 处理交易完成

示例：
```python
class MyStrategy(bt.Strategy):
    def __init__(self):
        self.sma = bt.indicators.SMA(period=20)
        self.order = None  # 跟踪待处理订单

    def next(self):
        if self.order:  # 防止重复下单
            return
        if self.data.close[0] > self.sma[0]:
            self.order = self.buy()

    def notify_order(self, order):
        if order.status in [order.Completed]:
            self.order = None  # 清除订单引用
```

### 数据索引

Backtrader 使用数组式索引：
- `[0]` = 当前 K 线（今天）
- `[-1]` = 前 1 根 K 线（昨天）
- `[-2]` = 前 2 根 K 线
- 以此类推

## 数据格式要求

Backtrader 需要 OHLCV 数据，包含以下列：
- `datetime` - 日期时间
- `open` - 开盘价
- `high` - 最高价
- `low` - 最低价
- `close` - 收盘价
- `volume` - 成交量
- `openinterest` - 持仓量（可选）

数据加载示例：
```python
# 从 Pandas DataFrame（本项目最常用）
df = pd.DataFrame({
    'datetime': dates,
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...],
    'openinterest': [0...]
})
df_indexed = df.set_index('datetime')  # 必须设置：datetime 作为索引
data = bt.feeds.PandasData(dataname=df_indexed)

# 从 CSV 文件
data = bt.feeds.CSVGeneralData(dataname='data/sample_data.csv')
```

**重要提示**：使用 PandasData 时，务必将 datetime 设置为索引后再传入。

## 常见代码模式

### 订单管理（推荐模式）

使用此模式防止重复下单：

```python
class MyStrategy(bt.Strategy):
    def __init__(self):
        self.order = None

    def next(self):
        # 检查是否有待处理订单
        if self.order:
            return

        # 你的交易逻辑
        if not self.position:
            self.order = self.buy(size=100)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            # 处理完成
            pass

        # 清除订单引用
        self.order = None
```

### 策略参数

使用 `params` 元组使策略可配置：

```python
class MyStrategy(bt.Strategy):
    params = (
        ('fast_period', 10),
        ('slow_period', 30),
        ('position_size', 100),
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(period=self.params.fast_period)
```

### 交叉信号模式

使用 `CrossOver` 指标检测信号：

```python
def __init__(self):
    self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

def next(self):
    if self.crossover[0] > 0:  # 金叉（快线上穿慢线）
        self.buy()
    elif self.crossover[0] < 0:  # 死叉（快线下穿慢线）
        self.sell()
```

## 教学理念

帮助用户学习 Backtrader 时：

1. **循序渐进**：从简单概念开始，逐步增加复杂度
2. **动手实践**：每个概念都应有可运行代码
3. **解释原理**：不仅说明如何写代码，还要解释 Backtrader 为什么这样工作
4. **鼓励实验**：建议修改参数观察效果变化

## 课程创建模式

创建新课程时，遵循以下结构：

1. **README.md** - 理论说明和代码示例
2. **示例脚本** - 可运行的演示，带中文注释
3. **练习任务** - 供用户尝试的具体练习
4. **问答部分** - 预见常见问题

## 代码风格

- 使用 UTF-8 编码，适当添加中文注释
- 策略类使用中文文档字符串
- 打印语句使用 emoji 提高可读性（📈, 📉, 💰 等）
- 将数据生成函数与策略类分离，便于复用
- 每个脚本应自包含（生成自己的测试数据）
- 下单时使用 `size=` 参数指定仓位大小

## 重要约定

1. **使用 PandasData 时必须设置 datetime 为索引**
2. **在 `next()` 中存储订单引用**，防止重复下单
3. **在 `notify_order()` 中清除订单**，在完成后
4. **在脚本内生成示例数据**，而非依赖外部文件
5. **将生成的数据保存到 `data/`** 目录以便复用（如 `02_hello_world.py`）
