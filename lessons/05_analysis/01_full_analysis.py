#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backtrader 完整回测分析示例

学习要点：
1. 使用各种 Analyzers 进行深度分析
2. 解读关键性能指标
3. 生成详细的回测报告
4. 识别策略优缺点
"""

import backtrader as bt
import pandas as pd
import random
from datetime import datetime


def generate_sample_data(days=500):
    """生成模拟数据"""
    start_date = datetime(2022, 1, 1)
    dates = pd.date_range(start_date, periods=days, freq='D')

    price = 100.0
    prices = []
    trend = 0
    trend_duration = 0

    for i in range(days):
        # 每 80 天切换一次趋势
        if trend_duration > 80:
            trend = random.uniform(-0.3, 0.3)
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


class TestStrategy(bt.Strategy):
    """测试用的双均线策略"""

    params = (
        ('fast_period', 10),
        ('slow_period', 30),
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(period=self.params.fast_period)
        self.slow_ma = bt.indicators.SMA(period=self.params.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        self.order = None
        self.buyprice = None

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buyprice = order.executed.price
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.crossover[0] > 0:
                self.order = self.buy(size=100)
        else:
            if self.crossover[0] < 0:
                self.order = self.sell(size=100)


def print_analysis(strat, initial_cash, final_cash):
    """打印详细的分析报告"""

    print("\n" + "="*70)
    print(" "*20 + "📊 回测分析报告")
    print("="*70)

    # ========== 资金分析 ==========
    print("\n💰 资金分析")
    print("-"*70)
    print(f"  初始资金:        {initial_cash:>15,.2f}")
    print(f"  最终资金:        {final_cash:>15,.2f}")
    print(f"  绝对收益:        {final_cash - initial_cash:>15,.2f}")
    print(f"  收益率:          {(final_cash/initial_cash - 1)*100:>14.2f}%")

    # ========== 收益分析 ==========
    returns = strat.analyzers.returns.get_analysis()
    if 'rtot' in returns:
        print("\n📈 收益分析")
        print("-"*70)
        print(f"  累计收益率:      {returns['rtot']:>14.2%}")
        if 'ravg' in returns:
            print(f"  平均日收益率:    {returns['ravg']:>14.2%}%")
        if 'rnorm' in returns:
            print(f"  年化收益率:      {returns['rnorm']:>14.2%}%")
        if 'rtot' in returns:
            # 计算月度收益
            monthly_return = (1 + returns['rtot']) ** (1/12) - 1
            print(f"  平均月收益率:    {monthly_return:>14.2f}%")

    # ========== 风险分析 ==========
    drawdown = strat.analyzers.drawdown.get_analysis()
    if 'max' in drawdown:
        print("\n📉 风险分析")
        print("-"*70)
        print(f"  最大回撤:        {drawdown['max']['drawdown']:>14.2f}%")
        print(f"  最大回撤金额:    {drawdown['max']['money']:>15,.2f}")
        print(f"  最大回撤持续:    {drawdown['max']['len']:>15} 天")
        print(f"  回撤次数:        {len([x for x in strat.analyzers.drawdown.get_analysis() if isinstance(x, dict)]):>15}")

    # ========== 夏普比率 ==========
    sharpe = strat.analyzers.sharpe.get_analysis()
    if 'sharperatio' in sharpe and sharpe['sharperatio'] is not None:
        print("\n📊 风险调整收益")
        print("-"*70)
        print(f"  夏普比率:        {sharpe['sharperatio']:>15.2f}")

        # 解读夏普比率
        if sharpe['sharperatio'] < 1:
            assessment = "表现不佳"
        elif sharpe['sharperatio'] < 1.5:
            assessment = "表现一般"
        elif sharpe['sharperatio'] < 2:
            assessment = "表现良好"
        elif sharpe['sharperatio'] < 3:
            assessment = "表现优秀"
        else:
            assessment = "表现极佳"
        print(f"  评估:            {assessment:>15}")

        # 计算卡尔玛比率
        if 'rnorm' in returns and 'max' in drawdown:
            calmar = abs(returns['rnorm'] / (drawdown['max']['drawdown'] / 100))
            print(f"  卡尔玛比率:      {calmar:>15.2f}")

    # ========== 交易分析 ==========
    trades = strat.analyzers.trades.get_analysis()
    if 'total' in trades:
        print("\n🔄 交易统计")
        print("-"*70)

        total_trades = trades['total']['total']
        won_trades = trades['won']['total'] if 'won' in trades else 0
        lost_trades = trades['lost']['total'] if 'lost' in trades else 0

        print(f"  总交易次数:      {total_trades:>15}")
        print(f"  盈利交易:        {won_trades:>15}")
        print(f"  亏损交易:        {lost_trades:>15}")

        if total_trades > 0:
            win_rate = (won_trades / total_trades) * 100
            print(f"  胜率:            {win_rate:>14.1f}%")

        # 盈利交易详情
        if 'won' in trades:
            won_stats = trades['won']
            print(f"\n  ✨ 盈利交易统计:")
            if 'len' in won_stats:
                print(f"     平均持仓天数:  {won_stats['len']['average']:>10.1f}")
            if 'pnl' in won_stats:
                print(f"     总盈利:        {won_stats['pnl']['total']:>10,.2f}")
                print(f"     平均盈利:      {won_stats['pnl']['average']:>10,.2f}")
                print(f"     最大盈利:      {won_stats['pnl']['max']:>10,.2f}")
                print(f"     最小盈利:      {won_stats['pnl']['min']:>10,.2f}")

        # 亏损交易详情
        if 'lost' in trades:
            lost_stats = trades['lost']
            print(f"\n  ⚠️  亏损交易统计:")
            if 'len' in lost_stats:
                print(f"     平均持仓天数:  {lost_stats['len']['average']:>10.1f}")
            if 'pnl' in lost_stats:
                print(f"     总亏损:        {lost_stats['pnl']['total']:>10,.2f}")
                print(f"     平均亏损:      {lost_stats['pnl']['average']:>10,.2f}")
                print(f"     最大亏损:      {lost_stats['pnl']['max']:>10,.2f}")
                print(f"     最小亏损:      {lost_stats['pnl']['min']:>10,.2f}")

        # 盈亏比
        if 'won' in trades and 'lost' in trades:
            avg_win = trades['won']['pnl']['average']
            avg_loss = abs(trades['lost']['pnl']['average'])
            if avg_loss > 0:
                profit_loss_ratio = avg_win / avg_loss
                print(f"\n  盈亏比:          {profit_loss_ratio:>15.2f}")

    # ========== SQN 指标 ==========
    if 'sqn' in dir(strat.analyzers):
        try:
            sqn = strat.analyzers.sqn.get_analysis()
            if 'sqn' in sqn:
                print("\n📊 系统质量数(SQN)")
                print("-"*70)
                print(f"  SQN:             {sqn['sqn']:>15.2f}")

                if sqn['sqn'] < 1.5:
                    assessment = "系统质量较差"
                elif sqn['sqn'] < 2:
                    assessment = "系统质量一般"
                elif sqn['sqn'] < 3:
                    assessment = "系统质量良好"
                else:
                    assessment = "系统质量优秀"
                print(f"  评估:            {assessment:>15}")
        except:
            pass

    # ========== 交易记录 ==========
    transactions = strat.analyzers.transactions.get_analysis()
    if transactions:
        print("\n📝 最近交易记录")
        print("-"*70)
        print(f"  {'日期':<12} {'类型':<6} {'价格':>10} {'数量':>8} {'金额':>12}")
        print("-"*70)

        # 只显示最近 10 笔交易
        recent_transactions = list(transactions)[-10:]
        for dte, txn_list in recent_transactions:
            for txn in txn_list:
                date_str = dte.strftime('%Y-%m-%d')
                typ = '买入' if txn[0] > 0 else '卖出'
                price = txn[1]
                size = abs(txn[0])
                value = price * size
                print(f"  {date_str:<12} {typ:<6} {price:>10.2f} {size:>8} {value:>12,.2f}")

    print("\n" + "="*70)


def run_analysis():
    """运行完整分析"""

    print("="*70)
    print(" "*20 + "Backtrader 完整回测分析")
    print("="*70)

    # 创建 Cerebro
    cerebro = bt.Cerebro()

    # 添加策略
    cerebro.addstrategy(TestStrategy)

    # 生成数据
    df = generate_sample_data()
    df_indexed = df.set_index('datetime')

    # 加载数据
    data = bt.feeds.PandasData(dataname=df_indexed)
    cerebro.adddata(data)

    # 设置资金
    initial_cash = 100000.0
    cerebro.broker.setcash(initial_cash)

    # 设置手续费
    cerebro.broker.setcommission(commission=0.001)

    # ========== 添加分析器 ==========
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.0)
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.Transactions, _name='transactions')

    # 添加观察者
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.DrawDown)
    cerebro.addobserver(bt.observers.BuySell)

    # 运行回测
    print(f"\n⏳ 正在运行回测...")
    strat = cerebro.run()[0]
    final_cash = cerebro.broker.getvalue()

    # 打印分析报告
    print_analysis(strat, initial_cash, final_cash)

    # 策略评估
    print("\n" + "="*70)
    print(" "*25 + "💡 策略评估")
    print("="*70)

    returns = strat.analyzers.returns.get_analysis()
    drawdown = strat.analyzers.drawdown.get_analysis()
    sharpe = strat.analyzers.sharpe.get_analysis()
    trades = strat.analyzers.trades.get_analysis()

    # 综合评估
    score = 0
    issues = []
    strengths = []

    # 收益率评估
    if 'rtot' in returns:
        if returns['rtot'] > 0.5:
            score += 2
            strengths.append("✓ 收益率优秀 (>50%)")
        elif returns['rtot'] > 0.2:
            score += 1
            strengths.append("✓ 收益率良好 (>20%)")
        elif returns['rtot'] < 0:
            issues.append("✗ 策略亏损")

    # 回撤评估
    if 'max' in drawdown:
        if drawdown['max']['drawdown'] < 10:
            score += 2
            strengths.append("✓ 回撤控制优秀 (<10%)")
        elif drawdown['max']['drawdown'] < 20:
            score += 1
            strengths.append("✓ 回撤控制良好 (<20%)")
        elif drawdown['max']['drawdown'] > 40:
            issues.append("✗ 回撤过大 (>40%)")

    # 夏普比率评估
    if 'sharperatio' in sharpe and sharpe['sharperatio'] is not None:
        if sharpe['sharperatio'] > 2:
            score += 2
            strengths.append("✓ 夏普比率优秀 (>2)")
        elif sharpe['sharperatio'] > 1:
            score += 1
            strengths.append("✓ 夏普比率良好 (>1)")
        elif sharpe['sharperatio'] < 0:
            issues.append("✗ 夏普比率为负")

    # 胜率评估
    if 'total' in trades and 'won' in trades:
        win_rate = trades['won']['total'] / trades['total']['total']
        if win_rate > 0.5:
            score += 1
            strengths.append(f"✓ 胜率: {win_rate*100:.1f}%")
        else:
            issues.append(f"✗ 胜率偏低: {win_rate*100:.1f}%")

    print("\n👍 优势:")
    if strengths:
        for s in strengths:
            print(f"  {s}")
    else:
        print("  无明显优势")

    print("\n⚠️  问题:")
    if issues:
        for i in issues:
            print(f"  {i}")
    else:
        print("  无明显问题")

    print(f"\n📊 综合评分: {score}/8")

    if score >= 6:
        print("  🌟 策略表现优秀，值得进一步研究！")
    elif score >= 4:
        print("  👍 策略表现良好，可以继续优化。")
    elif score >= 2:
        print("  ⚠️  策略表现一般，需要改进。")
    else:
        print("  ❌ 策略表现不佳，建议重新设计。")

    print("="*70)

    # 绘制图表
    print("\n📈 正在生成图表...")
    cerebro.plot(style='candlestick', barup='red', bardown='green')
    print("✓ 分析完成！")


if __name__ == '__main__':
    run_analysis()
