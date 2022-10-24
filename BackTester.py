from statistics import stdev
import pandas as pd
import numpy as np
import pandas_ta as ta
import matplotlib.pyplot as plt
import math
import exchanges.Bybit_History as h

# Back Test Settings
symbol = 'BTC-PERP'

dataString = 'HistoricalData/'+symbol+'.csv'
data = pd.read_csv(dataString)

# Execution Functions
def BackTest():

    # Variables
    global tradeCount
    global equityStart
    global equity
    global profits
    global winCount
    global profit

    # Initialize
    tradeCount = 0
    equityStart = 1
    equity = equityStart
    profits = []
    winCount = 0
    profit = 0
    equityCurve = [equityStart]
    openTrades=[]
    riskFreeReturn = 25

    open = data['open']
    high = data['high']
    low = data['low']
    close = data['close']
    
    # Strategy Settings
    riskReward = 2
    stopMultiplier = 0.7
    commission = 0.06

    stoc_length = 20
    k_length = 5
    d_length = 2

    band = 8

    # Indicators
    ma = data.ta.ema(length=25)
    ma_slow = data.ta.ema(length=100)

    rsi = data.ta.rsi(length=12)
    stoc = ta.stoch(rsi, rsi, rsi, smooth_k=k_length, k=stoc_length, d=d_length).reset_index()
    suffix = str(stoc_length)+'_'+str(d_length)+'_'+str(k_length)

    k = stoc['STOCHk_'+suffix]
    d = stoc['STOCHd_'+suffix]

    atr = data.ta.atr(lenth=20)

    commission = commission/100

    # Trade Functions
    def Enter(side, qty, entryPrice, tp, sl, commission):
        global tradeCount
        global equity

        tradeCount+=1
        equity -= commission  
        openTrades.append({'direction' : side, 'tradeID' : tradeCount, 'quantity' : qty, 'entry price' : entryPrice, 'tp' : tp, 'sl' : sl})
        print(f"{side} #{tradeCount} | ${entryPrice} per {symbol} | Qty ${qty}")

    def Exit(trade):
        global profits
        global equity
        global winCount

        if trade['direction'] == 'long':
            if high[i] >= trade['tp']:
                profit = ((trade['tp']-trade['entry price'])*trade['quantity']/trade['tp'] - (commission)*trade['quantity'])/trade['tp']
                print(f"exit #{trade['tradeID']} | ${close[i]} per {symbol} | Profit: +{profit}\n")
            elif low[i] <= trade['sl']: 
                profit = ((trade['sl']-trade['entry price'])*trade['quantity']/trade['sl'] - (commission)*trade['quantity'])/trade['sl']
                print(f"exit #{trade['tradeID']} | ${close[i]} per {symbol} | Loss: {profit}\n")    
        else:
            if low[i] <= trade['tp']:
                profit = ((trade['entry price']-trade['tp'])*trade['quantity']/trade['tp'] - (commission)*trade['quantity'])/trade['tp']
                print(f"exit  #{trade['tradeID']} | ${close[i]} per {symbol} | Profit: +{profit}\n") 
            elif high[i] >= trade['sl']:
                profit = ((trade['entry price']-trade['sl'])*trade['quantity']/trade['sl'] - (commission)*trade['quantity'])/trade['sl']
                print(f"exit  #{trade['tradeID']} | ${close[i]} per {symbol} | Loss: {profit}\n")

        if profit > 0: winCount+=1
        profits.append(profit)
        equity += profit
        equityCurve.append(equity) 
              
    # Interate Through Each Candle
    for i in range(1,len(k)):

        # Exit trades
        for trade in openTrades:
            exit = False

            if trade['direction']=='long':
                if high[i] >= trade['tp']:
                    exit = True
                    Exit(trade) 
                if low[i] <= trade['sl']:
                    exit = True
                    Exit(trade)

            if trade['direction']=='short':
                if low[i] <= trade['tp']:
                    exit = True
                    Exit(trade)   
                if high[i] >= trade['sl']:
                    exit = True
                    Exit(trade)
                    
            if exit == True: openTrades.remove(trade)    

        stoc_long = k[i-1]<d[i-1] and k[i]>d[i] and k[i-1]<band and d[i-1]<band
        stoc_short = k[i-1]>d[i-1] and k[i]<d[i] and k[i-1]>100-band and d[i-1]>100-band 

        longCondition = stoc_long and close[i]>ma[i] and close[i]>ma_slow[i] and ma[i]>ma_slow[i] and len(openTrades) == 0
        shortCondition = stoc_short and close[i]<ma[i] and close[i]<ma_slow[i] and ma[i]<ma_slow[i] and len(openTrades) == 0

        # Enter a buy trade
        if longCondition:
            tradeCount+=1
            stopSize = atr[i] * stopMultiplier
            sl = low[i] - stopSize
            longStopDist = close[i] - sl
            tp = close[i] + longStopDist * riskReward

            # Entry Commision
            _commision = (commission)*math.floor(equity*close[i])/close[i]  
            qty = math.floor((equity*close[i]))

            Enter('long', qty, close[i], tp, sl, _commision)


        # Enter a sell trade
        if shortCondition:
            tradeCount+=1
            stopSize = atr[i] * stopMultiplier
            sl = high[i] + stopSize
            shortStopDist = sl - close[i]
            tp = close[i] - shortStopDist * riskReward

            # Entry Commision
            _commision = (commission)*math.floor(equity*close[i])/close[i]  
            qty = math.floor((equity*close[i]))

            Enter('short', qty, close[i], tp, sl, _commision)

        if equity < 0.85*equityStart:
            print("\nAccount Dropped below 85% of principle")
            break     

    # Calculate Results
    profit = equity - equityStart

    # Sharpe Ratio
    st_dev = np.std(equityCurve)
    sharpeRatio = (profit-(((1+riskFreeReturn/100)*equityStart)-equityStart))/st_dev

    # Drawdown
    drawdownCurve = []
    max = 0
    maxDrawdown = 0
    for i in range(len(equityCurve)):  
        if equityCurve[i] > max:
            max = equityCurve[i]
        drawdown = 1-(max - equityCurve[i])/max   
        if 1-drawdown > maxDrawdown:
            maxDrawdown = 1-drawdown 
        drawdownCurve.append(drawdown)  

    # Report Backtest Results
    print(f"\nNumber of Trades: {tradeCount}")
    print(f"Profit: {profit}")
    print(f"Equity: {equity}\n")
    print(f"Profitable Trades: {winCount}")
    print(f"Percentage Profitable: {round((winCount/tradeCount)*100,2)}%\n")
    print(f"Sharpe Ratio: {sharpeRatio}")
    print(f"Max Drawdown: {maxDrawdown*100}%")  

    plt.plot(equityCurve)
    plt.show()

BackTest()
