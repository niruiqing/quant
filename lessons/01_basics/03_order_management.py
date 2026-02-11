#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backtrader 订单管理详解

学习要点：
1. 订单状态生命周期
2. 订单类型（市价单、限价单、停止单）
3. notify_order 和 notify_trade 回调
4. 如何追踪订单和交易
"""

import backtrader as bt
import pandas as pd
import random
from datetime import datetime


def generate_sample_data():
    """生成模拟数据"""
    start_date = datetime(2023, 1, 1)
    dates = pd.date_range(start_date, periods=100, freq='D')

    price = 100.0
    prices = []

    for _ in range(100):
        change = random.uniform(-2, 2)
        price = max(price + change, 10)
        prices.append(price)

    df = pd.DataFrame({
        'datetime': dates,
        'open': [p * random.uniform(0.98, 1.02) for p in prices],
        'high': [p * random.uniform(1.0, 1.05) for p in prices],
        'low': [p * random.uniform(0.95, 1.0) for p in prices],
        'close': prices,
        'volume': [random.randint(1000, 10000) for _ in range(100)],
        'openinterest': [0] * 100
    })

    return df


class OrderManagementStrategy(bt.Strategy):
    """
    订单管理策略示例
    演示各种订单操作和回调方法
    """

    def __init__(self):
        """初始化"""
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low

        # 订单追踪
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # 交易统计
        self.trades_count = 0
        self.wins = 0
        self.losses = 0

    def notify_order(self, order):
        """
        订单状态变化回调

        订单状态：
        - Created: 订单已创建
        - Submitted: 订单已提交
        - Accepted: 订单被接受
        - Partial: 部分成交
        - Completed: 完全成交
        - Cancelled: 已取消
        - Expired: 已过期
        - Margin: 保证金不足
        - Rejected: 被拒绝
        """
        if order.status in [order.Submitted, order.Accepted]:
            # 订单已提交或被接受，等待成交
            return

        if order.status in [order.Completed]:
            # 订单成交
            if order.isbuy():
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm

                print(f'\n{"="*50}')
                print(f'✅ 买入订单成交')
                print(f'{"="*50}')
                print(f'📅 日期: {self.datas[0].datetime.date(0)}')
                print(f'💰 成交价格: {order.executed.price:.2f}')
                print(f'📊 成交数量: {order.executed.size:.0f}')
                print(f'💵 成交金额: {order.executed.value:.2f}')
                print(f'💸 手续费: {order.executed.comm:.2f}')
                print(f'💼 剩余现金: {self.broker.getcash():.2f}')
                print(f'📈 总资产: {self.broker.getvalue():.2f}')
                print(f'{"="*50}\n')

            else:  # 卖出
                print(f'\n{"="*50}')
                print(f'✅ 卖出订单成交')
                print(f'{"="*50}')
                print(f'📅 日期: {self.datas[0].datetime.date(0)}')
                print(f'💰 成交价格: {order.executed.price:.2f}')
                print(f'📊 成交数量: {order.executed.size:.0f}')
                print(f'💵 成交金额: {order.executed.value:.2f}')
                print(f'💸 手续费: {order.executed.comm:.2f}')
                print(f'💼 剩余现金: {self.broker.getcash():.2f}')
                print(f'📈 总资产: {self.broker.getvalue():.2f}')

                # 计算盈亏
                pnl = (order.executed.price - self.buyprice) * order.executed.size
                pnl_net = pnl - order.executed.comm - self.buycomm

                print(f'\n📊 交易盈亏:')
                print(f'   买入价格: {self.buyprice:.2f}')
                print(f'   卖出价格: {order.executed.price:.2f}')
                print(f'   毛盈亏: {pnl:.2f}')
                print(f'   净盈亏: {pnl_net:.2f} (含手续费)')

                if pnl_net > 0:
                    self.wins += 1
                    print(f'   ✨ 盈利交易！')
                else:
                    self.losses += 1
                    print(f'   ⚠️ 亏损交易')

                print(f'{"="*50}\n')

        elif order.status in [order.Cancelled]:
            print(f'❌ 订单已取消')

        elif order.status in [order.Margin]:
            print(f'❌ 保证金不足，订单无法执行')

        elif order.status in [order.Rejected]:
            print(f'❌ 订单被拒绝')

        elif order.status in [order.Expired]:
            print(f'⏰ 订单已过期')

        # 重置订单引用
        self.order = None

    def notify_trade(self, trade):
        """
        交易完成回调

        trade 对象在每次完整的买入-卖出周期后触发
        """
        if not trade.isclosed:
            return

        self.trades_count += 1

        print(f'\n🔄 交易周期 #{self.trades_count} 完成')
        print(f'   毛盈亏: {trade.pnl:.2f}')
        print(f'   净盈亏: {trade.pnlcomm:.2f}')
        print(f'   手续费: {trade.comm:.2f}')
        print(f'   胜率: {self.wins/(self.wins+self.losses)*100:.1f}% ' +
              f'({self.wins}胜{self.losses}负)')

    def next(self):
        """每个交易日调用"""
        # 如果有待处理的订单，等待成交
        if self.order:
            return

        # 如果没有持仓
        if not self.position:
            # 价格低于 95，买入
            if self.dataclose[0] < 95:
                # 市价单买入（默认）
                self.order = self.buy(size=10)
                print(f'📈 {self.datas[0].datetime.date(0)}: ' +
                      f'发出市价买入信号, 价格={self.dataclose[0]:.2f}')

            # 也可以使用限价单
            # elif self.dataclose[0] > 90:
            #     # 限价单：只在价格 <= 92 时买入
            #     self.order = self.buy(size=10, price=92, exectype=bt.Order.Limit)
            #     print(f'📈 发出限价买入信号, 限价=92, 当前价格={self.dataclose[0]:.2f}')

        else:
            # 已持仓，价格高于 105，卖出
            if self.dataclose[0] > 105:
                self.order = self.sell(size=10)
                print(f'📉 {self.datas[0].datetime.date(0)}: ' +
                      f'发出卖出信号, 价格={self.dataclose[0]:.2f}')


def main():
    """主函数"""
    print("=" * 60)
    print("Backtrader 订单管理示例")
    print("=" * 60)

    # 1. 生成数据
    print("\n📊 生成模拟数据...")
    df = generate_sample_data()
    df_indexed = df.set_index('datetime')

    # 2. 创建 Cerebro 引擎
    cerebro = bt.Cerebro()

    # 3. 添加策略
    cerebro.addstrategy(OrderManagementStrategy)

    # 4. 加载数据
    data = bt.feeds.PandasData(dataname=df_indexed)
    cerebro.adddata(data)

    # 5. 设置初始资金
    initial_cash = 10000.0
    cerebro.broker.setcash(initial_cash)

    # 6. 设置手续费（0.1%）
    cerebro.broker.setcommission(commission=0.001)

    # 7. 添加观察者
    cerebro.addobserver(bt.observers.Trades)      # 交易观察者
    cerebro.addobserver(bt.observers.DrawDown)    # 回撤观察者

    # 8. 运行回测
    print(f"\n💰 初始资金: {initial_cash:.2f}")
    print("-" * 60)
    strat = cerebro.run()
    final_value = cerebro.broker.getvalue()
    print("-" * 60)

    # 9. 打印最终统计
    print(f'\n{"="*60}')
    print(f'📊 回测总结')
    print(f'{"="*60}')
    print(f'💰 初始资金: {initial_cash:.2f}')
    print(f'💰 最终资金: {final_value:.2f}')
    print(f'📈 总收益: {final_value - initial_cash:.2f} ' +
          f'({(final_value/initial_cash - 1)*100:.2f}%)')
    print(f'🔄 交易次数: {strat[0].trades_count}')
    print(f'✨ 盈利交易: {strat[0].wins}')
    print(f'⚠️ 亏损交易: {strat[0].losses}')
    if strat[0].wins + strat[0].losses > 0:
        print(f'📊 胜率: {strat[0].wins/(strat[0].wins+strat[0].losses)*100:.1f}%')
    print(f'{"="*60}')

    # 10. 绘制结果
    print("\n📈 正在生成图表...")
    cerebro.plot(style='candlestick', barup='red', bardown='green')
    print("✓ 完成！")


if __name__ == '__main__':
    main()
