#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backtrader Hello World - 使用本地模拟数据
这是一个可以直接运行的完整示例

核心概念：
- Cerebro: 回测引擎
- Strategy: 交易策略
- Data: 价格数据
- Broker: 模拟券商（处理订单、资金）
"""

import backtrader as bt
import pandas as pd
import random
from datetime import datetime


def generate_sample_data():
    """
    生成模拟的股票数据
    返回一个 DataFrame，包含 Backtrader 需要的列
    """
    # 日期范围
    start_date = datetime(2023, 1, 1)
    dates = pd.date_range(start_date, periods=100, freq='D')

    # 生成随机价格数据（简单的随机游走）
    price = 100.0
    prices = []
    volumes = []

    for _ in range(100):
        change = random.uniform(-2, 2)  # 每天变化 -2 到 +2
        price = max(price + change, 10)  # 价格不能低于 10
        prices.append(price)
        volumes.append(random.randint(1000, 10000))

    # 创建 DataFrame（Backtrader 需要的列名）
    df = pd.DataFrame({
        'datetime': dates,
        'open': [p * random.uniform(0.98, 1.02) for p in prices],
        'high': [p * random.uniform(1.0, 1.05) for p in prices],
        'low': [p * random.uniform(0.95, 1.0) for p in prices],
        'close': prices,
        'volume': volumes,
        'openinterest': [0] * 100
    })

    return df


class HelloWorldStrategy(bt.Strategy):
    """
    Hello World 策略
    简单逻辑：价格低于 95 时买入，高于 105 时卖出
    """

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None

    def notify_order(self, order):
        """订单状态变化时调用"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                print(f'✅ 买入执行: 价格={order.executed.price:.2f}, '
                      f'手续费={order.executed.comm:.2f}, '
                      f'数量={order.executed.size}')
            else:
                print(f'✅ 卖出执行: 价格={order.executed.price:.2f}, '
                      f'手续费={order.executed.comm:.2f}, '
                      f'数量={order.executed.size}')

        self.order = None

    def next(self):
        """每个交易日调用"""
        # 如果有待处理的订单，直接返回
        if self.order:
            return

        # 如果没有持仓
        if not self.position:
            # 价格低于 95，买入
            if self.dataclose[0] < 95:
                self.order = self.buy(size=10)
                print(f'📈 {self.datas[0].datetime.date(0)}: 发出买入信号, 价格={self.dataclose[0]:.2f}')
        else:
            # 如果已持仓，价格高于 105，卖出
            if self.dataclose[0] > 105:
                self.order = self.sell(size=10)
                print(f'📉 {self.datas[0].datetime.date(0)}: 发出卖出信号, 价格={self.dataclose[0]:.2f}')


def main():
    """主函数"""
    print("=" * 60)
    print("Backtrader Hello World 示例")
    print("=" * 60)

    # 1. 生成数据
    print("\n📊 生成模拟数据...")
    df = generate_sample_data()
    df.to_csv('data/sample_data.csv', index=False)
    print(f"✓ 数据已保存到 data/sample_data.csv")
    print(f"✓ 数据行数: {len(df)}")
    print(f"✓ 日期范围: {df['datetime'].min()} 到 {df['datetime'].max()}")

    # 2. 创建 Cerebro 引擎
    cerebro = bt.Cerebro()

    # 3. 添加策略
    cerebro.addstrategy(HelloWorldStrategy)

    # 4. 加载数据
    # 将 datetime 设置为索引，Backtrader 会自动识别
    df_indexed = df.set_index('datetime')
    data = bt.feeds.PandasData(dataname=df_indexed)
    cerebro.adddata(data)

    # 5. 设置初始资金
    initial_cash = 10000.0
    cerebro.broker.setcash(initial_cash)

    # 6. 设置手续费（0.1%）
    cerebro.broker.setcommission(commission=0.001)

    # 7. 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

    # 8. 运行回测
    print(f"\n💰 初始资金: {initial_cash:.2f}")
    print("-" * 60)
    strat = cerebro.run()
    final_value = cerebro.broker.getvalue()
    print("-" * 60)
    print(f"💰 最终资金: {final_value:.2f}")
    print(f"📊 总收益: {final_value - initial_cash:.2f} ({(final_value/initial_cash - 1)*100:.2f}%)")

    # 9. 绘制结果
    print("\n📈 正在生成图表...")
    cerebro.plot(style='candlestick', barup='red', bardown='green')
    print("✓ 完成！")


if __name__ == '__main__':
    main()
