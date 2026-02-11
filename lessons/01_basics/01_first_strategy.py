#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backtrader 第一个策略：买入持有策略
这是学习 Backtrader 的 "Hello World"

学习要点：
1. Cerebro - 策略引擎
2. Strategy - 策略类定义
3. Data Feeds - 数据加载
4. 运行回测
"""

import backtrader as bt
import tushare as ts
import pandas as pd
import os
from datetime import datetime


# 第一步：定义策略类
class FirstStrategy(bt.Strategy):
    """
    第一个策略：简单的买入持有
    逻辑：第一天买入，一直持有到最后
    """

    def __init__(self):
        """初始化策略"""
        # 获取数据引用
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        # 记录订单状态
        self.order = None

    def next(self):
        """
        每个交易日都会调用这个方法
        这里编写你的交易逻辑
        """
        # 打印每日开盘价和收盘价
        print(f'{self.datas[0].datetime.date(0)} | 开盘价: {self.dataopen[0]:.2f} | 收盘价: {self.dataclose[0]:.2f}')

        # 如果没有持仓，买入
        if self.position.size == 0:
            # 买入 100 股
            self.order = self.buy(size=100)

    def notify_order(self, order):
        """订单状态回调 - 当订单成交时调用"""
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'\n✅ 买入成交')
                print(f'   日期: {self.datas[0].datetime.date(0)}')
                print(f'   成交价格: {order.executed.price:.2f}')
                print(f'   成交数量: {order.executed.size}')
                print(f'   成交金额: {order.executed.value:.2f}')
                print(f'   手续费: {order.executed.comm:.2f}')
                print(f'   剩余现金: {self.broker.getcash():.2f}')
                print(f'   总资产: {self.broker.getvalue():.2f}\n')


# 第二步：创建 Cerebro 引擎
def run_strategy():
    """运行策略"""

    # 创建 Cerebro 引擎
    cerebro = bt.Cerebro()

    # 添加策略
    cerebro.addstrategy(FirstStrategy)

    # 第三步：使用 tushare 获取数据
    # 注意：需要在 tushare 官网注册获取 token：https://tushare.pro/register
    # 设置 token：os.environ['TUSHARE_TOKEN'] = '你的token'
    # 或在代码中设置：ts.set_token('你的token')
    csv_path = 'data/000001_2023.csv'
    ts_code = '000001.SZ'  # 平安银行

    # 检查本地缓存
    if os.path.exists(csv_path):
        print('📂 使用本地缓存数据...')
        df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    else:
        # 获取 token（优先从环境变量读取）
        token = os.environ.get('TUSHARE_TOKEN')
        if not token:
            print('❌ 错误：未找到 TUSHARE_TOKEN')
            print('请先设置 token：')
            print('  方式1：设置环境变量：set TUSHARE_TOKEN=你的token')
            print('  方式2：在代码中添加：ts.set_token("你的token")')
            print('\n注册地址：https://tushare.pro/register')
            return

        # 初始化 tushare
        ts.set_token(token)
        pro = ts.pro_api()

        print(f'📡 正在从 tushare 获取 {ts_code} 数据...')

        # 获取日线数据
        df = pro.daily(
            ts_code=ts_code,
            start_date='20230101',
            end_date='20231231'
        )

        if df.empty:
            print(f'❌ 未获取到数据，请检查网络连接和 token 是否有效')
            return

        # 转换日期格式并排序
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        df = df.sort_values('trade_date')
        df.set_index('trade_date', inplace=True)

        # 重命名列以适配 Backtrader
        df.rename(columns={
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'vol': 'volume'
        }, inplace=True)

        # 保存到本地
        os.makedirs('data', exist_ok=True)
        df.to_csv(csv_path)
        print(f'✓ 数据已保存到 {csv_path}')

    print(f'✓ 数据行数: {len(df)}')

    # 确保列名是小写（Backtrader 要求）
    df.columns = [c.lower() for c in df.columns]

    # 加载数据到 Cerebro
    data = bt.feeds.PandasData(
        dataname=df,
        datetime=None,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        openinterest=6
    )
    cerebro.adddata(data)

    # 第四步：设置初始资金
    cerebro.broker.setcash(10000.0)

    # 第五步：设置交易手续费（万分之一）
    cerebro.broker.setcommission(commission=0.0001)

    # 第六步：运行回测
    print('初始资金: %.2f' % cerebro.broker.getvalue())
    result = cerebro.run()
    print('最终资金: %.2f' % cerebro.broker.getvalue())

    # 第七步：绘制结果
    cerebro.plot()


if __name__ == '__main__':
    run_strategy()
