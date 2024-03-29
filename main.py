"""
Purpose: Algo Trade on Coinbase

Inputs:
    1. Same Directory:
        a. coinbase_cloud_api_key.json

Outputs:
    None
"""


# Libraries
from coinbase.rest import RESTClient
import time
import pandas as pd
import numpy as np
import json
import uuid


if __name__ == '__main__':
    # Client and trade parameters
    with open('coinbase_cloud_api_key.json') as f:
        user = json.load(f)
    client, rest_sec = RESTClient(api_key=user['name'], api_secret=user['privateKey']), 1.00
    products = {'DOGE-USD': 1, 'LTC-USD': 4}  # {'product_pair': 'trade_float_precision'}
    usd_invest, profit_pct, loss_pct = 1.00, 5.75, 0.33  # Risk Factor = 1 when profit_pct to loss_pct ratio is about 5.75 to 0.33

    # Initial statuses
    profit_list, price_list, n_trade, usd_buy, bal_after, prod_qty, t_buy, profit_limit, loss_limit, bal_usd_quit = (
        [], [], 0, 0, 0, 0, 0, 0, 0, 25)
    bal_before = {a['currency']: round(float(a['available_balance']['value']), 8) for a in client.get_accounts(limit=250)['accounts']}
    print('T_START =', time.strftime("%H:%M:%S", time.localtime()), '| USD_BAL_START =', bal_before['USD'], 
          '| USD_BAL_QUIT =', bal_usd_quit, '| USD_INVEST =', usd_invest, '| PROFIT_PCT =', profit_pct, '| LOSS_PCT =', loss_pct)

    # While USD Balance > USD Quit Limit
    while {a['currency']: round(float(a['available_balance']['value']), 8) for a in client.get_accounts(limit=250)['accounts']}['USD'] > bal_usd_quit:
        for p in products.keys():  # Cycle through product pairs
            # Rest
            time.sleep(rest_sec)

            # Query and aggregate market data
            query = client.get_market_trades(product_id=p, limit=500, start=str(int(time.time()) - 1000), end=str(int(time.time())))
            data_original = pd.DataFrame({'price': [t['price'] for t in query['trades']], 
                                          'time': [t['time'] for t in query['trades']]})
            data_original['time'] = pd.to_datetime(data_original['time'], format='ISO8601').dt.floor('s')
            data_original = data_original.astype({'price': float}).sort_values(by=['time'])
            data_aggregated = data_original.groupby([data_original['time']]).mean().reset_index().sort_values(by=['time'])

            # Enter criteria 1: EMA Short > EMA Long
            ema_short_values = data_aggregated['price'].ewm(span=20, adjust=False).mean().tolist()
            ema_long_values = data_aggregated['price'].ewm(span=200, adjust=False).mean().tolist()
            criteria_ema_short_over_ema_long = ema_short_values[-1] > ema_long_values[-1]  # Compare latest values

            # Enter critera 2: EMA Short's slope > 0
            ema_short_slope = np.polyfit(ema_short_values, list(range(1, len(ema_short_values) + 1)), 1)[0]
            criteria_ema_short_slope_positive = ema_short_slope > 0

            # Enter market
            if criteria_ema_short_over_ema_long and criteria_ema_short_slope_positive:
                # Place market order
                order_buy = client.market_order_buy(client_order_id=str(uuid.uuid4()), product_id=p, quote_size=str(usd_invest))
                usd_buy = round(float(client.get_product(product_id=p)['price']), 8)

                # Check market order
                bal_after = {a['currency']: round(float(a['available_balance']['value']), 8) for a in client.get_accounts(limit=250)['accounts']}
                prod_qty = round(bal_after[p.split('-')[0]] - bal_before[p.split('-')[0]], products[p])
                if prod_qty > 0:  # Confirm via checking balance manually because API isn't reliable
                    # Update statuses
                    t_buy, temp = time.localtime(), p.split('-')[0]
                    loss_limit = round(usd_buy - (usd_buy * loss_pct / 100), 8)
                    profit_limit = round(usd_buy + (usd_buy * profit_pct / 100), 8)
                    print('T_BUY =', time.strftime("%H:%M:%S", t_buy), f'| {temp}_QTY =', prod_qty, f'| USD_PRICE =', usd_buy,
                          '| PROFIT_LIMIT =', profit_limit, '| LOSS_LIMIT =', loss_limit)
                else:  # Cancel market order
                    client.cancel_orders(order_ids=[order_buy['order_id']])
                    prod_qty = 0

            # Exit market
            while prod_qty > 0:
                # Rest
                time.sleep(rest_sec)

                # Check spot prices and exit criterias
                usd_sell = round(float(client.get_product(product_id=p)['price']), 8)
                criteria_sell_profit, criteria_sell_loss = usd_sell >= profit_limit, usd_sell <= loss_limit
                price_list.insert(0, usd_sell)
                print('\r\tPRICE_RECENT_10 =', price_list[:10], ' '*10, end='')  # Show the most recent 10 spot prices
                if criteria_sell_profit or criteria_sell_loss:
                    # Place market order
                    order_sell = client.market_order_sell(client_order_id=str(uuid.uuid4()), product_id=p, base_size=str(prod_qty))

                    # Check market order
                    bal_after = {a['currency']: round(float(a['available_balance']['value']), 8) for a in client.get_accounts(limit=250)['accounts']}
                    prod_qty = round(bal_after[p.split('-')[0]] - bal_before[p.split('-')[0]], products[p])
                    if prod_qty == 0:  # Confirm via checking balance manually because API isn't reliable
                        # Update statuses
                        bal_after = {a['currency']: round(float(a['available_balance']['value']), 8) for a in client.get_accounts(limit=250)['accounts']}
                        profit_list.append(round(bal_after[p.split('-')[1]] - bal_before[p.split('-')[1]], 8))
                        prod_qty, bal_before, n_trade, price_list = 0, bal_after, n_trade + 1, []
                        print('\n\r\tT_SELL =', time.strftime("%H:%M:%S", time.localtime()),
                              '| T_DIFF_MIN =', round((time.mktime(time.localtime()) - time.mktime(t_buy)) / 60, 2),
                              '| USD_BAL_NET =', round(sum(profit_list), 8), '| N_TRADE =', n_trade)
                        t_buy = 0
                    else:  # Cancel market order
                        client.cancel_orders(order_ids=[order_sell['order_id']])
