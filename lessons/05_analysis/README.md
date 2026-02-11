# 第五课：回测分析与优化

## 📌 学习目标
掌握如何分析回测结果和优化策略参数

---

## 🔑 核心概念

### 为什么要分析回测结果？

回测不仅看最终收益，更重要的是评估：
- 风险水平（回撤、波动率）
- 收益稳定性（夏普比率、卡尔玛比率）
- 交易质量（胜率、盈亏比）

---

## 📊 关键性能指标

### 1. 收益指标

**总收益率**
```python
returns = cerebro.run()[0].analyzers.returns.get_analysis()
total_return = returns['rtot']  # 总收益率
```

**年化收益率**
```python
# 计算 CAGR（复合年增长率）
initial_value = 10000
final_value = 15000
years = 2
cagr = (final_value / initial_value) ** (1/years) - 1
```

---

### 2. 风险指标

**最大回撤（Max Drawdown）**
```python
drawdown = cerebro.run()[0].analyzers.drawdown.get_analysis()
max_dd = drawdown['max']['drawdown']  # 最大回撤百分比
```

**回撤持续时间**
```python
max_dd_duration = drawdown['max']['len']  # 最大回撤持续天数
```

---

### 3. 风险调整收益指标

**夏普比率（Sharpe Ratio）**
```python
sharpe = cerebro.run()[0].analyzers.sharpe.get_analysis()
sharpe_ratio = sharpe['sharperatio']
```

**解读：**
- Sharpe < 1：策略表现不佳
- Sharpe 1-2：策略表现良好
- Sharpe > 2：策略表现优秀
- Sharpe > 3：策略表现极佳

**卡尔玛比率（Calmar Ratio）**
```python
calmar = 年化收益率 / 最大回撤
```
- 衡量单位回撤带来的收益
- 值越大越好

---

### 4. 交易指标

**胜率（Win Rate）**
```python
trades = cerebro.run()[0].analyzers.trades.get_analysis()
win_rate = trades['won']['total'] / trades['total']['total']
```

**盈亏比（Profit/Loss Ratio）**
```python
avg_win = trades['won']['pnl']['average']
avg_loss = trades['lost']['pnl']['average']
profit_loss_ratio = avg_win / abs(avg_loss)
```

**平均持仓天数**
```python
avg_hold = trades['total']['len']['average']
```

---

## 🛠️ 参数优化

### 基础参数优化

```python
# 定义参数范围
cerebro.optstrategy(
    MyStrategy,
    fast_period=range(5, 20, 5),    # 5, 10, 15
    slow_period=range(20, 60, 10),  # 20, 30, 40, 50
)

# 运行优化
results = cerebro.run()

# 找出最优参数组合
best_result = max(results, key=lambda x: x[0].analyzers.returns.get_analysis()['rtot'])
```

### 避免过拟合

**1. 样本外测试**
- 训练集：70% 数据用于优化
- 测试集：30% 数据用于验证

**2. 参数数量限制**
- 不要优化太多参数
- 通常 2-3 个参数为宜

**3. 简化原则**
- 简单策略往往更稳定
- 避免过度复杂的规则

---

## 📈 回测报告解读

### 理想的回测结果特征

✅ **好的特征：**
- 曲线平滑上升（没有大起大落）
- 最大回撤 < 20%
- 夏普比率 > 1.5
- 胜率稳定
- 交易次数适中（不过度交易）

❌ **不好的特征：**
- 收益曲线急剧上升后快速下跌
- 最大回撤 > 50%
- 交易次数过多（手续费侵蚀收益）
- 参数过度优化（拟合历史）

---

## 📝 分析器使用

### 完整分析器示例

```python
class MyStrategy(bt.Strategy):
    pass

cerebro = bt.Cerebro()
cerebro.addstrategy(MyStrategy)

# 添加多个分析器
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
cerebro.addanalyzer(bt.analyzers.Transactions, _name='transactions')

# 运行回测
strat = cerebro.run()

# 获取分析结果
sharpe = strat[0].analyzers.sharpe.get_analysis()
returns = strat[0].analyzers.returns.get_analysis()
drawdown = strat[0].analyzers.drawdown.get_analysis()
trades = strat[0].analyzers.trades.get_analysis()
```

---

## 🎯 优化流程

### 步骤 1：建立基准
先运行基础策略，了解初始表现

### 步骤 2：单参数优化
每次只优化一个参数，观察影响

### 步骤 3：多参数优化
在单参数优化的基础上，进行多参数组合

### 步骤 4：样本外验证
用未参与优化的数据测试

### 步骤 5：实盘前测试
- 模拟盘测试
- 小资金实盘
- 逐步扩大规模

---

## 📝 本课示例

### 示例 1: 回测分析
```bash
python lessons/05_analysis/01_full_analysis.py
```

### 示例 2: 参数优化
```bash
python lessons/05_analysis/02_parameter_optimization.py
```

### 示例 3: 多策略对比
```bash
python lessons/05_analysis/03_strategy_comparison.py
```

---

## ❓ 常见问题

**Q: 回测收益率多少算好？**
A: 没有标准答案，但通常：
- 年化 15-30%：良好
- 年化 > 50%：需警惕过拟合

**Q: 最大回撤多少可以接受？**
A: 取决于你的风险承受能力：
- 保守投资者：< 10%
- 激进投资者：< 30%

**Q: 如何判断策略是否过拟合？**
A: 观察以下信号：
- 参数极其敏感（微小变化导致巨大差异）
- 交易规则过于复杂
- 样本外表现大幅下降

---

## 📚 学习总结

完成这五课后，你应该掌握了：

1. ✅ Backtrader 核心概念（Cerebro, Strategy, Data）
2. ✅ 数据加载与处理
3. ✅ 技术指标使用
4. ✅ 经典策略实现
5. ✅ 回测分析与优化

**下一步建议：**
- 尝试实现自己的策略想法
- 学习风险管理
- 研究实盘交易细节

**记住：**
- 回测不保证实盘盈利
- 风险管理永远第一
- 保持策略简单有效

---

## 🎓 恭喜完成课程！
继续探索量化交易的精彩世界！
