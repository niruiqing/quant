#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
经典策略 3：海龟交易法则 (Turtle Trading)

这是量化交易史上最著名的策略之一，源自 1983 年理查德·丹尼斯
著名的"海龟实验"。

策略核心思想：
1. 趋势跟踪：价格突破 N 日高点/低点时入场
2. 仓位管理：基于 ATR（平均真实波幅）计算仓位
3. 风险控制：严格的止损和加仓规则

海龟交易有两个系统：
- 系统 1：短期突破（20 日）
- 系统 2：长期突破（55 日）

本示例实现系统 1
"""

import backtrader as bt
import pandas as pd
import random
from datetime import datetime


def generate_sample_data(days=600):
    """生成模拟数据（带趋势）"""
    start_date = datetime(2022, 1, 1)
    dates = pd.date_range(start_date, periods=days, freq='D')

    price = 100.0
    prices = []
    trend = 0
    trend_duration = 0

    for i in range(days):
        # 每 100 天切换一次趋势（较长趋势）
        if trend_duration > 100:
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


class TurtleStrategy(bt.Strategy):
    """
    海龟交易策略（系统 1：20 日突破）

    入场规则：
    - 价格突破过去 20 日最高价 → 买入
    - 价格跌破过去 20 日最低价 → 卖空

    离场规则：
    - 多头持仓：价格跌破过去 10 日最低价 → 离场
    - 空头持仓：价格突破过去 10 日最高价 → 离场

    仓位管理：
    - 基于 ATR 计算单位头寸
    - 每 1% ATR 的波动对应 1% 账户风险
    """

    params = (
        ('entry_period', 20),     # 入场周期
        ('exit_period', 10),      # 离场周期
        ('atr_period', 20),       # ATR 周期
        ('risk_ratio', 0.01),     # 每单位风险比例（1%）
    )

    def __init__(self):
        # Donchian 通道（用于突破信号）
        self.donchian_entry = bt.indicators.DonchianChannels(
            period=self.params.entry_period,
            subplot=False
        )

        self.donchian_exit = bt.indicators.DonchianChannels(
            period=self.params.exit_period,
            subplot=False
        )

        # ATR（用于仓位管理）
        self.atr = bt.indicators.ATR(period=self.params.atr_period)

        self.order = None
        self.entry_price = None
        self.units = 0  # 当前持有单位数

        print(f'\n{"="*60}')
        print(f'📊 海龟交易策略参数')
        print(f'{"="*60}')
        print(f'  入场周期: {self.params.entry_period} 日')
        print(f'  离场周期: {self.params.exit_period} 日')
        print(f'  ATR 周期: {self.params.atr_period} 日')
        print(f'  风险比例: {self.params.risk_ratio:.1%}')
        print(f'{"="*60}\n')

    def notify_order(self, order):
        """订单状态回调"""
        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                print(f'  ✅ 买入成交')
                print(f'     价格: {order.executed.price:.2f}')
                print(f'     数量: {order.executed.size:.0f}')
                print(f'     ATR: {self.atr[0]:.2f}')
            else:
                if self.entry_price:
                    pnl = (order.executed.price - self.entry_price) * order.executed.size
                    print(f'  ✅ 卖出成交')
                    print(f'     价格: {order.executed.price:.2f}')
                    print(f'     盈亏: {pnl:.2f}')
                else:
                    print(f'  ✅ 卖空成交')
                    print(f'     价格: {order.executed.price:.2f}')

        self.order = None

    def calculate_unit_size(self):
        """
        计算单位头寸大小

        海龟公式：
        单位 = (账户价值 × 风险比例) / ATR
        """
        portfolio_value = self.broker.getvalue()
        risk_amount = portfolio_value * self.params.risk_ratio
        unit_size = int(risk_amount / self.atr[0])

        # 确保至少交易 1 股
        unit_size = max(unit_size, 1)

        return unit_size

    def next(self):
        """每个交易日调用"""
        # 确保有足够数据
        if len(self.data) < self.params.entry_period + 1:
            return

        # 如果有待处理订单，等待
        if self.order:
            return

        # 获取通道上下轨
        entry_high = self.donchian_entry.top[0]
        entry_low = self.donchian_entry.bot[0]
        exit_high = self.donchian_exit.top[0]
        exit_low = self.donchian_exit.bot[0]

        # 没有持仓时
        if not self.position:
            # 多头突破：价格超过 entry_period 日最高价
            if self.data.close[0] > entry_high:
                unit_size = self.calculate_unit_size()
                self.order = self.buy(size=unit_size)
                self.units = 1
                print(f'\n📈 {self.datas[0].datetime.date(0)}: 海龟买入信号')
                print(f'   突破价格: {entry_high:.2f}')
                print(f'   当前价格: {self.data.close[0]:.2f}')
                print(f'   单位大小: {unit_size} 股')
                print(f'   ATR: {self.atr[0]:.2f}')

            # 空头突破：价格跌破 entry_period 日最低价
            elif self.data.close[0] < entry_low:
                unit_size = self.calculate_unit_size()
                self.order = self.sell(size=unit_size)
                self.units = 1
                print(f'\n📉 {self.datas[0].datetime.date(0)}: 海龟卖空信号')
                print(f'   突破价格: {entry_low:.2f}')
                print(f'   当前价格: {self.data.close[0]:.2f}')
                print(f'   单位大小: {unit_size} 股')
                print(f'   ATR: {self.atr[0]:.2f}')

        # 有多头持仓时
        elif self.position.size > 0:
            # 止损离场：价格跌破 exit_period 日最低价
            if self.data.close[0] < exit_low:
                self.order = self.sell(size=self.position.size)
                print(f'\n🛑 {self.datas[0].datetime.date(0)}: 海龟离场信号（多头）')
                print(f'   离场价格: {exit_low:.2f}')
                print(f'   当前价格: {self.data.close[0]:.2f}')

            # 加仓：价格再创新高（可选，海龟原策略允许加仓）
            # elif self.data.close[0] > self.entry_price * (1 + 0.5 * self.atr[0] / self.entry_price):
            #     if self.units < 4:  # 最多 4 个单位
            #         unit_size = self.calculate_unit_size()
            #         self.order = self.buy(size=unit_size)
            #         self.units += 1
            #         print(f'📈 加仓信号（第 {self.units} 单位）')

        # 有空头持仓时
        else:  # self.position.size < 0
            # 止损离场：价格突破 exit_period 日最高价
            if self.data.close[0] > exit_high:
                self.order = self.buy(size=-self.position.size)  # 平空
                print(f'\n🛑 {self.datas[0].datetime.date(0)}: 海龟离场信号（空头）')
                print(f'   离场价格: {exit_high:.2f}')
                print(f'   当前价格: {self.data.close[0]:.2f}')


class TurtleStrategySimple(bt.Strategy):
    """
    简化版海龟策略（仅做多）

    适合：
    - 不想使用杠杆
    - 只想捕捉上升趋势
    """

    params = (
        ('entry_period', 20),
        ('exit_period', 10),
    )

    def __init__(self):
        # 计算 N 日最高价和最低价
        self.high_period = bt.indicators.Highest(self.data.high, period=self.params.entry_period)
        self.low_period = bt.indicators.Lowest(self.data.low, period=self.params.entry_period)
        self.exit_low = bt.indicators.Lowest(self.data.low, period=self.params.exit_period)

        self.order = None
        self.buyprice = None

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buyprice = order.executed.price
                print(f'  ✅ 买入: {order.executed.price:.2f}')
            else:
                pnl = (order.executed.price - self.buyprice) * order.executed.size
                print(f'  ✅ 卖出: {order.executed.price:.2f}, 盈亏={pnl:.2f}')
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            # 价格突破 N 日最高价
            if self.data.close[0] > self.high_period[0]:
                self.order = self.buy(size=100)
                print(f'\n📈 {self.datas[0].datetime.date(0)}: 突破信号')
                print(f'   突破价: {self.high_period[0]:.2f}')
        else:
            # 价格跌破 N 日最低价
            if self.data.close[0] < self.exit_low[0]:
                self.order = self.sell(size=100)
                print(f'\n📉 {self.datas[0].datetime.date(0)}: 离场信号')
                print(f'   离场价: {self.exit_low[0]:.2f}')


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
    print("海龟交易法则策略回测")
    print("=" * 60)

    # 运行完整海龟策略
    cerebro = run_backtest(TurtleStrategy, "海龟交易策略（系统 1）")

    # 可以选择运行简化版
    # run_backtest(TurtleStrategySimple, "海龟策略简化版（仅做多）")

    # 绘制结果
    print("\n📈 正在生成图表...")
    cerebro.plot(style='candlestick', barup='red', bardown='green')
    print("✓ 完成！")


if __name__ == '__main__':
    main()
