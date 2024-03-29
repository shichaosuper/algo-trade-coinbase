# algo-trade-coinbase
## Purpose:
My attempt to algorithmically trade cryptocurrencies on Coinbase namely DOGE, to see how it performs for smaller-sized cryptos, and LTC, to see how it performs for larger-sized cryptos, Coins.

## Input(s):
1. **"coinbase_cloud_api_key.json" File**: Provided by Coinbase Cloud; an anonymized example is provided in the repo.
   * Instructions to get the file: https://docs.cloud.coinbase.com/advanced-trade-api/docs/rest-api-auth#cloud-api-trading-keys
   * The 2 keys of interest are "name" and "privateKey"

## Logic:
1. Import "coinbase_cloud_api_key.json" File from same directory
2. Instantiate Coinbase client, parameters and statuses variables
3. While USD BALANCE above specified USD QUIT LIMIT, cycle through product pairs e.g. "DOGE-USD":
   * Queries its most recent historic market data
   * Aggregate the prices on a time unit level = seconds
   * Estimate the EMA SHORT, most recent 20 prices, and EMA LONG, up to most recent 200 prices, values
   * If the latest EMA SHORT value is over the latest EMA LONG value, i.e. latest short-price action is above latest long-price action, and the EMA SHORT values give a positive slope, i.e. most recent price actions indicate the formation of an upward trend, then enter market with USD INVEST amount and update statuses
   * While some Product amount was brought:
     * If spot price is above calculated USD PROFIT LIMIT or below calculated USD LOSS LIMIT, sell of all of the product amount and update statutes
   
## Output(s):
None; however, since the Program will have access to your Coinbase account and be live trading, your balance will reflect accordingly.

## Results:
Please refer to the "Results_X.png" Files in the repo.
* **"Results_1.png" File**: Made 2 profitable trades
* **"Results_2.png" File**: Nothing of great interest here in terms of wins and losses
* **"Results_3.png" File**: Took 2 huge losses; about 3x the usual size of about $0.03; manually terminated Program at at Trade Number = 43

When all is said and done, in about 24 hours, my investments of $1.00 yielded a net return of about -$2.86 i.e. an ROI of about -286%.

## Rooms for Improvements:
1. **Improve market entry criterias**: I used some simple metrics i.e. EMAs and Slopes to gauge when to enter the market; a model-based approach, or hybrid of the two strategies, may paint a clearer image of a market's fruitfulness
2. **Improve market exit criterias**:
   * Once some Product amount was brought, Program will be stuck in a While loop until it sells the whole amount of product off so Program can miss out on other market entry opportunities
   * The USD PROFIT LIMIT, 5.75% above the estimated USD BUY price, and USD LOSS LIMIT, 0.33% below the estimated USD BUY price, were established experimentally based on trial and error to figure out what a Risk Factor = 1 looks like once Coinbase fees, etc. were factored into a live trade
3. **Use of limit orders instead of market orders**: All market entries and exits were done using market orders because they're the most liquid; however, using them can lead to over-paying, e.g. acquiring only 5 DOGE Coins at $0.02 instead of 6 DOGE Coins, or over-hemorrhaging, e.g. as in "Results_3.png" File where there were some losses that were 3x the expected usual amount
