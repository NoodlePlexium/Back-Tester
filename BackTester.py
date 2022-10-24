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
    riskFreeReturn = 22
    
    # Strategy Settings
    riskReward = 1
    commission = 0.06

    # Indicator Settings

    # OHLC Arrays
    open = data['open']
    high = data['high']
    low = data['low']
    close = data['close']
    
    # Pandas TA Indicators

    # Commision
    commission = commission/100

    # Enter Trade
    def Enter(side, qty, entryPrice, tp, sl):
        global tradeCount
        global equity

        tradeCount+=1
        equity -= (commission)*math.floor(equity*entryPrice)/entryPrice  
        openTrades.append({'direction' : side, 'tradeID' : tradeCount, 'quantity' : qty, 'entry price' : entryPrice, 'tp' : tp, 'sl' : sl})
        print(f"{side} #{tradeCount} | ${entryPrice} per {symbol} | Qty ${qty}")

    # Exit Trade
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
              
    # Interate throught the dataframe
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

        # Custon trade entry conditions ---------------------------------------------------------- 
        longCondition = False
        shortCondition = False

        # Enter long
        if longCondition:

            # Calculate TP & SL
            sl = close[i] * 0.9
            tp = close[i] * 1.1

            # Trade Size
            qty = math.floor((equity*close[i]))

            Enter('long', qty, close[i], tp, sl, _commision)


        # Enter short
        if shortCondition:

            # Calculate TP & SL
            sl = close[i] * 1.1
            tp = close[i] * 0.9
            
            # Trade Size
            qty = math.floor((equity*close[i]))

            Enter('short', qty, close[i], tp, sl, _commision) 

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

    # Plot equity
    plt.plot(equityCurve)
    plt.show()

BackTest()
