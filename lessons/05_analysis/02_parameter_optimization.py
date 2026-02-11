#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backtrader 参数优化示例

学习要点：
1. 使用 optstrategy 进行参数优化
2. 避免过拟合
3. 样本内外测试
4. 选择最优参数组合
"""

import backtrader as bt
import pandas as pd
import random
from datetime import datetime
from itertools import product


def generate_sample_data(days=500):
    """生成模拟数据"""
    start_date = datetime(2022, 1, 1)
    dates = pd.date_range(start_date, periods=days, freq='D')

    price = 100.0
    prices = []
    trend = 0
    trend_duration = 0

    for i in range(days):
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


class DualMAStrategy(bt.Strategy):
    """双均线策略（带参数）"""

    params = (
        ('fast_period', 10),
        ('slow_period', 30),
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(period=self.params.fast_period)
        self.slow_ma = bt.indicators.SMA(period=self.params.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Completed]:
            pass
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


def simple_optimization():
    """使用 Backtrader 内置优化功能"""

    print("=" * 70)
    print(" "*15 + "参数优化：Backtrader 内置方法")
    print("=" * 70)

    # 生成数据
    df = generate_sample_data()
    df_indexed = df.set_index('datetime')

    # 创建 Cerebro
    cerebro = bt.Cerebro()

    # 添加策略（带参数优化）
    cerebro.optstrategy(
        DualMAStrategy,
        fast_period=range(5, 15, 5),    # 5, 10
        slow_period=range(20, 50, 10),   # 20, 30, 40
    )

    # 加载数据
    data = bt.feeds.PandasData(dataname=df_indexed)
    cerebro.adddata(data)

    # 设置资金和手续费
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)

    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

    # 运行优化
    print("\n⏳ 正在优化参数...")
    print("   快线周期: [5, 10]")
    print("   慢线周期: [20, 30, 40]")
    print("   组合数量: 6\n")

    results = cerebro.run(maxcpu=1)  # maxcpu=1 避免多进程问题

    # 分析结果
    print("\n" + "="*70)
    print(" "*20 + "优化结果汇总")
    print("="*70)
    print(f"\n{'快线':<8} {'慢线':<8} {'最终资金':>12} {'收益率':>10} {'夏普比率':>10} {'最大回撤':>10}")
    print("-"*70)

    best_return = -float('inf')
    best_sharpe = -float('inf')
    best_config_return = None
    best_config_sharpe = None

    for strat in results:
        fast = strat.params.fast_period
        slow = strat.params.slow_period

        final_value = cerebro.broker.getvalue()
        ret = strat.analyzers.returns.get_analysis()
        sharpe = strat.analyzers.sharpe.get_analysis()
        drawdown = strat.analyzers.drawdown.get_analysis()

        total_return = ret.get('rtot', 0)
        sharpe_ratio = sharpe.get('sharperatio', None)
        max_dd = drawdown.get('max', {}).get('drawdown', 0)

        print(f"{fast:<8} {slow:<8} {final_value:>10,.0f} {total_return:>9.2%} ", end="")
        if sharpe_ratio is not None:
            print(f"{sharpe_ratio:>10.2f} ", end="")
        else:
            print(f"{'N/A':>10} ", end="")
        print(f"{max_dd:>9.2f}%")

        # 记录最优配置
        if total_return > best_return:
            best_return = total_return
            best_config_return = (fast, slow, final_value, sharpe_ratio, max_dd)

        if sharpe_ratio is not None and sharpe_ratio > best_sharpe:
            best_sharpe = sharpe_ratio
            best_config_sharpe = (fast, slow, final_value, total_return, max_dd)

    print("\n" + "="*70)
    print("🏆 最优参数组合（按收益率）")
    print("-"*70)
    if best_config_return:
        print(f"  快线周期: {best_config_return[0]}")
        print(f"  慢线周期: {best_config_return[1]}")
        print(f"  最终资金: {best_config_return[2]:,.2f}")
        print(f"  收益率:   {best_config_return[3]:.2%}")
        print(f"  夏普比率: {best_config_return[4]:.2f}")
        print(f"  最大回撤: {best_config_return[5]:.2f}%")

    print("\n" + "="*70)
    print("🏆 最优参数组合（按夏普比率）")
    print("-"*70)
    if best_config_sharpe:
        print(f"  快线周期: {best_config_sharpe[0]}")
        print(f"  慢线周期: {best_config_sharpe[1]}")
        print(f"  最终资金: {best_config_sharpe[2]:,.2f}")
        print(f"  夏普比率: {best_config_sharpe[3]:.2f}")
        print(f"  收益率:   {best_config_sharpe[4]:.2%}")
        print(f"  最大回撤: {best_config_sharpe[5]:.2f}%")

    print("="*70)


def custom_optimization():
    """自定义优化循环（更灵活）"""

    print("\n\n" + "=" * 70)
    print(" "*15 + "参数优化：自定义方法")
    print("=" * 70)

    # 生成数据
    df = generate_sample_data()
    df_indexed = df.set_index('datetime')

    # 定义参数范围
    fast_range = [5, 10, 15]
    slow_range = [20, 30, 40, 50]

    # 所有可能的组合
    param_combinations = list(product(fast_range, slow_range))

    print(f"\n⏳ 测试 {len(param_combinations)} 种参数组合...\n")

    results = []

    for fast, slow in param_combinations:
        if fast >= slow:  # 跳过无效组合
            continue

        # 创建 Cerebro
        cerebro = bt.Cerebro()

        # 添加策略
        cerebro.addstrategy(DualMAStrategy, fast_period=fast, slow_period=slow)

        # 加载数据
        data = bt.feeds.PandasData(dataname=df_indexed)
        cerebro.adddata(data)

        # 设置
        cerebro.broker.setcash(100000.0)
        cerebro.broker.setcommission(commission=0.001)

        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

        # 运行
        strat = cerebro.run()[0]

        # 获取结果
        ret = strat.analyzers.returns.get_analysis()
        sharpe = strat.analyzers.sharpe.get_analysis()
        drawdown = strat.analyzers.drawdown.get_analysis()
        trades = strat.analyzers.trades.get_analysis()

        total_return = ret.get('rtot', 0)
        sharpe_ratio = sharpe.get('sharperatio', 0)
        max_dd = drawdown.get('max', {}).get('drawdown', 0)
        total_trades = trades.get('total', {}).get('total', 0)

        results.append({
            'fast': fast,
            'slow': slow,
            'return': total_return,
            'sharpe': sharpe_ratio if sharpe_ratio else 0,
            'drawdown': max_dd,
            'trades': total_trades
        })

    # 排序结果
    results_by_return = sorted(results, key=lambda x: x['return'], reverse=True)
    results_by_sharpe = sorted(results, key=lambda x: x['sharpe'], reverse=True)

    # 打印前 10 名
    print("\n" + "="*70)
    print(" "*25 + "🏆 Top 10（按收益率）")
    print("="*70)
    print(f"\n{'排名':<6} {'快线':<6} {'慢线':<6} {'收益率':>10} {'夏普':>8} {'回撤':>8} {'交易数':>8}")
    print("-"*70)

    for i, r in enumerate(results_by_return[:10], 1):
        print(f"{i:<6} {r['fast']:<6} {r['slow']:<6} {r['return']:>9.2%} "
              f"{r['sharpe']:>8.2f} {r['drawdown']:>7.1f}% {r['trades']:>8}")

    print("\n" + "="*70)
    print(" "*25 + "🏆 Top 10（按夏普比率）")
    print("="*70)
    print(f"\n{'排名':<6} {'快线':<6} {'慢线':<6} {'夏普':>8} {'收益率':>10} {'回撤':>8} {'交易数':>8}")
    print("-"*70)

    for i, r in enumerate(results_by_sharpe[:10], 1):
        print(f"{i:<6} {r['fast']:<6} {r['slow']:<6} {r['sharpe']:>8.2f} "
              f"{r['return']:>9.2%} {r['drawdown']:>7.1f}% {r['trades']:>8}")

    print("="*70)


def walk_forward_analysis():
    """样本内外测试示例（Walk Forward）"""

    print("\n\n" + "=" * 70)
    print(" "*20 + "样本内外测试（Walk Forward）")
    print("=" * 70)

    # 生成数据
    df = generate_sample_data(days=600)
    total_days = len(df)

    # 定义训练和测试窗口
    train_days = 300  # 训练期
    test_days = 100   # 测试期

    print(f"\n总数据: {total_days} 天")
    print(f"训练期: {train_days} 天")
    print(f"测试期: {test_days} 天")
    print(f"滚动次数: {(total_days - train_days) // test_days}\n")

    windows = []
    start = 0

    while start + train_days + test_days <= total_days:
        train_start = start
        train_end = start + train_days
        test_start = train_end
        test_end = test_start + test_days

        windows.append({
            'train_start': train_start,
            'train_end': train_end,
            'test_start': test_start,
            'test_end': test_end
        })

        start += test_days

    print(f"将进行 {len(windows)} 轮 Walk Forward 测试\n")
    print("="*70)

    # 简化演示：只做第一轮
    if len(windows) > 0:
        window = windows[0]

        print(f"\n第 1 轮:")
        print(f"  训练期: 第 {window['train_start']} - {window['train_end']} 天")
        print(f"  测试期: 第 {window['test_start']} - {window['test_end']} 天")

        # 这里应该实现完整的 Walk Forward 逻辑
        # 为了简洁，仅做概念演示
        print("\n💡 Walk Forward 分析步骤:")
        print("  1. 在训练期数据上优化参数")
        print("  2. 选择最优参数组合")
        print("  3. 在测试期数据上验证性能")
        print("  4. 滚动窗口，重复 1-3")
        print("  5. 统计所有测试期的平均表现")

    print("\n" + "="*70)


def main():
    """主函数"""
    print("\n")
    print("█" * 70)
    print("█" + " "*20 + "参数优化教程" + " "*20 + "█")
    print("█" * 70)

    # 运行不同类型的优化
    simple_optimization()
    custom_optimization()
    walk_forward_analysis()

    # 优化建议
    print("\n\n" + "="*70)
    print(" "*20 + "💡 参数优化建议")
    print("="*70)

    print("""
1. 避免过拟合
   - 不要优化太多参数（建议不超过 3 个）
   - 参数范围要合理，不要过于精确
   - 优先选择参数空间中的"稳健区域"

2. 样本内外测试
   - 70% 数据用于训练（优化）
   - 30% 数据用于验证（测试）
   - 或使用 Walk Forward 分析

3. 考虑交易成本
   - 优化时必须包含手续费
   - 避免过度交易（参数敏感）

4. 选择稳健参数
   - 不要只选收益率最高的
   - 综合考虑夏普比率、最大回撤
   - 选择参数曲线"平坦"的区域

5. 实盘前验证
   - 模拟盘测试至少 1-3 个月
   - 小资金实盘验证
   - 逐步扩大资金规模

6. 定期重新优化
   - 市场环境变化，参数可能失效
   - 建议每 3-6 个月重新评估
    """)

    print("="*70)
    print("\n✓ 优化完成！")


if __name__ == '__main__':
    main()
