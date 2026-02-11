#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
经典策略 1：双均线策略

这是一个最经典的趋势跟踪策略

策略原理：
- 金叉：短期均线上穿长期均线 → 买入信号
- 死叉：短期均线下穿长期均线 → 卖出信号

优点：
- 简单易懂，容易实现
- 在趋势市场中表现良好

缺点：
- 震荡市频繁交易，容易亏损
- 滞后性，信号出现时趋势已运行一段时间
"""

import backtrader as bt
import pandas as pd
import random
from datetime import datetime


def generate_sample_data(days=300):
    """生成模拟数据"""
    start_date = datetime(2023, 1, 1)
    dates = pd.date_range(start_date, periods=days, freq='D')

    # 生成有趋势和震荡的数据
    price = 100.0
    prices = []
    trend = 0
    trend_duration = 0

    for i in range(days):
        # 每 50 天切换一次趋势
        if trend_duration > 50:
            trend = random.uniform(-0.5, 0.5)
            trend_duration = 0

        trend_duration += 1
        change = random.uniform(-1.5, 1.5) + trend
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


class DualMAStrategy(bt.Strategy):
    """
    双均线策略

    参数：
    - fast_period: 快线周期（默认 10）
    - slow_period: 慢线周期（默认 30）
    - position_size: 每次交易数量（默认 100）
    """

    params = (
        ('fast_period', 10),
        ('slow_period', 30),
        ('position_size', 100),
    )

    def __init__(self):
        """初始化策略"""
        # 快线
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.params.fast_period)
        # 慢线
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.params.slow_period)

        # 交叉指标
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

        # 追踪价格和订单
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # 统计信息
        self.trade_count = 0
        self.wins = 0
        self.losses = 0

        print(f'\n{"="*60}')
        print(f'📊 双均线策略参数')
        print(f'{"="*60}')
        print(f'  快线周期: {self.params.fast_period} 日')
        print(f'  慢线周期: {self.params.slow_period} 日')
        print(f'  每次交易数量: {self.params.position_size} 股')
        print(f'{"="*60}\n')

    def notify_order(self, order):
        """订单状态回调"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                print(f'✅ 买入成交')
                print(f'   日期: {self.datas[0].datetime.date(0)}')
                print(f'   价格: {order.executed.price:.2f}')
                print(f'   数量: {order.executed.size:.0f}')
                print(f'   金额: {order.executed.value:.2f}')
                print(f'   手续费: {order.executed.comm:.2f}')
                print(f'   现金: {self.broker.getcash():.2f}')
            else:  # 卖出
                pnl = (order.executed.price - self.buyprice) * order.executed.size
                pnl_net = pnl - order.executed.comm - self.buycomm

                print(f'✅ 卖出成交')
                print(f'   日期: {self.datas[0].datetime.date(0)}')
                print(f'   价格: {order.executed.price:.2f}')
                print(f'   数量: {order.executed.size:.0f}')
                print(f'   盈亏: {pnl:.2f}')
                print(f'   净盈亏: {pnl_net:.2f}')

                if pnl_net > 0:
                    self.wins += 1
                    print(f'   ✨ 盈利！')
                else:
                    self.losses += 1
                    print(f'   ⚠️ 亏损')

        self.order = None

    def notify_trade(self, trade):
        """交易完成回调"""
        if not trade.isclosed:
            return

        self.trade_count += 1

    def next(self):
        """每个交易日调用"""
        # 如果有待处理订单，等待
        if self.order:
            return

        # 如果没有持仓
        if not self.position:
            # 金叉：快线上穿慢线
            if self.crossover[0] > 0:
                self.order = self.buy(size=self.params.position_size)
                print(f'\n📈 {self.datas[0].datetime.date(0)}: 金叉信号！')
                print(f'   快线: {self.fast_ma[0]:.2f}')
                print(f'   慢线: {self.slow_ma[0]:.2f}')
                print(f'   收盘价: {self.data.close[0]:.2f}')

        # 有持仓
        else:
            # 死叉：快线下穿慢线
            if self.crossover[0] < 0:
                self.order = self.sell(size=self.params.position_size)
                print(f'\n📉 {self.datas[0].datetime.date(0)}: 死叉信号！')
                print(f'   快线: {self.fast_ma[0]:.2f}')
                print(f'   慢线: {self.slow_ma[0]:.2f}')
                print(f'   收盘价: {self.data.close[0]:.2f}')


def run_backtest(fast_period=10, slow_period=30):
    """运行回测"""
    # 创建 Cerebro
    cerebro = bt.Cerebro()

    # 添加策略
    cerebro.addstrategy(
        DualMAStrategy,
        fast_period=fast_period,
        slow_period=slow_period
    )

    # 生成数据
    df = generate_sample_data()
    df_indexed = df.set_index('datetime')

    # 加载数据
    data = bt.feeds.PandasData(dataname=df_indexed)
    cerebro.adddata(data)

    # 设置资金
    initial_cash = 100000.0
    cerebro.broker.setcash(initial_cash)

    # 设置手续费（0.1%）
    cerebro.broker.setcommission(commission=0.001)

    # 添加观察者
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.DrawDown)
    cerebro.addobserver(bt.observers.BuySell)

    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    # 运行回测
    print(f'\n💰 初始资金: {initial_cash:.2f}')
    print(f'{"="*60}\n')

    strat = cerebro.run()
    final_value = cerebro.broker.getvalue()

    # 打印结果
    print(f'\n{"="*60}')
    print(f'📊 回测结果')
    print(f'{"="*60}')
    print(f'初始资金: {initial_cash:.2f}')
    print(f'最终资金: {final_value:.2f}')
    print(f'总收益: {final_value - initial_cash:.2f} ({(final_value/initial_cash - 1)*100:.2f}%)')

    # 分析结果
    sharpe = strat[0].analyzers.sharpe.get_analysis()
    returns = strat[0].analyzers.returns.get_analysis()
    drawdown = strat[0].analyzers.drawdown.get_analysis()
    trades = strat[0].analyzers.trades.get_analysis()

    if 'sharperatio' in sharpe and sharpe['sharperatio'] is not None:
        print(f'夏普比率: {sharpe["sharperatio"]:.2f}')

    if 'rtot' in returns:
        print(f'累计收益率: {returns["rtot"]:.2%}')

    if 'ravg' in returns:
        print(f'平均日收益率: {returns["ravg"]:.2%}')

    if 'max' in drawdown:
        print(f'最大回撤: {drawdown["max"]["drawdown"]:.2%}')

    if 'total' in trades:
        total_trades = trades['total']['total']
        won_trades = trades['won']['total'] if 'won' in trades else 0
        win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0
        print(f'总交易次数: {total_trades}')
        print(f'盈利交易: {won_trades}')
        print(f'胜率: {win_rate:.1f}%')

    print(f'{"="*60}\n')

    return cerebro


def main():
    """主函数"""
    print("=" * 60)
    print("双均线策略回测")
    print("=" * 60)

    # 运行回测
    cerebro = run_backtest(fast_period=10, slow_period=30)

    # 绘制结果
    print("📈 正在生成图表...")
    cerebro.plot(style='candlestick', barup='red', bardown='green')
    print("✓ 完成！")


if __name__ == '__main__':
    main()
