#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backtrader CSV 数据加载示例

学习要点：
1. 从 CSV 文件加载数据
2. 数据格式要求
3. 数据预处理
"""

import backtrader as bt
import pandas as pd
import random
from datetime import datetime


def create_sample_csv():
    """
    创建示例 CSV 文件
    演示 Backtrader 需要的数据格式
    """
    print("📝 创建示例 CSV 文件...")

    # 日期范围
    start_date = datetime(2023, 1, 1)
    dates = pd.date_range(start_date, periods=100, freq='D')

    # 生成随机价格数据
    price = 100.0
    prices = []

    for _ in range(100):
        change = random.uniform(-2, 2)
        price = max(price + change, 10)
        prices.append(price)

    # 创建 DataFrame
    df = pd.DataFrame({
        'datetime': dates,
        'open': [p * random.uniform(0.98, 1.02) for p in prices],
        'high': [p * random.uniform(1.0, 1.05) for p in prices],
        'low': [p * random.uniform(0.95, 1.0) for p in prices],
        'close': prices,
        'volume': [random.randint(1000, 10000) for _ in range(100)],
        'openinterest': [0] * 100
    })

    # 保存到 CSV
    csv_path = 'data/sample.csv'
    df.to_csv(csv_path, index=False)
    print(f"✓ CSV 文件已创建: {csv_path}")
    print(f"✓ 数据行数: {len(df)}")
    print(f"✓ 日期范围: {df['datetime'].min()} 到 {df['datetime'].max()}")

    return csv_path


class SimpleStrategy(bt.Strategy):
    """简单策略：价格低于 95 买入，高于 105 卖出"""

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'✅ 买入: 价格={order.executed.price:.2f}, ' +
                      f'数量={order.executed.size}')
            else:
                print(f'✅ 卖出: 价格={order.executed.price:.2f}, ' +
                      f'数量={order.executed.size}')
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.dataclose[0] < 95:
                self.order = self.buy(size=10)
                print(f'📈 {self.datas[0].datetime.date(0)}: ' +
                      f'买入信号, 价格={self.dataclose[0]:.2f}')
        else:
            if self.dataclose[0] > 105:
                self.order = self.sell(size=10)
                print(f'📉 {self.datas[0].datetime.date(0)}: ' +
                      f'卖出信号, 价格={self.dataclose[0]:.2f}')


def main():
    """主函数"""
    print("=" * 60)
    print("Backtrader CSV 数据加载示例")
    print("=" * 60)

    # 1. 创建示例 CSV 文件
    csv_path = create_sample_csv()

    # 2. 创建 Cerebro 引擎
    cerebro = bt.Cerebro()

    # 3. 添加策略
    cerebro.addstrategy(SimpleStrategy)

    # 4. 方式一：使用 CSVGeneralData 直接读取
    print("\n📂 使用 CSVGeneralData 加载...")
    data = bt.feeds.CSVGeneralData(
        dataname=csv_path,
        datetime=0,      # datetime 在第 0 列
        open=1,          # open 在第 1 列
        high=2,          # high 在第 2 列
        low=3,           # low 在第 3 列
        close=4,         # close 在第 4 列
        volume=5,        # volume 在第 5 列
        openinterest=6,  # openinterest 在第 6 列
    )

    # 方式二：使用 Pandas 读取后加载（推荐，更灵活）
    # print("\n📂 使用 Pandas 加载...")
    # df = pd.read_csv(csv_path)
    # df['datetime'] = pd.to_datetime(df['datetime'])
    # df.set_index('datetime', inplace=True)
    # data = bt.feeds.PandasData(dataname=df)

    cerebro.adddata(data)

    # 5. 设置初始资金
    initial_cash = 10000.0
    cerebro.broker.setcash(initial_cash)

    # 6. 设置手续费
    cerebro.broker.setcommission(commission=0.001)

    # 7. 运行回测
    print(f"\n💰 初始资金: {initial_cash:.2f}")
    print("-" * 60)
    cerebro.run()
    final_value = cerebro.broker.getvalue()
    print("-" * 60)
    print(f"💰 最终资金: {final_value:.2f}")
    print(f"📊 总收益: {final_value - initial_cash:.2f} " +
          f"({(final_value/initial_cash - 1)*100:.2f}%)")

    # 8. 绘制结果
    print("\n📈 正在生成图表...")
    cerebro.plot()
    print("✓ 完成！")


if __name__ == '__main__':
    main()
