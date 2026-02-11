# 第一课：Backtrader 核心概念

## 📌 学习目标
理解 Backtrader 的 7 个核心组件

---

## 🔑 核心组件详解

### 1. Cerebro（引擎）
- **作用**：回测引擎，整个策略的"大脑"
- **职责**：
  - 管理策略
  - 加载数据
  - 执行回测
  - 处理订单
  - 生成结果

```python
cerebro = bt.Cerebro()  # 创建引擎
cerebro.run()           # 运行回测
cerebro.plot()          # 绘制结果
```

---

### 2. Strategy（策略）
- **作用**：定义交易逻辑的地方
- **关键方法**：
  - `__init__()`: 初始化，定义指标
  - `next()`: 核心！每个交易日调用，编写买卖逻辑

```python
class MyStrategy(bt.Strategy):
    def __init__(self):
        self.close = self.datas[0].close  # 引用收盘价

    def next(self):
        if self.close[0] > self.close[-1]:  # 今天涨了
            self.buy()                       # 买入
```

---

### 3. Data Feeds（数据源）
- **作用**：提供价格数据
- **数据格式**：至少需要这些列
  - datetime（日期时间）
  - open（开盘价）
  - high（最高价）
  - low（最低价）
  - close（收盘价）
  - volume（成交量）
  - openinterest（持仓量，可选）

```python
# 从 CSV 加载
data = bt.feeds.CSVGeneralData(dataname='aapl.csv')

# 从 Pandas DataFrame 加载
data = bt.feeds.PandasData(dataname=df)

# 从 Yahoo Finance 加载
data = bt.feeds.YahooFinanceData(daname='AAPL')
```

---

### 4. Indicators（指标）
- **作用**：计算技术指标
- **内置指标**：MA, MACD, RSI, BollingerBands 等

```python
class MyStrategy(bt.Strategy):
    def __init__(self):
        # 创建 20 日均线
        self.sma = bt.indicators.SMA(period=20)
        # 创建 MACD
        self.macd = bt.indicators.MACD()

    def next(self):
        if self.data.close[0] > self.sma[0]:
            self.buy()
```

---

### 5. Broker（券商）
- **作用**：模拟真实券商，处理交易
- **设置内容**：
  - 初始资金
  - 手续费
  - 滑点

```python
cerebro.broker.setcash(10000)           # 设置资金
cerebro.broker.setcommission(0.001)     # 设置手续费 0.1%
```

---

### 6. Observers（观察者）
- **作用**：观察和记录回测过程
- **常用观察者**：
  - DrawDown: 记录回撤
  - Trades: 记录交易
  - BuySell: 在图上标记买卖点

```python
cerebro.addobserver(bt.observers.DrawDown)
cerebro.addobserver(bt.observers.Trades)
```

---

### 7. Analyzers（分析器）
- **作用**：计算策略表现指标
- **常用分析器**：
  - SharpeRatio: 夏普比率
  - Returns: 收益率
  - DrawDown: 最大回撤

```python
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

# 运行后获取结果
strat = cerebro.run()
sharpe = strat[0].analyzers.sharpe.get_analysis()
```

---

## 📝 Backtrader 工作流程

```
1. 创建 Cerebro 引擎
   ↓
2. 添加 Strategy（策略）
   ↓
3. 添加 Data Feeds（数据）
   ↓
4. 设置 Broker 参数（资金、手续费）
   ↓
5. 添加 Analyzers/Observers（可选）
   ↓
6. 运行回测 cerebro.run()
   ↓
7. 查看结果/绘图 cerebro.plot()
```

---

## 🎯 本课练习

### 任务 1：运行 Hello World
```bash
python lessons/01_basics/02_hello_world.py
```

### 任务 2：修改策略
修改 `02_hello_world.py` 中的策略：
- 改变买入条件（价格 < 90）
- 改变卖出条件（价格 > 110）
- 观察结果变化

### 任务 3：理解数据
查看生成的 `data/sample_data.csv`，理解数据格式

---

## ❓ 常见问题

**Q: next() 方法什么时候被调用？**
A: 每个新的交易日（或数据条）都会调用一次。

**Q: self.dataclose[0] 和 self.dataclose[-1] 有什么区别？**
A:
- `[0]` = 当前日
- `[-1]` = 前 1 日
- `[-2]` = 前 2 日
- 以此类推

**Q: position 是什么？**
A: position 表示当前持仓情况：
- `self.position.size == 0`: 没有持仓
- `self.position.size > 0`: 有持仓
- `self.position.size`: 持仓数量

---

## 📚 下一步
完成本课后，进入第二课：**数据加载与处理**
