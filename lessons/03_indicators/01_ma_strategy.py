#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backtrader 移动平均线策略示例

学习要点：
1. SMA（简单移动平均线）使用
2. EMA（指数移动平均线）使用
3. 双均线金叉死叉策略
4. 指标的可视化
"""

import backtrader_next as bt
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
    trend = 0  # 趋势方向

    for i in range(200):
        # 随机趋势变化
        if i % 30 == 0:
            trend = random.uniform(-0.5, 0.5)

        change = random.uniform(-1.5, 1.5) + trend
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


# ============= 策略 1: 双均线策略 =============
class DualMAStrategy(bt.Strategy):
    """
    双均线策略

    逻辑：
    - 快线上穿慢线（金叉）→ 买入
    - 快线下穿慢线（死叉）→ 卖出
    """

    params = (
        ('fast_period', 10),   # 快线周期
        ('slow_period', 30),   # 慢线周期
    )

    def __init__(self):
        """初始化指标"""
        # 订单追踪
        self.order = None

        # 快线
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.params.fast_period)
        # 慢线
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.params.slow_period)

        # 交叉信号（1: 金叉, -1: 死叉）
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

        print(f'\n📊 策略参数:')
        print(f'   快线周期: {self.params.fast_period}')
        print(f'   慢线周期: {self.params.slow_period}')

    def notify_order(self, order):
        """订单状态回调"""
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'✅ 买入成交: 价格={order.executed.price:.2f}, ' +
                      f'数量={order.executed.size:.0f}')
            else:
                print(f'✅ 卖出成交: 价格={order.executed.price:.2f}, ' +
                      f'数量={order.executed.size:.0f}')

    def next(self):
        """每个交易日调用"""
        # 如果有待处理的订单，等待
        if self.order:
            return

        # 没有持仓时，只考虑买入
        if not self.position:
            # 金叉：快线上穿慢线
            if self.crossover[0] > 0:
                self.order = self.buy(size=10)
                print(f'\n📈 {self.datas[0].datetime.date(0)}: 金叉信号')
                print(f'   快线: {self.fast_ma[0]:.2f}')
                print(f'   慢线: {self.slow_ma[0]:.2f}')
                print(f'   收盘价: {self.data.close[0]:.2f}')

        # 有持仓时，只考虑卖出
        else:
            # 死叉：快线下穿慢线
            if self.crossover[0] < 0:
                self.order = self.sell(size=10)
                print(f'\n📉 {self.datas[0].datetime.date(0)}: 死叉信号')
                print(f'   快线: {self.fast_ma[0]:.2f}')
                print(f'   慢线: {self.slow_ma[0]:.2f}')
                print(f'   收盘价: {self.data.close[0]:.2f}')


# ============= 策略 2: 三均线策略 =============
class TripleMAStrategy(bt.Strategy):
    """
    三均线策略（多空确认）

    逻辑：
    - 短期 > 中期 > 长期 → 强势，买入
    - 短期 < 中期 < 长期 → 弱势，卖出
    """

    params = (
        ('short', 5),
        ('medium', 20),
        ('long', 60),
    )

    def __init__(self):
        self.ma_short = bt.indicators.SMA(period=self.params.short)
        self.ma_medium = bt.indicators.SMA(period=self.params.medium)
        self.ma_long = bt.indicators.SMA(period=self.params.long)

    def next(self):
        if not self.position:
            # 多头排列：短 > 中 > 长
            if (self.ma_short[0] > self.ma_medium[0] and
                self.ma_medium[0] > self.ma_long[0]):
                if not self.order:  # 确保没有挂单
                    self.order = self.buy(size=10)
                    print(f'📈 {self.datas[0].datetime.date(0)}: 多头排列，买入')
        else:
            # 空头排列：短 < 中 < 长
            if (self.ma_short[0] < self.ma_medium[0] and
                self.ma_medium[0] < self.ma_long[0]):
                if not self.order:
                    self.order = self.sell(size=10)
                    print(f'📉 {self.datas[0].datetime.date(0)}: 空头排列，卖出')


# ============= 策略 3: 价格与均线策略 =============
class PriceMAStrategy(bt.Strategy):
    """
    价格与均线策略

    逻辑：
    - 价格突破均线 → 买入
    - 价格跌破均线 → 卖出
    """

    params = (
        ('ma_period', 20),
    )

    def __init__(self):
        self.sma = bt.indicators.SMA(period=self.params.ma_period)

    def next(self):
        if not self.position:
            # 价格上穿均线
            if self.data.close[0] > self.sma[0] and self.data.close[-1] <= self.sma[-1]:
                self.buy(size=10)
                print(f'📈 {self.datas[0].datetime.date(0)}: 价格突破均线，买入')
        else:
            # 价格下穿均线
            if self.data.close[0] < self.sma[0] and self.data.close[-1] >= self.sma[-1]:
                self.sell(size=10)
                print(f'📉 {self.datas[0].datetime.date(0)}: 价格跌破均线，卖出')


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
    data = bt.feeds.PandasData(dataframe=df_indexed)
    cerebro.adddata(data)

    # 设置资金和手续费
    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.001)

    # 添加观察者
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.DrawDown)

    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

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
    drawdown = strat[0].analyzers.drawdown.get_analysis()

    if 'sharperatio' in sharpe and sharpe['sharperatio'] is not None:
        print(f"📈 夏普比率: {sharpe['sharperatio']:.2f}")

    if 'rtot' in returns:
        print(f"📊 累计收益: {returns['rtot']:.2%}")

    if 'max' in drawdown:
        print(f"📉 最大回撤: {drawdown['max']['drawdown']:.2%}")

    return cerebro


def main():
    """主函数"""
    print("=" * 60)
    print("Backtrader 移动平均线策略示例")
    print("=" * 60)

    # 运行双均线策略
    cerebro1 = run_strategy(PriceMAStrategy, "价格与均线策略")
    # 可以选择运行其他策略
    # run_strategy(DualMAStrategy, "双均线策略")
    # run_strategy(TripleMAStrategy, "三均线策略")
    # run_strategy(PriceMAStrategy, "价格与均线策略")

    # 绘制结果
    print("\n📈 正在生成图表...")
    cerebro1.plot(style='candlestick', barup='red', bardown='green')
    print("✓ 完成！")

if __name__ == '__main__':
    main()
