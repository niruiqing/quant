#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
经典策略 2：布林带策略

布林带是一个基于统计学的技术分析工具，由三条线组成：
1. 中轨：N日移动平均线
2. 上轨：中轨 + K倍标准差
3. 下轨：中轨 - K倍标准差

策略类型：
- 均值回归策略：价格触及上下轨时反向交易
- 趋势突破策略：价格突破上下轨时顺势交易

本示例演示均值回归策略
"""

import backtrader as bt
import pandas as pd
import random
from datetime import datetime


def generate_sample_data(days=300):
    """生成模拟数据（震荡为主）"""
    start_date = datetime(2023, 1, 1)
    dates = pd.date_range(start_date, periods=days, freq='D')

    # 生成均值回归特征的数据
    price = 100.0
    prices = []

    for i in range(days):
        # 均值回归力量
        deviation = price - 100
        mean_reversion = -deviation * 0.15

        # 随机波动
        change = random.uniform(-4, 4) + mean_reversion
        price = max(price + change, 20)
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


# ============= 策略 1: 布林带均值回归策略 =============
class BollingerBandsStrategy(bt.Strategy):
    """
    布林带均值回归策略

    逻辑：
    - 价格触及下轨 → 超卖，买入
    - 价格触及上轨 → 超买，卖出
    - 价格回归中轨 → 平仓

    参数：
    - period: 均线周期
    - devfactor: 标准差倍数
    """

    params = (
        ('period', 20),         # 布林带周期
        ('devfactor', 2.0),     # 标准差倍数
        ('position_size', 100), # 每次交易数量
    )

    def __init__(self):
        # 创建布林带指标
        self.bollinger = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.period,
            devfactor=self.params.devfactor
        )

        # 引用各条线
        self.top = self.bollinger.top       # 上轨
        self.mid = self.bollinger.mid       # 中轨（SMA）
        self.bot = self.bollinger.bot       # 下轨

        self.order = None
        self.buyprice = None

        print(f'\n{"="*60}')
        print(f'📊 布林带策略参数')
        print(f'{"="*60}')
        print(f'  周期: {self.params.period} 日')
        print(f'  标准差倍数: {self.params.devfactor}')
        print(f'  每次交易数量: {self.params.position_size} 股')
        print(f'{"="*60}\n')

    def notify_order(self, order):
        """订单状态回调"""
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buyprice = order.executed.price
                print(f'  ✅ 买入成交')
                print(f'     价格: {order.executed.price:.2f}')
                print(f'     上轨: {self.top[0]:.2f}')
                print(f'     中轨: {self.mid[0]:.2f}')
                print(f'     下轨: {self.bot[0]:.2f}')
            else:
                pnl = (order.executed.price - self.buyprice) * order.executed.size
                print(f'  ✅ 卖出成交')
                print(f'     价格: {order.executed.price:.2f}')
                print(f'     盈亏: {pnl:.2f}')

        self.order = None

    def next(self):
        """每个交易日调用"""
        if self.order:
            return

        # 确保有足够的布林带数据
        if len(self.bollinger) < self.params.period:
            return

        # 没有持仓
        if not self.position:
            # 价格触及或低于下轨 → 买入信号
            if self.data.close[0] <= self.bot[0]:
                self.order = self.buy(size=self.params.position_size)
                print(f'\n📈 {self.datas[0].datetime.date(0)}: 价格触及下轨，买入信号')
                print(f'   价格: {self.data.close[0]:.2f}')
                print(f'   下轨: {self.bot[0]:.2f}')
                print(f'   中轨: {self.mid[0]:.2f}')
                print(f'   上轨: {self.top[0]:.2f}')

        # 有持仓
        else:
            # 方式1: 价格触及上轨 → 卖出
            if self.data.close[0] >= self.top[0]:
                self.order = self.sell(size=self.params.position_size)
                print(f'\n📉 {self.datas[0].datetime.date(0)}: 价格触及上轨，卖出信号')
                print(f'   价格: {self.data.close[0]:.2f}')
                print(f'   上轨: {self.top[0]:.2f}')

            # 方式2: 价格回归中轨 → 卖出（更保守）
            # elif self.data.close[0] >= self.mid[0]:
            #     self.order = self.sell(size=self.params.position_size)
            #     print(f'\n📉 价格回归中轨，卖出')


# ============= 策略 2: 布林带宽度策略 =============
class BollingerWidthStrategy(bt.Strategy):
    """
    布林带宽度策略

    逻辑：
    - 布林带收窄后扩张 → 突破信号
    - 带宽 = (上轨 - 下轨) / 中轨
    """

    def __init__(self):
        self.bollinger = bt.indicators.BollingerBands(period=20, devfactor=2)

        # 计算带宽
        self.bbw = (self.bollinger.top - self.bollinger.bot) / self.bollinger.mid

        # 带宽的移动平均
        self.bbw_sma = bt.indicators.SMA(self.bbw, period=20)

    def next(self):
        # 确保有足够数据
        if len(self.bbw) < 20:
            return

        # 带宽从低位扩张
        if self.bbw[0] > self.bbw_sma[0] and self.bbw[-1] <= self.bbw_sma[-1]:
            if not self.position:
                # 带宽扩张 + 价格在上半区 → 做多
                if self.data.close[0] > self.bollinger.mid[0]:
                    self.buy(size=100)
                    print(f'📈 {self.datas[0].datetime.date(0)}: 带宽扩张突破，买入')
        else:
            # 带宽收窄时平仓
            if self.position:
                self.sell(size=100)
                print(f'📉 带宽收窄，平仓')


# ============= 策略 3: 布林带 %B 策略 =============
class BollingerPercentB(bt.Strategy):
    """
    布林带 %B 指标策略

    %B = (价格 - 下轨) / (上轨 - 下轨)

    逻辑：
    - %B < 0 → 超卖，买入
    - %B > 1 → 超买，卖出
    """

    def __init__(self):
        self.bollinger = bt.indicators.BollingerBands(period=20, devfactor=2)

        # 计算 %B
        self.pctb = (self.data.close - self.bollinger.bot) / \
                    (self.bollinger.top - self.bollinger.bot)

    def next(self):
        if not self.position:
            # %B < 0.1 → 超卖
            if self.pctb[0] < 0.1:
                self.buy(size=100)
                print(f'📈 %B={self.pctb[0]:.2f} < 0.1, 买入')
        else:
            # %B > 0.9 → 超买
            if self.pctb[0] > 0.9:
                self.sell(size=100)
                print(f'📉 %B={self.pctb[0]:.2f} > 0.9, 卖出')


# ============= 策略 4: 布林带趋势突破 =============
class BollingerTrend(bt.Strategy):
    """
    布林带趋势突破策略

    逻辑：
    - 价格突破上轨 → 强势，买入
    - 价格跌破中轨 → 趋势结束，卖出
    """

    def __init__(self):
        self.bollinger = bt.indicators.BollingerBands(period=20, devfactor=2)
        self.sma200 = bt.indicators.SMA(period=200)  # 长期趋势过滤

    def next(self):
        # 只在上升趋势中交易
        if self.data.close[0] < self.sma200[0]:
            if self.position:
                self.sell(size=100)
                print(f'📉 跌破长期均线，平仓')
            return

        if not self.position:
            # K线收盘价突破上轨
            if self.data.close[0] > self.bollinger.top[0]:
                self.buy(size=100)
                print(f'📈 突破上轨，买入')
        else:
            # 跌破中轨平仓
            if self.data.close[0] < self.bollinger.mid[0]:
                self.sell(size=100)
                print(f'📉 跌破中轨，平仓')


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
        print(f'📉 最大回撤: {drawdown["max"]["drawdown"]:.2%}')

    return cerebro


def main():
    """主函数"""
    print("=" * 60)
    print("布林带策略回测")
    print("=" * 60)

    # 运行布林带均值回归策略
    cerebro = run_backtest(BollingerBandsStrategy, "布林带均值回归策略")

    # 可以选择运行其他策略
    # run_backtest(BollingerWidthStrategy, "布林带宽度策略")
    # run_backtest(BollingerPercentB, "布林带 %B 策略")
    # run_backtest(BollingerTrend, "布林带趋势突破策略")

    # 绘制结果
    print("\n📈 正在生成图表...")
    cerebro.plot(style='candlestick', barup='red', bardown='green')
    print("✓ 完成！")


if __name__ == '__main__':
    main()
