# 第二课：数据加载与处理

## 📌 学习目标
掌握在 Backtrader 中加载和使用各种数据源

---

## 🔑 核心概念

### 数据格式要求
Backtrader 需要标准的 OHLCV 格式数据：

| 列名 | 说明 | 必需 |
|------|------|------|
| datetime | 日期时间 | ✅ |
| open | 开盘价 | ✅ |
| high | 最高价 | ✅ |
| low | 最低价 | ✅ |
| close | 收盘价 | ✅ |
| volume | 成交量 | ✅ |
| openinterest | 持仓量 | ❌ |

---

## 📊 数据源类型

### 1. Pandas DataFrame 加载（推荐）

```python
import pandas as pd

# 读取 CSV 数据
df = pd.read_csv('stock.csv')

# 确保 datetime 是索引（必须步骤）
df['datetime'] = pd.to_datetime(df['datetime'])
df.set_index('datetime', inplace=True)

# 加载到 Backtrader
data = bt.feeds.PandasData(dataname=df)
```

### 2. TuShare 数据（中国股市）

```python
import tushare as ts

# 获取数据
pro = ts.pro_api('your_token')
df = pro.daily(ts_code='000001.SZ', start_date='20230101')

# 转换格式
df['trade_date'] = pd.to_datetime(df['trade_date'])
df.set_index('trade_date', inplace=True)

# 加载
data = bt.feeds.PandasData(dataname=df)
```

### 3. Yahoo Finance 数据

```python
# 需要安装: pip install yfinance
data = bt.feeds.YahooFinanceData(
    dataname='AAPL',
    fromdate=datetime(2020, 1, 1),
    todate=datetime(2023, 12, 31)
)
```

---

## 🛠️ 数据预处理

### 重命名列名

```python
df.rename(columns={
    'trade_date': 'datetime',
    'vol': 'volume'
}, inplace=True)
```

### 处理缺失值

```python
# 删除缺失值
df.dropna(inplace=True)

# 或填充缺失值
df.fillna(method='ffill', inplace=True)
```

### 确保数据类型正确

```python
df['datetime'] = pd.to_datetime(df['datetime'])
df[['open', 'high', 'low', 'close']] = \
    df[['open', 'high', 'low', 'close']].astype(float)
df['volume'] = df['volume'].astype(int)
```

---

## 📁 多数据源

同时交易多个品种：

```python
# 添加多个数据源
data1 = bt.feeds.PandasData(dataname=df1)
data2 = bt.feeds.PandasData(dataname=df2)

cerebro.adddata(data1, name='AAPL')
cerebro.adddata(data2, name='MSFT')

# 在策略中访问
class MyStrategy(bt.Strategy):
    def __init__(self):
        self.data1 = self.datas[0]  # 第一个数据源
        self.data2 = self.datas[1]  # 第二个数据源
```

---

## 📝 本课示例

### 示例 1: CSV 数据加载
```bash
python lessons/02_data/01_csv_data.py
```

### 示例 2: TuShare 数据获取
```bash
python lessons/02_data/02_tushare_data.py
```

### 示例 3: 多数据源
```bash
python lessons/02_data/03_multiple_data.py
```

---

## ❓ 常见问题

**Q: 数据必须是日线吗？**
A: 不是，可以是任何周期：分钟线、小时线、周线、月线等。

**Q: 如何获取实时数据？**
A: 使用支持实时数据的数据源，如 Yahoo Finance 或券商 API。

**Q: 数据索引必须是 datetime 吗？**
A: 使用 PandasData 时，建议将 datetime 设为索引，Backtrader 会自动识别。

---

## 📚 下一步
完成本课后，进入第三课：**技术指标**
