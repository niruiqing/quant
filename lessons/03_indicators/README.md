# 第三课：技术指标

## 📌 学习目标
掌握 Backtrader 内置技术指标的使用方法

---

## 🔑 核心概念

### 指标是什么？
技术指标是通过对价格和成交量数据进行数学计算，帮助判断市场趋势和买卖信号的辅助工具。

### 在 Backtrader 中使用指标

```python
class MyStrategy(bt.Strategy):
    def __init__(self):
        # 创建指标
        self.sma = bt.indicators.SMA(period=20)
        self.rsi = bt.indicators.RSI(period=14)

    def next(self):
        # 使用指标值
        if self.data.close[0] > self.sma[0]:
            self.buy()
```

---

## 📊 常用技术指标

### 1. 移动平均线（Moving Average）

**简单移动平均线（SMA）**
```python
sma = bt.indicators.SMA(period=20)  # 20日均线
```

**指数移动平均线（EMA）**
```python
ema = bt.indicators.EMA(period=20)  # 20日指数均线
```

**加权移动平均线（WMA）**
```python
wma = bt.indicators.WMA(period=20)
```

---

### 2. MACD（指数平滑异同移动平均线）

```python
macd = bt.indicators.MACD(period_me1=12,   # 快线周期
                          period_me2=26,   # 慢线周期
                          period_signal=9) # 信号线周期

# 访问各个分量
macd_line = macd.macd        # MACD 线
signal_line = macd.signal    # 信号线
histogram = macd.histo       # 柱状图
```

**经典信号：**
- MACD 上穿信号线 → 买入
- MACD 下穿信号线 → 卖出

---

### 3. RSI（相对强弱指数）

```python
rsi = bt.indicators.RSI(period=14, safediv=True)
```

**经典信号：**
- RSI > 70 → 超买，考虑卖出
- RSI < 30 → 超卖，考虑买入

---

### 4. 布林带（Bollinger Bands）

```python
bb = bt.indicators.BollingerBands(period=20,  # 周期
                                  devfactor=2) # 标准差倍数

# 访问各条线
bb_top = bb.top        # 上轨
bb_mid = bb.mid        # 中轨（就是 SMA）
bb_bot = bb.bot        # 下轨
```

**经典信号：**
- 价格触及上轨 → 可能回调
- 价格触及下轨 → 可能反弹

---

### 5. KDJ（随机指标）

```python
stoch = bt.indicators.Stochastic(period=14,      # K 周期
                                 period_dfast=3, # D 周期
                                 period_dslow=3) # 慢速 D 周期

k_line = stoch.percK   # K 线
d_line = stoch.percD   # D 线
```

**经典信号：**
- K 上穿 D → 买入
- K 下穿 D → 卖出

---

### 6. ATR（平均真实波幅）

```python
atr = bt.indicators.ATR(period=14)
```

**用途：**
- 衡量市场波动性
- 设置止损位
- 动态调整仓位

---

## 🎯 指标组合策略示例

### 双均线策略

```python
class DualMAStrategy(bt.Strategy):
    def __init__(self):
        # 快线
        self.fast_ma = bt.indicators.SMA(period=5)
        # 慢线
        self.slow_ma = bt.indicators.SMA(period=20)

    def next(self):
        # 金叉：快线上穿慢线
        if self.fast_ma[0] > self.slow_ma[0] and \
           self.fast_ma[-1] <= self.slow_ma[-1]:
            self.buy()

        # 死叉：快线下穿慢线
        if self.fast_ma[0] < self.slow_ma[0] and \
           self.fast_ma[-1] >= self.slow_ma[-1]:
            self.sell()
```

### RSI + MACD 组合

```python
class RSIMACDStrategy(bt.Strategy):
    def __init__(self):
        self.rsi = bt.indicators.RSI(period=14)
        self.macd = bt.indicators.MACD()

    def next(self):
        # RSI 超卖 + MACD 金叉
        if self.rsi[0] < 30 and self.macd.macd[0] > self.macd.signal[0]:
            if not self.position:
                self.buy()

        # RSI 超买 + MACD 死叉
        if self.rsi[0] > 70 and self.macd.macd[0] < self.macd.signal[0]:
            if self.position:
                self.sell()
```

---

## 📝 本课示例

### 示例 1: 移动平均线策略
```bash
python lessons/03_indicators/01_ma_strategy.py
```

### 示例 2: MACD 策略
```bash
python lessons/03_indicators/02_macd_strategy.py
```

### 示例 3: RSI 策略
```bash
python lessons/03_indicators/03_rsi_strategy.py
```

### 示例 4: 布林带策略
```bash
python lessons/03_indicators/04_bollinger_strategy.py
```

---

## 💡 使用技巧

### 1. 指标自动绘图
```python
cerebro = bt.Cerebro()
# 指标会自动绘制在图上
```

### 2. 在子图中显示指标
```python
# RSI 通常显示在单独的子图中
rsi = bt.indicators.RSI(period=14)
# subplot=True 将指标显示在独立子图
```

### 3. 指标参考数据
```python
# 使用特定数据的收盘价计算指标
sma = bt.indicators.SMA(self.data.close, period=20)
```

---

## ❓ 常见问题

**Q: 为什么指标前面有 N/A？**
A: 指标需要一定的历史数据才能计算，这叫做"预热期"（warmup period）。

**Q: 如何访问昨天的指标值？**
A: 使用 `self.sma[-1]` 访问前一天的值。

**Q: 可以自定义指标吗？**
A: 可以，继承 `bt.Indicator` 类实现自定义指标。

---

## 📚 下一步
完成本课后，进入第四课：**经典策略实现**
