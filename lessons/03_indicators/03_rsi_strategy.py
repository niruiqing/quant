#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backtrader RSI 策略示例

学习要点：
1. RSI 指标的使用
2. 超买超卖策略
3. RSI 均值回归策略
4. RSI 与价格背离
"""

import backtrader as bt
import pandas as pd
import random
from datetime import datetime


def generate_sample_data():
    """生成模拟数据（带震荡特征）"""
    start_date = datetime(2023, 1, 1)
    dates = pd.date_range(start_date, periods=200, freq='D')

    # 生成震荡的价格数据
    price = 100.0
    prices = []

    for i in range(200):
        # 生成均值回归特征
        deviation = price - 100
        mean_reversion = -deviation * 0.1  # 均值回归力量

        change = random.uniform(-3, 3) + mean_reversion
        price = max(price + change, 20)
        prices.append(price)

    df = pd.DataFrame({
        'datetime': dates,
        'open': [p * random.uniform(0.98, 1.02) for p in prices],
        'high': [p * random.uniform(1.0, 1.05) for p in prices],
        'low': [p * random.uniform(0.95, 1.0) for p in prices],
        'close': prices,
        'volume': [random.randint(1000, 10000) for _ in range(200)],
        'openinterest': [0] * 200
    })

    return df


# ============= 策略 1: RSI 超买超卖策略 =============
class RSIStrategy(bt.Strategy):
    """
    RSI 经典策略

    逻辑：
    - RSI < 30（超卖）→ 买入
    - RSI > 70（超买）→ 卖出
    """

    params = (
        ('rsi_period', 14),      # RSI 周期
        ('oversold', 30),        # 超卖阈值
        ('overbought', 70),      # 超买阈值
    )

    def __init__(self):
        # 创建 RSI 指标
        self.rsi = bt.indicators.RSI(
            self.data.close,
            period=self.params.rsi_period,
            safediv=True  # 避免除零错误
        )

        self.order = None
        self.buyprice = None

        print(f'\n📊 RSI 策略参数:')
        print(f'   RSI 周期: {self.params.rsi_period}')
        print(f'   超卖阈值: {self.params.oversold}')
        print(f'   超买阈值: {self.params.overbought}')

    def notify_order(self, order):
        """订单状态回调"""
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buyprice = order.executed.price
                print(f'  ✅ 买入: 价格={order.executed.price:.2f}, RSI={self.rsi[0]:.1f}')
            else:
                pnl = (order.executed.price - self.buyprice) * order.executed.size
                print(f'  ✅ 卖出: 价格={order.executed.price:.2f}, RSI={self.rsi[0]:.1f}, 盈亏={pnl:.2f}')

        self.order = None

    def next(self):
        """每个交易日调用"""
        if self.order:
            return

        # 确保有足够的 RSI 数据
        if len(self.rsi) < self.params.rsi_period + 1:
            return

        # 没有持仓
        if not self.position:
            # RSI 超卖
            if self.rsi[0] < self.params.oversold:
                self.order = self.buy(size=10)
                print(f'\n📈 {self.datas[0].datetime.date(0)}: RSI 超卖信号')
                print(f'   RSI: {self.rsi[0]:.1f}')
                print(f'   价格: {self.data.close[0]:.2f}')

        # 有持仓
        else:
            # RSI 超买
            if self.rsi[0] > self.params.overbought:
                self.order = self.sell(size=10)
                print(f'\n📉 {self.datas[0].datetime.date(0)}: RSI 超买信号')
                print(f'   RSI: {self.rsi[0]:.1f}')
                print(f'   价格: {self.data.close[0]:.2f}')


# ============= 策略 2: RSI 均值回归策略 =============
class RSIMeanReversion(bt.Strategy):
    """
    RSI 均值回归策略

    逻辑：
    - RSI 偏离 50 较多时，反向交易
    - RSI < 40 → 买入
    - RSI > 60 → 卖出
    """

    params = (
        ('lower_bound', 40),
        ('upper_bound', 60),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(period=14, safediv=True)

    def next(self):
        if not self.position:
            if self.rsi[0] < self.params.lower_bound:
                self.buy(size=10)
                print(f'📈 {self.datas[0].datetime.date(0)}: RSI {self.rsi[0]:.1f} < {self.params.lower_bound}, 买入')
        else:
            if self.rsi[0] > self.params.upper_bound:
                self.sell(size=10)
                print(f'📉 {self.datas[0].datetime.date(0)}: RSI {self.rsi[0]:.1f} > {self.params.upper_bound}, 卖出')


# ============= 策略 3: RSI + 趋势过滤 =============
class RSITrendStrategy(bt.Strategy):
    """
    RSI + 趋势过滤策略

    逻辑：
    - 只在上升趋势中做多
    - RSI < 30 且价格 > MA200 → 买入
    - RSI > 70 → 卖出
    """

    def __init__(self):
        self.rsi = bt.indicators.RSI(period=14, safediv=True)
        self.sma200 = bt.indicators.SMA(period=200)

    def next(self):
        if not self.position:
            # RSI 超卖 且 上升趋势
            if self.rsi[0] < 30 and self.data.close[0] > self.sma200[0]:
                self.buy(size=10)
                print(f'📈 {self.datas[0].datetime.date(0)}: RSI超卖+上升趋势，买入')
        else:
            if self.rsi[0] > 70:
                self.sell(size=10)
                print(f'📉 {self.datas[0].datetime.date(0)}: RSI超买，卖出')


# ============= 策略 4: RSI 双线策略 =============
class RSIDivergence(bt.Strategy):
    """
    RSI 双线策略

    逻辑：
    - RSI 快线与慢线交叉
    - 快线上穿慢线 → 买入
    - 快线下穿慢线 → 卖出
    """

    def __init__(self):
        self.rsi_fast = bt.indicators.RSI(period=7, safediv=True)
        self.rsi_slow = bt.indicators.RSI(period=21, safediv=True)
        self.crossover = bt.indicators.CrossOver(self.rsi_fast, self.rsi_slow)

    def next(self):
        if not self.position:
            if self.crossover[0] > 0:
                self.buy(size=10)
                print(f'📈 {self.datas[0].datetime.date(0)}: RSI快线上穿慢线，买入')
        else:
            if self.crossover[0] < 0:
                self.sell(size=10)
                print(f'📉 {self.datas[0].datetime.date(0)}: RSI快线下穿慢线，卖出')


def run_strategy(strategy_class, strategy_name):
    """运行指定策略"""
    print("\n" + "=" * 60)
    print(f"策略: {strategy_name}")
    print("=" * 60)

    # 生成数据
    df = generate_sample_data()
    df_indexed = df.set_index('datetime')

    # 创建 Cerebro
    cerebro = bt.Cerebro()
    cerebro.addstrategy(strategy_class)

    # 加载数据
    data = bt.feeds.PandasData(dataname=df_indexed)
    cerebro.adddata(data)

    # 设置资金和手续费
    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.001)

    # 添加观察者和分析器
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.DrawDown)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

    # 运行回测
    print(f"\n💰 初始资金: {cerebro.broker.getvalue():.2f}")
    print("-" * 60)

    strat = cerebro.run()
    final_value = cerebro.broker.getvalue()

    print("-" * 60)
    print(f"💰 最终资金: {final_value:.2f}")
    print(f"📊 收益率: {(final_value/10000 - 1)*100:.2f}%")

    # 打印分析结果
    sharpe = strat[0].analyzers.sharpe.get_analysis()
    returns = strat[0].analyzers.returns.get_analysis()

    if 'sharperatio' in sharpe and sharpe['sharperatio'] is not None:
        print(f"📈 夏普比率: {sharpe['sharperatio']:.2f}")

    if 'rtot' in returns:
        print(f"📊 累计收益: {returns['rtot']:.2%}")

    return cerebro


def main():
    """主函数"""
    print("=" * 60)
    print("Backtrader RSI 策略示例")
    print("=" * 60)

    # 运行 RSI 超买超卖策略
    cerebro = run_strategy(RSIStrategy, "RSI 超买超卖策略")

    # 可以选择运行其他策略
    # run_strategy(RSIMeanReversion, "RSI 均值回归策略")
    # run_strategy(RSITrendStrategy, "RSI + 趋势过滤策略")
    # run_strategy(RSIDivergence, "RSI 双线策略")

    # 绘制结果
    print("\n📈 正在生成图表...")
    cerebro.plot(style='candlestick', barup='red', bardown='green')
    print("✓ 完成！")


if __name__ == '__main__':
    main()
