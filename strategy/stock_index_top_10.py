# region imports
from AlgorithmImports import *
import datetime
# endregion

## Trend follow strategy selecting the top 10 companies from the stock index with weekly/monthly rebalancing equally weighted.
class StockIndexTop10_V2(QCAlgorithm):

    INDEXES = {
            "SP500": ["NVDA","MSFT","AAPL","AMZN","META","AVGO","GOOGL","BRK.B","TSLA", "GOOG"], # https://finance.yahoo.com/quote/SPY/holdings/
            "NASDAQ100":["NVDA","MSFT","AAPL","AMZN","AVGO","META","NFLX","TSLA","COST","GOOGL"], # https://finance.yahoo.com/quote/QQQ/holdings/
            "SP500 MOMENTUM": ["NVDA","META","AMZN","AVGO","JPM","TSLA","WMT","NFLX","PLTR","COST"], # https://finance.yahoo.com/quote/SPMO/holdings/ 
            "SP MEDIUM CAP MOMENTUM": ["IBKR","EME","SFM","FIX","GWRE","USFD","CRS","EQH","CW","CASY"], # https://finance.yahoo.com/quote/XMMO/holdings/ 
            "SP SMALL CAP MOMENTUM": ["EAT","CORT","COOP","AWI","IDCC","SKYW","JXN","CALM","DY","SMTC"] # https://finance.yahoo.com/quote/XSMO/holdings/ 
        }

    def initialize(self):

        # ********************************
        # User defined inputs
        # ********************************
        index = self.get_parameter("index", "SP500 MOMENTUM")
        rebalancing_frequency = self.get_parameter("rebalancing_frequency","weekly")
        self.enable_filter = True if (self.get_parameter("enable_filter", "True") == "True") else False

        # Basic settings
        self.symbols = self.INDEXES[index]
        self.benchmark_symbol = self.get_parameter("benchmark_symbol", "SPMO")
        self.add_equity(self.benchmark_symbol, Resolution.DAILY)
        self.benchmark_sma200 = self.sma(self.benchmark_symbol, 200)

        # ********************************
        # Algorithm settings
        # ********************************

        # Basic
        self.set_start_date(datetime.date.today().year - 10, 1, 1)
        self.set_cash(10000)
        self.markets = {symbol: self.add_equity(symbol, Resolution.DAILY) for symbol in self.symbols}
        self.enable_trading = True

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
        if self.enable_filter:
            # Safely check if benchmark_symbol exists in data.bars before accessing it
            if self.benchmark_symbol in data.bars:
                bar_benchmark = data.bars[self.benchmark_symbol]
                if bar_benchmark.close < self.benchmark_sma200[1].value:
                    self.enable_trading = False
                else:
                    self.enable_trading = True
        else:
            # Optionally add logging/debugging to help trace missing data
            self.debug(f"No data for {self.benchmark_symbol} at {self.time}. Skipping filter this bar.")

    def _rebalance_portfolio(self):
        if self.portfolio.invested:
            self.liquidate()

        if self.enable_trading:
            for symbol in self.symbols:
                self.set_holdings(symbol, 1/len(self.symbols))
                # self.set_holdings(symbol, 1/len(self.symbols)*2) # leverage 2x
