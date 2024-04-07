# Vegas tunnel strategy
'''
    Youtube: https://www.youtube.com/watch?v=FxnBlJMD7Qw&t=68s

    Long Signal:
    1. EMA 144 > EMA 576 and EMA 676
    2. EMA 169 > EMA 576 and EMA 676
    3. EMA 12 > EMA 144 and EMA 169
    4. (Stock price < EMA 144 && Stock price > EMA 169) || (Stock price > EMA 144 && Stock price < EMA 169)  

    Stop loss:
    1. Stock price < EMA 144 && Stock price > EMA 169 and volume osc > 144
    2. Accelerated dip in 24 hours
    3. After 24 hours Stock price < EMA 144 && Stock price < EMA 169
    4. Stop loss at recent lowest price
    5. Sock price < EMA 676 (when buy)

    Stop gain:
    1. 1:1 (current price - buy price) == (Buy price - EMA 676 (when buy))
    2. 1:3 (current price - buy price) == 3 (Buy price - EMA 676 (when buy))
'''
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from StockHLOC import StockHLOC
import backtrader as bt
import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])


module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)

from backtrader.indicators import SumN, TrueLow, TrueRange

class VolumeOscillator(bt.Indicator):
    lines = ('volume_oscillator',)

    params = (
        ('short_period', 1),
        ('long_period', 14)
    )

    def __init__(self):
        short_sma = bt.ind.SMA(self.data.volume, period=self.params.short_period)
        long_sma = bt.ind.SMA(self.data.volume, period=self.params.long_period)

        self.l.volume_oscillator = short_sma - long_sma

class MyStrategy(bt.Strategy):

    params = (
        ("ema1_period", 144),
        ("ema2_period", 169),
        ("ema3_period", 575),
        ("ema4_period", 676),
        ("ema5_period", 12),
        ("interval", 60)
    )
    
    def __init__(self):
        # self.dataclose = self.datas[0].close
        # self.open = self.datas[0].open
        self.ema1 = bt.ind.EMA(self.data.close, period=self.params.ema1_period)
        self.ema2 = bt.ind.EMA(self.data.close, period=self.params.ema2_period)
        self.ema3 = bt.ind.EMA(self.data.close, period=self.params.ema3_period)
        self.ema4 = bt.ind.EMA(self.data.close, period=self.params.ema4_period)
        self.ema5 = bt.ind.EMA(self.data.close, period=self.params.ema5_period)
        self.interval = self.params.interval
        self.volume_osc = VolumeOscillator(self.data)


    def log(self, txt, dt=None):
        pass

    def next(self):
        volume_osc = self.volume_osc[0]
        current_ema1 = self.ema1[0]
        current_ema2 = self.ema2[0]
        current_ema3 = self.ema3[0]
        current_ema4 = self.ema4[0]
        current_ema5 = self.ema5[0]
        current_volume_osc = self.volume_osc[0]
        current_price = self.data.close[0]
        if self.position:
            # Stop loss
            if (current_price < current_ema1 and current_price > current_ema2 and
                current_volume_osc > 144) or (current_price < current_ema1 and current_price < current_ema2) or (current_price < self.stop_loss_price):
                self.sell()

            # Stop gain
            if (current_price - self.buy_price) == (self.buy_price - current_ema4):
                self.sell()
            elif (current_price - self.buy_price) == 2 * (self.buy_price - current_ema4):
                self.sell()

        else:
            # No position:
            if (current_ema1 > current_ema3 and current_ema1 > current_ema4 and
                current_ema2 > current_ema3 and current_ema2 > current_ema4 and
                current_ema5 > current_ema1 and current_ema5 > current_ema2 and
                ((current_price < current_ema1 and current_price > current_ema2) or
                 (current_price > current_ema1 and current_price < current_ema2))):
                
                self.buy()
                stop_loss_window = 24 # (24 * 60 / self.interval) 
                self.stop_loss_price = min(self.data.close.get(size=stop_loss_window))
                self.stop_gain_price = (current_price - self.stop_loss_price) * 3
                self.buy_price = current_price
            
if __name__ == '__main__':
    modpath = os.path.dirname(os.path.abspath('../data/BTC_30mins_2y_parsed.CSV'))
    datapath = os.path.join(modpath, 'BTC_30mins_2y_parsed.CSV')

    data = StockHLOC(
        dataname=datapath,
        name="SPY_30mins_2y_parsed",
        datetime=0,
        high=2,
        low=3,
        open=4,
        close=5,
        volume=6,
        timeframe=bt.TimeFrame.Minutes,
        compression=15
    )
    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.addstrategy(MyStrategy)
    cerebro.broker.setcash(300_000.0)
    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    plot_path = 'vegas_tunnel_strategy_plot.png'
    cerebro.plot(iplot=False, savefig=plot_path)