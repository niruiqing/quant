#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
经典策略 4：动量策略 (Momentum Strategy)

动量效应是金融市场中最著名的异象之一：
"过去表现好的资产，在未来的一段时间内倾向于继续表现良好"

策略原理：
- 计算过去 N 天的收益率
- 收益率为正 → 买入（持有强势资产）
- 收益率为负 → 卖出（规避弱势资产）

本示例实现几种动量策略变体
"""

import backtrader as bt
import pandas as pd
import random
from datetime import datetime


def generate_sample_data(days=400):
    """生成模拟数据（带动量特征）"""
    start_date = datetime(2022, 1, 1)
    dates = pd.date_range(start_date, periods=days, freq='D')

    price = 100.0
    prices = []
    trend = 0
    trend_duration = 0

    for i in range(days):
        # 每 60 天切换趋势
        if trend_duration > 60:
            trend = random.uniform(-0.5, 0.5)
            trend_duration = 0

        trend_duration += 1
        # 添加动量特征（趋势持续）
        momentum = trend * 0.3
        change = random.uniform(-1.5, 1.5) + momentum
        price = max(price + change, 10)
        prices.append(price)

    df = pd.DataFrame({
        'datetime': dates,
        'open': [p * random.uniform(0.98, 1.02) for p in prices],
        'high': [p * random.uniform(1.0, 1.05) for p in prices],
        'low': [p * random.uniform(0.95, 1.0) for p in prices],
        'close': prices,
        'volume': [random.randint(1000, 10000) for _ in range(days)],
        'openinterest': [0] * days
    })

    return df


# ============= 策略 1: 简单动量策略 =============
class MomentumStrategy(bt.Strategy):
    """
    简单动量策略

    逻辑：
    - 计算过去 N 天的收益率
    - 收益率 > 阈值 → 买入
    - 收益率 < -阈值 → 卖出（或平仓）
    """

    params = (
        ('momentum_period', 20),   # 动量计算周期
        ('buy_threshold', 0.02),   # 买入阈值（2%）
        ('sell_threshold', -0.01), # 卖出阈值（-1%）
    )

    def __init__(self):
        # 计算动量（收益率）
        # ROC = (当前价格 - N天前价格) / N天前价格
        self.roc = bt.indicators.ROC(
            self.data.close,
            period=self.params.momentum_period
        )

        self.order = None
        self.buyprice = None

        print(f'\n{"="*60}')
        print(f'📊 动量策略参数')
        print(f'{"="*60}')
        print(f'  动量周期: {self.params.momentum_period} 日')
        print(f'  买入阈值: {self.params.buy_threshold:.1%}')
        print(f'  卖出阈值: {self.params.sell_threshold:.1%}')
        print(f'{"="*60}\n')

    def notify_order(self, order):
        """订单状态回调"""
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buyprice = order.executed.price
                print(f'  ✅ 买入: 价格={order.executed.price:.2f}, ROC={self.roc[0]:.2%}')
            else:
                if self.buyprice:
                    pnl = (order.executed.price - self.buyprice) * order.executed.size
                    print(f'  ✅ 卖出: 价格={order.executed.price:.2f}, ROC={self.roc[0]:.2%}, 盈亏={pnl:.2f}')

        self.order = None

    def next(self):
        """每个交易日调用"""
        if self.order:
            return

        # 确保有足够的动量数据
        if len(self.roc) < self.params.momentum_period + 1:
            return

        # 没有持仓
        if not self.position:
            # 动量为正且超过阈值 → 买入
            if self.roc[0] > self.params.buy_threshold:
                self.order = self.buy(size=100)
                print(f'\n📈 {self.datas[0].datetime.date(0)}: 动量买入信号')
                print(f'   ROC({self.params.momentum_period}日): {self.roc[0]:.2%}')
                print(f'   当前价格: {self.data.close[0]:.2f}')

        # 有持仓
        else:
            # 动量转负 → 卖出
            if self.roc[0] < self.params.sell_threshold:
                self.order = self.sell(size=100)
                print(f'\n📉 {self.datas[0].datetime.date(0)}: 动量卖出信号')
                print(f'   ROC({self.params.momentum_period}日): {self.roc[0]:.2%}')
                print(f'   当前价格: {self.data.close[0]:.2f}')


# ============= 策略 2: 相对动量策略 =============
class RelativeMomentum(bt.Strategy):
    """
    相对动量策略

    逻辑：
    - 比较短周期和长周期的动量
    - 短期动量 > 长期动量 → 加速上涨，买入
    - 短期动量 < 长期动量 → 动量减弱，卖出
    """

    params = (
        ('short_period', 10),
        ('long_period', 30),
    )

    def __init__(self):
        self.roc_short = bt.indicators.ROC(period=self.params.short_period)
        self.roc_long = bt.indicators.ROC(period=self.params.long_period)

        # 动量差值
        self.momentum_diff = self.roc_short - self.roc_long

    def next(self):
        if not self.position:
            # 短期动量大于长期动量
            if self.roc_short[0] > self.roc_long[0] and self.roc_short[0] > 0:
                self.buy(size=100)
                print(f'📈 {self.datas[0].datetime.date(0)}: 相对动量买入')
                print(f'   短期ROC: {self.roc_short[0]:.2%}, 长期ROC: {self.roc_long[0]:.2%}')
        else:
            # 短期动量小于长期动量
            if self.roc_short[0] < self.roc_long[0]:
                self.sell(size=100)
                print(f'📉 {self.datas[0].datetime.date(0)}: 相对动量卖出')
                print(f'   短期ROC: {self.roc_short[0]:.2%}, 长期ROC: {self.roc_long[0]:.2%}')


# ============= 策略 3: 动量 + MA 过滤 =============
class MomentumMA(bt.Strategy):
    """
    动量 + 均线过滤策略

    逻辑：
    - 只在价格位于均线之上时做多
    - 动量 > 0 且价格 > MA200 → 买入
    - 动量 < 0 → 卖出
    """

    def __init__(self):
        self.roc = bt.indicators.ROC(period=20)
        self.sma200 = bt.indicators.SMA(period=200)

    def next(self):
        # 确保有足够数据
        if len(self.sma200) < 200:
            return

        if not self.position:
            # 动量为正 且 价格在均线上方
            if self.roc[0] > 0 and self.data.close[0] > self.sma200[0]:
                self.buy(size=100)
                print(f'📈 {self.datas[0].datetime.date(0)}: 动量+趋势买入')
        else:
            # 动量转负
            if self.roc[0] < 0:
                self.sell(size=100)
                print(f'📉 {self.datas[0].datetime.date(0)}: 动量转负，卖出')


# ============= 策略 4: 逆波动率动量策略 =============
class MomentumVolatility(bt.Strategy):
    """
    逆波动率动量策略

    逻辑：
    - 高波动时降低仓位
    - 低波动时提高仓位
    - 动量 > 0 时做多，仓位大小与波动率成反比
    """

    def __init__(self):
        self.roc = bt.indicators.ROC(period=20)
        self.atr = bt.indicators.ATR(period=14)
        self.atr_sma = bt.indicators.SMA(self.atr, period=50)

    def next(self):
        # 确保有足够数据
        if len(self.atr_sma) < 50:
            return

        # 计算相对波动率
        if self.atr_sma[0] > 0:
            relative_vol = self.atr[0] / self.atr_sma[0]
        else:
            relative_vol = 1

        # 根据波动率调整仓位
        if relative_vol > 1.5:  # 高波动
            position_size = 50
        elif relative_vol < 0.7:  # 低波动
            position_size = 150
        else:
            position_size = 100

        if not self.position:
            if self.roc[0] > 0.02:
                self.buy(size=position_size)
                print(f'📈 动量买入，仓位={position_size}，波动率={relative_vol:.2f}')
        else:
            if self.roc[0] < -0.01:
                self.sell(size=self.position.size)
                print(f'📉 动量卖出，波动率={relative_vol:.2f}')


def run_backtest(strategy_class, strategy_name):
    """运行回测"""
    print("\n" + "=" * 60)
    print(f"策略: {strategy_name}")
    print("=" * 60)

    # 创建 Cerebro
    cerebro = bt.Cerebro()
    cerebro.addstrategy(strategy_class)

    # 生成数据
    df = generate_sample_data()
    df_indexed = df.set_index('datetime')

    # 加载数据
    data = bt.feeds.PandasData(dataname=df_indexed)
    cerebro.adddata(data)

    # 设置资金和手续费
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)

    # 添加观察者和分析器
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.DrawDown)
    cerebro.addobserver(bt.observers.BuySell)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

    # 运行回测
    print(f"\n💰 初始资金: {cerebro.broker.getvalue():.2f}")
    print("-" * 60)

    strat = cerebro.run()
    final_value = cerebro.broker.getvalue()

    # 打印结果
    print("-" * 60)
    print(f'💰 最终资金: {final_value:.2f}')
    print(f'📊 收益率: {(final_value/100000 - 1)*100:.2f}%')

    # 分析结果
    sharpe = strat[0].analyzers.sharpe.get_analysis()
    returns = strat[0].analyzers.returns.get_analysis()
    drawdown = strat[0].analyzers.drawdown.get_analysis()

    if 'sharperatio' in sharpe and sharpe['sharperatio'] is not None:
        print(f'📈 夏普比率: {sharpe["sharperatio"]:.2f}')

    if 'rtot' in returns:
        print(f'📊 累计收益: {returns["rtot"]:.2%}')

    if 'max' in drawdown:
        print(f'📉 最大回撤: {drawdown["max"]["drawdown"]:.2f}%')

    return cerebro


def main():
    """主函数"""
    print("=" * 60)
    print("动量策略回测")
    print("=" * 60)

    # 运行简单动量策略
    cerebro = run_backtest(MomentumStrategy, "简单动量策略")

    # 可以选择运行其他策略
    # run_backtest(RelativeMomentum, "相对动量策略")
    # run_backtest(MomentumMA, "动量 + MA 过滤策略")
    # run_backtest(MomentumVolatility, "逆波动率动量策略")

    # 绘制结果
    print("\n📈 正在生成图表...")
    cerebro.plot(style='candlestick', barup='red', bardown='green')
    print("✓ 完成！")


if __name__ == '__main__':
    main()
