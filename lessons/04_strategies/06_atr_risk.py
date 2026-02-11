#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
风险管理：ATR 动态止损策略

在量化交易中，风险管理比入场信号更重要！

本示例展示如何使用 ATR（平均真实波幅）实现动态止损：
- ATR 反映市场波动性
- 波动大时，止损距离应该更远
- 波动小时，止损距离可以更近

同时展示：
1. 移动止损（Trailing Stop）
2. 固定比例止损
3. 基于时间的止损
"""

import backtrader as bt
import pandas as pd
import random
from datetime import datetime


def generate_sample_data(days=300):
    """生成模拟数据"""
    start_date = datetime(2023, 1, 1)
    dates = pd.date_range(start_date, periods=days, freq='D')

    price = 100.0
    prices = []
    trend = 0
    trend_duration = 0

    for i in range(days):
        if trend_duration > 60:
            trend = random.uniform(-0.4, 0.4)
            trend_duration = 0

        trend_duration += 1
        change = random.uniform(-2, 2) + trend
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


class ATRStopLossStrategy(bt.Strategy):
    """
    ATR 动态止损策略

    入场：简单双均线金叉
    出场：ATR 动态止损

    止损价格 = 入场价格 - N * ATR
    """

    params = (
        ('fast_period', 10),
        ('slow_period', 30),
        ('atr_period', 14),
        ('atr_multiplier', 2.0),  # ATR 倍数
    )

    def __init__(self):
        # 入场信号
        self.fast_ma = bt.indicators.SMA(period=self.params.fast_period)
        self.slow_ma = bt.indicators.SMA(period=self.params.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

        # ATR
        self.atr = bt.indicators.ATR(period=self.params.atr_period)

        self.order = None
        self.entry_price = None
        self.stop_loss_price = None

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                # 设置止损价格
                self.stop_loss_price = self.entry_price - self.params.atr_multiplier * self.atr[0]
                print(f'  ✅ 买入: {order.executed.price:.2f}, 止损: {self.stop_loss_price:.2f}, ATR: {self.atr[0]:.2f}')
            else:
                pnl = (order.executed.price - self.entry_price) * order.executed.size
                print(f'  ✅ 卖出: {order.executed.price:.2f}, 盈亏: {pnl:.2f}')
        self.order = None

    def next(self):
        if self.order:
            return

        # 没有持仓，等待入场
        if not self.position:
            if self.crossover[0] > 0:
                self.order = self.buy(size=100)
                print(f'\n📈 {self.datas[0].datetime.date(0)}: 金叉买入')
                print(f'   快线: {self.fast_ma[0]:.2f}, 慢线: {self.slow_ma[0]:.2f}')
                print(f'   ATR: {self.atr[0]:.2f}')

        # 有持仓，检查止损
        else:
            # 检查止损
            if self.data.close[0] <= self.stop_loss_price:
                self.order = self.sell(size=100)
                print(f'\n🛑 {self.datas[0].datetime.date(0)}: ATR 止损触发')
                print(f'   当前价格: {self.data.close[0]:.2f}')
                print(f'   止损价格: {self.stop_loss_price:.2f}')
                print(f'   亏损: {(self.data.close[0] - self.entry_price):.2f}')


class TrailingStopStrategy(bt.Strategy):
    """
    移动止损策略（Trailing Stop）

    特点：
    - 盈利时，止损价格跟随价格上移
    - 锁定部分利润，同时给价格波动空间
    - 止损距离 = N * ATR
    """

    params = (
        ('atr_period', 14),
        ('atr_multiplier', 2.0),
    )

    def __init__(self):
        self.atr = bt.indicators.ATR(period=self.params.atr_period)
        self.roc = bt.indicators.ROC(period=20)

        self.order = None
        self.entry_price = None
        self.highest_price = None  # 持仓期间的最高价

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.highest_price = self.entry_price
                print(f'  ✅ 买入: {order.executed.price:.2f}')
            else:
                pnl = (order.executed.price - self.entry_price) * order.executed.size
                print(f'  ✅ 卖出: {order.executed.price:.2f}, 盈亏: {pnl:.2f}')
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            # 动量买入
            if self.roc[0] > 2:
                self.order = self.buy(size=100)
                print(f'\n📈 {self.datas[0].datetime.date(0)}: 动量买入, ROC={self.roc[0]:.2%}')
        else:
            # 更新最高价
            if self.data.close[0] > self.highest_price:
                self.highest_price = self.data.close[0]

            # 计算移动止损价格
            trailing_stop = self.highest_price - self.params.atr_multiplier * self.atr[0]

            # 检查止损
            if self.data.close[0] <= trailing_stop:
                self.order = self.sell(size=100)
                pnl_percent = (self.data.close[0] - self.entry_price) / self.entry_price * 100
                print(f'\n🛑 {self.datas[0].datetime.date(0)}: 移动止损触发')
                print(f'   当前价格: {self.data.close[0]:.2f}')
                print(f'   止损价格: {trailing_stop:.2f}')
                print(f'   最高价格: {self.highest_price:.2f}')
                print(f'   盈亏: {pnl_percent:.2f}%')


class PercentStopStrategy(bt.Strategy):
    """
    固定百分比止损策略

    简单但有效：
- 亏损达到预设百分比就止损
    """

    params = (
        ('stop_loss_percent', 0.05),  # 5% 止损
        ('take_profit_percent', 0.15), # 15% 止盈
    )

    def __init__(self):
        self.sma20 = bt.indicators.SMA(period=20)
        self.sma60 = bt.indicators.SMA(period=60)

        self.order = None
        self.entry_price = None

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                print(f'  ✅ 买入: {order.executed.price:.2f}')
            else:
                pnl = (order.executed.price - self.entry_price) * order.executed.size
                pnl_percent = (order.executed.price - self.entry_price) / self.entry_price * 100
                print(f'  ✅ 卖出: {order.executed.price:.2f}, 盈亏: {pnl:.2f} ({pnl_percent:+.1f}%)')
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            # 价格突破均线
            if self.data.close[0] > self.sma20[0] and self.sma20[0] > self.sma60[0]:
                self.order = self.buy(size=100)
                print(f'\n📈 {self.datas[0].datetime.date(0)}: 均线突破买入')
        else:
            # 计算盈亏百分比
            pnl_percent = (self.data.close[0] - self.entry_price) / self.entry_price

            # 止损
            if pnl_percent <= -self.params.stop_loss_percent:
                self.order = self.sell(size=100)
                print(f'\n🛑 {self.datas[0].datetime.date(0)}: 止损触发')
                print(f'   亏损: {pnl_percent:.2%}')

            # 止盈
            elif pnl_percent >= self.params.take_profit_percent:
                self.order = self.sell(size=100)
                print(f'\n🎯 {self.datas[0].datetime.date(0)}: 止盈触发')
                print(f'   盈利: {pnl_percent:.2%}')


class TimeBasedStop(bt.Strategy):
    """
    基于时间的止损

    逻辑：
    - 持仓超过 N 天仍未盈利，强制平仓
    - 避免资金长期占用
    """

    params = (
        ('max_hold_days', 20),  # 最长持仓天数
    )

    def __init__(self):
        self.roc = bt.indicators.ROC(period=20)
        self.order = None
        self.entry_price = None
        self.entry_date = None
        self.hold_days = 0

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.entry_date = self.datas[0].datetime.date(0)
                self.hold_days = 0
                print(f'  ✅ 买入: {order.executed.price:.2f}')
            else:
                pnl = (order.executed.price - self.entry_price) * order.executed.size
                print(f'  ✅ 卖出: {order.executed.price:.2f}, 盈亏: {pnl:.2f}')
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.roc[0] > 3:
                self.order = self.buy(size=100)
                print(f'\n📈 {self.datas[0].datetime.date(0)}: 动量买入')
        else:
            self.hold_days += 1

            # 时间止损
            if self.hold_days >= self.params.max_hold_days:
                self.order = self.sell(size=100)
                pnl_percent = (self.data.close[0] - self.entry_price) / self.entry_price * 100
                print(f'\n⏰ {self.datas[0].datetime.date(0)}: 时间止损触发')
                print(f'   持仓天数: {self.hold_days}')
                print(f'   盈亏: {pnl_percent:.1f}%')


class RiskParityPosition(bt.Strategy):
    """
    风险平价仓位管理

    特点：
    - 根据 ATR 和账户价值动态计算仓位
    - 每笔交易风险固定（如账户的 1%）
    - 波动大时减少仓位，波动小时增加仓位

    公式：
    仓位 = (账户价值 × 风险比例) / ATR
    """

    params = (
        ('risk_per_trade', 0.01),  # 每笔交易风险 1%
    )

    def __init__(self):
        self.atr = bt.indicators.ATR(period=14)
        self.roc = bt.indicators.ROC(period=20)

        self.order = None
        self.entry_price = None
        self.stop_loss_price = None

    def calculate_position_size(self):
        """根据风险平价计算仓位"""
        account_value = self.broker.getvalue()
        risk_amount = account_value * self.params.risk_per_trade
        stop_distance = 2 * self.atr[0]  # 2倍 ATR 的止损距离
        position_size = int(risk_amount / stop_distance)
        return max(position_size, 1)  # 至少 1 股

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.stop_loss_price = self.entry_price - 2 * self.atr[0]
                print(f'  ✅ 买入: {order.executed.price:.2f}, 数量: {order.executed.size}, 止损: {self.stop_loss_price:.2f}')
            else:
                pnl = (order.executed.price - self.entry_price) * order.executed.size
                print(f'  ✅ 卖出: {order.executed.price:.2f}, 盈亏: {pnl:.2f}')
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.roc[0] > 2:
                size = self.calculate_position_size()
                self.order = self.buy(size=size)
                print(f'\n📈 {self.datas[0].datetime.date(0)}: 风险平价买入')
                print(f'   ATR: {self.atr[0]:.2f}')
                print(f'   账户价值: {self.broker.getvalue():.2f}')
                print(f'   仓位大小: {size}')
        else:
            # 止损
            if self.data.close[0] <= self.stop_loss_price:
                self.order = self.sell(size=self.position.size)
                print(f'\n🛑 {self.datas[0].datetime.date(0)}: 风险平价止损')


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
    print("风险管理策略回测")
    print("=" * 60)

    # 运行 ATR 动态止损策略
    cerebro = run_backtest(ATRStopLossStrategy, "ATR 动态止损策略")

    # 可以选择运行其他策略
    # run_backtest(TrailingStopStrategy, "移动止损策略")
    # run_backtest(PercentStopStrategy, "固定百分比止损")
    # run_backtest(TimeBasedStop, "基于时间的止损")
    # run_backtest(RiskParityPosition, "风险平价仓位管理")

    # 绘制结果
    print("\n📈 正在生成图表...")
    cerebro.plot(style='candlestick', barup='red', bardown='green')
    print("✓ 完成！")


if __name__ == '__main__':
    main()
