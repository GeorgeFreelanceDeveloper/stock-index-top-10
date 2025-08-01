# region imports
from AlgorithmImports import *
import datetime
# endregion

## Trend follow strategy selecting the top 10 companies from the stock index with weekly/monthly rebalancing equally weighted.
class StockIndexTop10_V1(QCAlgorithm):

    INDEXES = {
            "S&P500": ["NVDA","MSFT","AAPL","AMZN","META","AVGO","GOOGL","BRK.B","TSLA", "GOOG"], # https://finance.yahoo.com/quote/SPY/holdings/
            "NASDAQ100":["NVDA","MSFT","AAPL","AMZN","AVGO","META","NFLX","TSLA","COST","GOOGL"], # https://finance.yahoo.com/quote/QQQ/holdings/
            "S&P500 MOMENTUM": ["NVDA","META","AMZN","AVGO","JPM","TSLA","WMT","NFLX","PLTR","COST"] # https://finance.yahoo.com/quote/SPMO/holdings/ 
        }

    def initialize(self):

        # ********************************
        # User defined inputs
        # ********************************
        index = self.get_parameter("index", "S&P500 MOMENTUM")
        rebalancing_frequency = self.get_parameter("rebalancing_frequency","weekly")

        # Basic settings
        self.symbols = self.INDEXES[index]

        # ********************************
        # Algorithm settings
        # ********************************

        # Basic
        self.set_start_date(datetime.date.today().year - 10, 1, 1)
        self.set_cash(10000)
        self.markets = {symbol: self.add_equity(symbol, Resolution.DAILY) for symbol in self.symbols}

        rebalancing_frequency_internal = self.DateRules.MonthStart(self.symbols[0])
        match rebalancing_frequency:
            case "weekly":
                rebalancing_frequency_internal = self.DateRules.WeekStart(self.symbols[0])
            case "monthly":
                rebalancing_frequency_internal = self.DateRules.MonthStart(self.symbols[0])
            case "yearly":
                rebalancing_frequency_internal = self.DateRules.YearStart(self.symbols[0])
            case _:
                rebalancing_frequency_internal = self.DateRules.MonthStart(self.symbols[0])
        
        self.Schedule.On(
            rebalancing_frequency_internal,
            self.TimeRules.AfterMarketOpen(self.symbols[0], 30),
            self._rebalance_portfolio
        )

    def on_data(self, data: Slice):
        pass

    def _rebalance_portfolio(self):
        self.liquidate()
        for symbol in self.symbols:
            self.set_holdings(symbol, 1/len(self.symbols))
            # self.set_holdings(symbol, 1/len(self.symbols)*2) leverage 2x
