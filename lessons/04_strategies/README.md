# 第四课：经典策略实现

## 📌 学习目标
掌握量化交易中的经典策略实现

---

## 🎯 策略分类

### 1. 趋势跟踪策略
- 双均线策略
- 通道突破策略
- 动量策略

### 2. 均值回归策略
- 布林带策略
- RSI 均值回归

### 3. 海龟交易法则
- 经典的趋势跟踪系统

---

## 📊 经典策略详解

### 策略 1: 双均线策略

**原理：**
- 快线上穿慢线 → 金叉，买入信号
- 快线下穿慢线 → 死叉，卖出信号

**优点：**
- 简单易懂
- 在趋势市场中表现良好

**缺点：**
- 震荡市场频繁交易
- 滞后性明显

**适用场景：**
- 单边趋势明显的市场

---

### 策略 2: 布林带策略

**原理：**
- 价格触及下轨 → 超卖，买入
- 价格触及上轨 → 超买，卖出

**优点：**
- 自动适应波动率
- 止损止盈位置明确

**缺点：**
- 强势行情中容易被套

**适用场景：**
- 震荡市或均值回归市场

---

### 策略 3: 海龟交易法则

**原理：**
- 价格突破 20 日最高价 → 买入
- 价格跌破 10 日最低价 → 离场

**优点：**
- 著名的经典策略
- 严格执行交易规则

**缺点：**
- 回撤可能较大
- 需要耐心等待信号

**适用场景：**
- 长期趋势跟踪

---

### 策略 4: 动量策略

**原理：**
- 过去 N 天涨幅为正 → 买入
- 过去 N 天涨幅为负 → 卖出

**优点：**
- 捕捉市场动量
- 适合强势股

**缺点：**
- 动量反转时损失大

**适用场景：**
- 趋势明确的个股

---

## 💡 策略优化技巧

### 1. 参数优化
```python
# 使用 Cerebro 的优化功能
cerebro.optstrategy(
    MyStrategy,
    fast_period=range(5, 20, 5),
    slow_period=range(20, 60, 10)
)
```

### 2. 止损止盈
```python
class MyStrategy(bt.Strategy):
    def __init__(self):
        self.stop_loss = 0.05   # 5% 止损
        self.take_profit = 0.15  # 15% 止盈

    def next(self):
        if self.position:
            # 计算盈亏比例
            pnl = (self.data.close[0] - self.buyprice) / self.buyprice

            if pnl < -self.stop_loss:
                self.sell()  # 止损
            elif pnl > self.take_profit:
                self.sell()  # 止盈
```

### 3. 仓位管理
```python
# 根据账户价值动态计算仓位
cash = self.broker.getcash()
value = self.broker.getvalue()
size = int((value * 0.95) / self.data.close[0])  # 95% 仓位
self.buy(size=size)
```

### 4. 过滤器
```python
# 添加额外条件过滤假信号
def next(self):
    # ATR 过滤：波动率过大时不开仓
    if self.atr[0] > self.atr[-1] * 2:
        return

    # 成交量过滤：成交量放大时才交易
    if self.data.volume[0] < self.data.volume[-1] * 1.5:
        return
```

---

## 📝 本课示例

### 示例 1: 双均线策略
```bash
python lessons/04_strategies/01_dual_ma.py
```

### 示例 2: 布林带策略
```bash
python lessons/04_strategies/02_bollinger.py
```

### 示例 3: 海龟交易法则
```bash
python lessons/04_strategies/03_turtle.py
```

### 示例 4: 动量策略
```bash
python lessons/04_strategies/04_momentum.py
```

### 示例 5: 网格交易策略
```bash
python lessons/04_strategies/05_grid.py
```

---

## ⚠️ 风险提示

1. **历史表现不代表未来**
   - 回测结果优秀的策略不一定在实盘中盈利

2. **过拟合风险**
   - 过度优化参数可能导致策略失效

3. **交易成本**
   - 频繁交易的手续费会大幅侵蚀收益

4. **滑点影响**
   - 实盘成交价可能劣于预期

5. **市场变化**
   - 市场结构变化可能使策略失效

---

## 📚 下一步
完成本课后，进入第五课：**回测分析与优化**
