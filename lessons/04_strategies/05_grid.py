#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
策略 5：网格交易策略 (Grid Trading)

网格交易是一种适合震荡市的策略，不预测价格方向，
而是在设定的价格网格上机械地执行买卖规则。

策略原理：
1. 设定一个价格中心点和网格间距
2. 价格每下跌一个网格，买入一份
3. 价格每上涨一个网格，卖出一份
4. 通过不断低买高卖赚取价差

优点：
- 震荡市稳定盈利
- 不需要预测方向
- 规则简单机械

缺点：
- 单边行情会不断加仓，资金占用大
- 需要充足的资金支撑
- 可能长期被套
"""

import backtrader as bt
import pandas as pd
import random
from datetime import datetime


def generate_sample_data(days=300):
    """生成模拟数据（震荡为主）"""
    start_date = datetime(2023, 1, 1)
    dates = pd.date_range(start_date, periods=days, freq='D')

    price = 100.0
    prices = []

    for i in range(days):
        # 强均值回归，产生震荡
        deviation = price - 100
        mean_reversion = -deviation * 0.2
        change = random.uniform(-3, 3) + mean_reversion
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


class GridStrategy(bt.Strategy):
    """
    网格交易策略

    参数：
    - center_price: 网格中心价格
    - grid_spacing: 网格间距（百分比，如 0.05 表示 5%）
    - grid_levels: 网格层数（上下各几层）
    - order_size: 每格交易数量
    """

    params = (
        ('center_price', 100.0),   # 中心价格
        ('grid_spacing', 0.05),    # 网格间距 5%
        ('grid_levels', 5),        # 网格层数
        ('order_size', 10),        # 每格交易数量
    )

    def __init__(self):
        # 计算网格价格
        self.buy_grids = []
        self.sell_grids = []

        # 生成买入网格（中心价下方）
        for i in range(1, self.params.grid_levels + 1):
            price = self.params.center_price * (1 - self.params.grid_spacing * i)
            self.buy_grids.append(price)

        # 生成卖出网格（中心价上方）
        for i in range(1, self.params.grid_levels + 1):
            price = self.params.center_price * (1 + self.params.grid_spacing * i)
            self.sell_grids.append(price)

        # 排序
        self.buy_grids.sort(reverse=True)  # 从高到低
        self.sell_grids.sort()  # 从低到高

        # 已触发的网格
        self.triggered_buy = set()
        self.triggered_sell = set()

        # 最后价格（用于检测跨越网格）
        self.last_price = None

        self.order = None

        print(f'\n{"="*60}')
        print(f'📊 网格交易策略参数')
        print(f'{"="*60}')
        print(f'  中心价格: {self.params.center_price:.2f}')
        print(f'  网格间距: {self.params.grid_spacing:.1%}')
        print(f'  网格层数: {self.params.grid_levels}')
        print(f'  每格数量: {self.params.order_size}')
        print(f'\n  买入网格: {[f"{p:.2f}" for p in self.buy_grids]}')
        print(f'  卖出网格: {[f"{p:.2f}" for p in self.sell_grids]}')
        print(f'{"="*60}\n')

    def notify_order(self, order):
        """订单状态回调"""
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'  ✅ 买入成交: 价格={order.executed.price:.2f}, 数量={order.executed.size}')
            else:
                print(f'  ✅ 卖出成交: 价格={order.executed.price:.2f}, 数量={order.executed.size}')

        self.order = None

    def next(self):
        """每个交易日调用"""
        if self.order:
            return

        current_price = self.data.close[0]

        # 第一天
        if self.last_price is None:
            self.last_price = current_price
            return

        # 检查是否触发买入网格
        for grid_price in self.buy_grids:
            if grid_price in self.triggered_buy:
                continue

            # 价格跌破网格线
            if self.last_price > grid_price and current_price <= grid_price:
                self.order = self.buy(size=self.params.order_size)
                self.triggered_buy.add(grid_price)
                print(f'\n📈 {self.datas[0].datetime.date(0)}: 触发买入网格')
                print(f'   网格价格: {grid_price:.2f}')
                print(f'   当前价格: {current_price:.2f}')

        # 检查是否触发卖出网格
        for grid_price in self.sell_grids:
            if grid_price in self.triggered_sell:
                continue

            # 有持仓才卖出
            if self.position.size > 0:
                # 价格突破网格线
                if self.last_price < grid_price and current_price >= grid_price:
                    self.order = self.sell(size=self.params.order_size)
                    self.triggered_sell.add(grid_price)
                    print(f'\n📉 {self.datas[0].datetime.date(0)}: 触发卖出网格')
                    print(f'   网格价格: {grid_price:.2f}')
                    print(f'   当前价格: {current_price:.2f}')

        self.last_price = current_price


class GridStrategyDynamic(bt.Strategy):
    """
    动态网格策略

    特点：
    - 网格中心价格跟随移动平均线调整
    - 适用于有趋势的震荡市场
    """

    params = (
        ('ma_period', 50),        # 移动平均周期
        ('grid_spacing', 0.05),   # 网格间距
        ('grid_levels', 3),       # 网格层数
        ('order_size', 10),
    )

    def __init__(self):
        self.ma = bt.indicators.SMA(period=self.params.ma_period)

        # 网格价格（会动态更新）
        self.buy_grids = []
        self.sell_grids = []
        self.last_ma = None

        self.order = None
        self.triggered_buy = set()
        self.triggered_sell = set()
        self.last_price = None

    def update_grids(self, center_price):
        """更新网格价格"""
        self.buy_grids = []
        self.sell_grids = []

        for i in range(1, self.params.grid_levels + 1):
            buy_price = center_price * (1 - self.params.grid_spacing * i)
            sell_price = center_price * (1 + self.params.grid_spacing * i)
            self.buy_grids.append(buy_price)
            self.sell_grids.append(sell_price)

        self.buy_grids.sort(reverse=True)
        self.sell_grids.sort()

    def next(self):
        if self.order:
            return

        current_price = self.data.close[0]
        current_ma = self.ma[0]

        # MA 发生变化，更新网格
        if self.last_ma is None or abs(current_ma - self.last_ma) > self.last_ma * 0.02:
            self.update_grids(current_ma)
            self.last_ma = current_ma
            self.triggered_buy.clear()
            self.triggered_sell.clear()
            print(f'\n🔄 {self.datas[0].datetime.date(0)}: 更新网格中心价 {current_ma:.2f}')

        if self.last_price is None:
            self.last_price = current_price
            return

        # 检查买入网格
        for grid_price in self.buy_grids:
            if grid_price not in self.triggered_buy:
                if self.last_price > grid_price and current_price <= grid_price:
                    self.order = self.buy(size=self.params.order_size)
                    self.triggered_buy.add(grid_price)
                    print(f'📈 买入网格触发: {grid_price:.2f}')

        # 检查卖出网格
        for grid_price in self.sell_grids:
            if grid_price not in self.triggered_sell:
                if self.position.size > 0:
                    if self.last_price < grid_price and current_price >= grid_price:
                        self.order = self.sell(size=self.params.order_size)
                        self.triggered_sell.add(grid_price)
                        print(f'📉 卖出网格触发: {grid_price:.2f}')

        self.last_price = current_price

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'  ✅ 买入: {order.executed.price:.2f}')
            else:
                print(f'  ✅ 卖出: {order.executed.price:.2f}')
        self.order = None


class InfiniteGrid(bt.Strategy):
    """
    无限网格策略

    特点：
    - 不设固定网格层数
    - 价格每跌一定比例就买入
    - 价格每涨一定比例就卖出
    - 持仓越多，卖出网格越密
    """

    params = (
        ('grid_spacing', 0.03),   # 网格间距 3%
        ('order_size', 10),       # 基础交易数量
    )

    def __init__(self):
        self.last_buy_price = None  # 最后买入价格
        self.last_sell_price = None # 最后卖出价格
        self.base_price = self.data.close[0]  # 基准价格
        self.order = None

    def next(self):
        if self.order:
            return

        current_price = self.data.close[0]

        # 如果没有持仓，等待价格回到基准价以下再开始
        if not self.position:
            if current_price < self.base_price * (1 - self.params.grid_spacing):
                self.last_buy_price = current_price
                self.order = self.buy(size=self.params.order_size)
                print(f'📈 首次买入: {current_price:.2f}')
            return

        # 有持仓时的逻辑
        if self.last_buy_price is not None:
            # 价格下跌 3% → 买入
            target_buy = self.last_buy_price * (1 - self.params.grid_spacing)
            if current_price <= target_buy:
                self.last_buy_price = current_price
                self.order = self.buy(size=self.params.order_size)
                print(f'📈 加仓买入: {current_price:.2f}')

        if self.last_buy_price is not None:
            # 价格上涨 3% → 卖出（按比例）
            target_sell = self.last_buy_price * (1 + self.params.grid_spacing)
            if current_price >= target_sell and self.position.size >= self.params.order_size:
                self.order = self.sell(size=self.params.order_size)
                print(f'📉 获利卖出: {current_price:.2f}')

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'  ✅ 买入成交: {order.executed.price:.2f}, 持仓={self.position.size}')
            else:
                print(f'  ✅ 卖出成交: {order.executed.price:.2f}, 持仓={self.position.size}')
        self.order = None


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
    print("网格交易策略回测")
    print("=" * 60)

    # 运行固定网格策略
    cerebro = run_backtest(GridStrategy, "固定网格策略")

    # 可以选择运行其他策略
    # run_backtest(GridStrategyDynamic, "动态网格策略")
    # run_backtest(InfiniteGrid, "无限网格策略")

    # 绘制结果
    print("\n📈 正在生成图表...")
    cerebro.plot(style='candlestick', barup='red', bardown='green')
    print("✓ 完成！")


if __name__ == '__main__':
    main()
