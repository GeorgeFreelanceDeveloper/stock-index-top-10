# region imports
from AlgorithmImports import *
import datetime
# endregion

# Trend follow strategy selecting the top 10 companies from the stock index with weekly, monthly or yearly rebalancing equally weighted when broader market is in uptrend (price is above 200 daily moving average).
class StockIndexTop10_V2(QCAlgorithm):

    INDEXES = {
        "SP500": {
            "stocks": ["NVDA", "MSFT", "AAPL", "AMZN", "META", "AVGO", "GOOGL", "BRK.B", "TSLA", "GOOG"],
            "benchmark_symbol": "SPY"
            # https://finance.yahoo.com/quote/SPY/holdings/
        },
        "NASDAQ100": {
            "stocks": ["NVDA", "MSFT", "AAPL", "AMZN", "AVGO", "META", "NFLX", "TSLA", "COST", "GOOGL"],
            "benchmark_symbol": "QQQ"
            # https://finance.yahoo.com/quote/QQQ/holdings/
        },
        "SP500 MOMENTUM": {
            "stocks": ["NVDA", "META", "AMZN", "AVGO", "JPM", "TSLA", "WMT", "NFLX", "PLTR", "COST"],
            "benchmark_symbol": "SPMO"
            # https://finance.yahoo.com/quote/SPMO/holdings/
        },
        "SP MEDIUM CAP MOMENTUM": {
            "stocks": ["IBKR", "EME", "SFM", "FIX", "GWRE", "USFD", "CRS", "EQH", "CW", "CASY"],
            "benchmark_symbol": "XMMO"
            # https://finance.yahoo.com/quote/XMMO/holdings/
        },
        "SP SMALL CAP MOMENTUM": {
            "stocks": ["EAT", "CORT", "COOP", "AWI", "IDCC", "SKYW", "JXN", "CALM", "DY", "SMTC"],
            "benchmark_symbol": "XSMO"
            # https://finance.yahoo.com/quote/XSMO/holdings/
        },
        "IPOX 100 US": {
            "stocks": ["GEV", "PLTR", "APP", "CEG", "RBLX", "DASH", "IBM", "HOOD", "TT", "IOT"],
            "benchmark_symbol": "FPX"
            # https://finance.yahoo.com/quote/FPX/
        }
    }

    def initialize(self):

        # ********************************
        # User defined inputs
        # ********************************
        index = self.get_parameter("index", "SP500 MOMENTUM")
        rebalancing_frequency = self.get_parameter("rebalancing_frequency", "monthly")
        self.leverage = self.get_parameter("leverage", 0)

        # Filter settings
        self.enable_filter = True if (self.get_parameter("enable_filter", "True") == "True") else False

        # ********************************
        # Algorithm settings
        # ********************************

        # Basic
        self.set_start_date(datetime.date.today().year - 20, 1, 1)
        self.set_cash(10000)
        self.enable_automatic_indicator_warm_up = True

        self.benchmark_symbol = self.INDEXES[index]["benchmark_symbol"]
        self.symbols = self.INDEXES[index]["stocks"]
        self.markets = {symbol: self.add_equity(symbol, Resolution.DAILY) for symbol in self.symbols}
        self.add_equity(self.benchmark_symbol, Resolution.DAILY)
        self.benchmark_sma200 = self.sma(self.benchmark_symbol, 200)
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
                self.set_holdings(symbol, (1 / len(self.symbols)) + (1 / len(self.symbols) * self.leverage))
