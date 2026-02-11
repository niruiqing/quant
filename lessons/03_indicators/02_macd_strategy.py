#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backtrader MACD 策略示例

学习要点：
1. MACD 指标的构成（MACD线、信号线、柱状图）
2. MACD 金叉死叉策略
3. MACD 与零轴的关系
4. MACD 柱状图的应用
"""

import backtrader as bt
import pandas as pd
import random
from datetime import datetime


def generate_sample_data():
    """生成模拟数据"""
    start_date = datetime(2023, 1, 1)
    dates = pd.date_range(start_date, periods=200, freq='D')

    # 生成有趋势的价格数据
    price = 100.0
    prices = []
    trend = 0

    for i in range(200):
        if i % 40 == 0:
            trend = random.uniform(-0.8, 0.8)

        change = random.uniform(-2, 2) + trend
        price = max(price + change, 10)
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


# ============= 策略 1: MACD 金叉死叉策略 =============
class MACDStrategy(bt.Strategy):
    """
    MACD 经典策略

    逻辑：
    - MACD 线上穿信号线 → 金叉，买入
    - MACD 线下穿信号线 → 死叉，卖出
    """

    params = (
        ('fast_period', 12),    # 快线周期
        ('slow_period', 26),    # 慢线周期
        ('signal_period', 9),   # 信号线周期
    )

    def __init__(self):
        # 创建 MACD 指标
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.fast_period,
            period_me2=self.params.slow_period,
            period_signal=self.params.signal_period
        )

        # MACD 线
        self.macd_line = self.macd.macd
        # 信号线
        self.signal_line = self.macd.signal
        # 柱状图
        self.histo = self.macd.histo

        # 交叉信号
        self.crossover = bt.indicators.CrossOver(self.macd_line, self.signal_line)

        print(f'\n📊 MACD 参数:')
        print(f'   快线周期: {self.params.fast_period}')
        print(f'   慢线周期: {self.params.slow_period}')
        print(f'   信号线周期: {self.params.signal_period}')

    def notify_order(self, order):
        """订单状态回调"""
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'  ✅ 买入成交: 价格={order.executed.price:.2f}')
            else:
                pnl = (order.executed.price - self.buyprice) * order.executed.size
                print(f'  ✅ 卖出成交: 价格={order.executed.price:.2f}, 盈亏={pnl:.2f}')

    def next(self):
        """每个交易日调用"""
        # 确保有足够的 MACD 数据
        if len(self.macd) < self.params.slow_period + self.params.signal_period:
            return

        # 没有持仓时，只考虑买入
        if not self.position:
            # MACD 金叉
            if self.crossover[0] > 0:
                self.buyprice = self.data.close[0]
                self.order = self.buy(size=10)
                print(f'\n📈 {self.datas[0].datetime.date(0)}: MACD 金叉')
                print(f'   MACD: {self.macd_line[0]:.2f}')
                print(f'   信号: {self.signal_line[0]:.2f}')
                print(f'   柱状图: {self.histo[0]:.2f}')
                print(f'   价格: {self.data.close[0]:.2f}')

        # 有持仓时，只考虑卖出
        else:
            # MACD 死叉
            if self.crossover[0] < 0:
                self.order = self.sell(size=10)
                print(f'\n📉 {self.datas[0].datetime.date(0)}: MACD 死叉')
                print(f'   MACD: {self.macd_line[0]:.2f}')
                print(f'   信号: {self.signal_line[0]:.2f}')
                print(f'   柱状图: {self.histo[0]:.2f}')
                print(f'   价格: {self.data.close[0]:.2f}')


# ============= 策略 2: MACD 零轴策略 =============
class MACDZeroStrategy(bt.Strategy):
    """
    MACD 零轴策略

    逻辑：
    - MACD 线上穿零轴 → 买入
    - MACD 线下穿零轴 → 卖出
    """

    def __init__(self):
        self.macd = bt.indicators.MACD(self.data.close)
        self.macd_line = self.macd.macd

    def next(self):
        if not self.position:
            # MACD 上穿零轴
            if self.macd_line[0] > 0 and self.macd_line[-1] <= 0:
                self.buy(size=10)
                print(f'📈 {self.datas[0].datetime.date(0)}: MACD 上穿零轴，买入')
        else:
            # MACD 下穿零轴
            if self.macd_line[0] < 0 and self.macd_line[-1] >= 0:
                self.sell(size=10)
                print(f'📉 {self.datas[0].datetime.date(0)}: MACD 下穿零轴，卖出')


# ============= 策略 3: MACD 柱状图策略 =============
class MACDHistoStrategy(bt.Strategy):
    """
    MACD 柱状图策略

    逻辑：
    - 柱状图由负转正 → 买入
    - 柱状图由正转负 → 卖出
    """

    def __init__(self):
        self.macd = bt.indicators.MACD(self.data.close)
        self.histo = self.macd.histo

    def next(self):
        if not self.position:
            # 柱状图由负转正
            if self.histo[0] > 0 and self.histo[-1] <= 0:
                self.buy(size=10)
                print(f'📈 {self.datas[0].datetime.date(0)}: 柱状图转正，买入')
        else:
            # 柱状图由正转负
            if self.histo[0] < 0 and self.histo[-1] >= 0:
                self.sell(size=10)
                print(f'📉 {self.datas[0].datetime.date(0)}: 柱状图转负，卖出')


# ============= 策略 4: MACD + 趋势过滤 =============
class MACDTrendStrategy(bt.Strategy):
    """
    MACD + 趋势过滤策略

    逻辑：
    - 只在 MACD > 0（上升趋势）时做多
    - MACD 金叉且 MACD > 0 → 买入
    - MACD 死叉 → 卖出
    """

    def __init__(self):
        self.macd = bt.indicators.MACD(self.data.close)
        self.macd_line = self.macd.macd
        self.signal_line = self.macd.signal
        self.crossover = bt.indicators.CrossOver(self.macd_line, self.signal_line)

    def next(self):
        if not self.position:
            # MACD 金叉 且 MACD 在零轴上方（强势）
            if self.crossover[0] > 0 and self.macd_line[0] > 0:
                self.buy(size=10)
                print(f'📈 {self.datas[0].datetime.date(0)}: 金叉+强势，买入')
        else:
            # 死叉就卖出
            if self.crossover[0] < 0:
                self.sell(size=10)
                print(f'📉 {self.datas[0].datetime.date(0)}: 死叉，卖出')


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

    # 添加策略
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
    print("Backtrader MACD 策略示例")
    print("=" * 60)

    # 运行 MACD 金叉死叉策略
    cerebro = run_strategy(MACDStrategy, "MACD 金叉死叉策略")

    # 可以选择运行其他策略
    # run_strategy(MACDZeroStrategy, "MACD 零轴策略")
    # run_strategy(MACDHistoStrategy, "MACD 柱状图策略")
    # run_strategy(MACDTrendStrategy, "MACD + 趋势过滤策略")

    # 绘制结果
    print("\n📈 正在生成图表...")
    cerebro.plot(style='candlestick', barup='red', bardown='green')
    print("✓ 完成！")


if __name__ == '__main__':
    main()
