#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from collections import namedtuple

def log_returns(prices):
    return np.log(np.roll(prices, -1) / prices)


def parse_transaction_log(transaction_log):
    '''
    Parses the transaction log generated by the backtest into something
    more readable.

    '''

    cash_transactions = []
    market_transactions = []

    for key, lists in transaction_log.items():
        for item in lists:

            if type(item).__name__ == 'cash_transaction':
                cash_transactions.append(item)

            if type(item).__name__ == 'market_transaction':
                market_transactions.append(item)

    cash_transactions = pd.DataFrame.from_dict(
        cash_transactions).set_index('time')

    market_transactions = pd.DataFrame.from_dict(
        market_transactions).set_index('time')

    return cash_transactions, market_transactions


def trade_details(transaction_log, sequence_id, return_as_tuple=False):
    '''
    Parse the transaction log by sequence id to get the details of a 
    trade. The sequence id is unique, and is assigned to an open position
    until the position has been closed. 
    '''

    trade_summary = namedtuple('trade_summary',
                               ['ticker', 'enter_time', 'exit_time',
                                   'enter_price', 'exit_price',
                                   'shares_purchased', 'shares_sold',
                                   'avg_buy_price', 'avg_sell_price',
                                   'num_of_trades', 'pnl', 'commission_total',
                                   'holding_period', 'completed']
                               )

    trades_with_sequence = transaction_log[
        transaction_log['sequence'] == sequence_id]

    sell_mask = trades_with_sequence['direction'] == 'SELL'

    sells = trades_with_sequence[sell_mask]
    buys = trades_with_sequence[~sell_mask]

    total_shares_bought = np.sum(buys['shares'])
    total_shares_sold = np.sum(sells['shares'])

    enter_time = trades_with_sequence.index[0]
    enter_price = buys.iloc[0]['price']
    num_of_trades = len(trades_with_sequence)
    total_commissions = np.sum(trades_with_sequence['commission'])

    holding_period = np.nan
    exit_time = np.nan
    exit_price = np.nan
    completed = False
    pnl = np.nan

    if total_shares_bought - total_shares_sold == 0:
        exit_time = trades_with_sequence.index[-1]
        completed = True

        holding_period = exit_time - enter_time
        exit_price = sells.iloc[-1]['price']

        sum_of_buys = buys['price'] * buys['shares'] - buys['commission']
        sum_of_buys = np.sum(sum_of_buys)

        sum_of_solds = (sells['price'] *
                        sells['shares'] - sells['commission'])
        sum_of_solds = np.sum(sum_of_solds)

        pnl = np.round(sum_of_solds - sum_of_buys, 2)

    avg_buy_price = np.mean(buys['price'])
    avg_sell_price = np.mean(sells['price'])

    details = trade_summary(ticker=trades_with_sequence['ticker'][0],
                            enter_time=enter_time, exit_time=exit_time,
                            enter_price=enter_price, exit_price=exit_price,
                            shares_purchased=total_shares_bought,
                            shares_sold=total_shares_sold,
                            avg_buy_price=avg_buy_price,
                            avg_sell_price=avg_sell_price,
                            num_of_trades=num_of_trades, pnl=pnl,
                            commission_total=total_commissions,
                            holding_period=holding_period,
                            completed=completed
                            )
    # return_as_tuple=True to return as a namedtuple.
    if return_as_tuple:
        return details
    else:
        return pd.Series(details, index=details._fields)


def trades_summary(transaction_log, tickers):
    '''
    Summary of all trades that occurred in the transaction log.
    '''

    all_trades = []
    if not isinstance(tickers, list):
        tickers = [tickers]

    for ticker in tickers:
        selected_data = transaction_log[transaction_log['ticker'] == ticker]
        sequences = selected_data['sequence'].unique()

        for sequence in sequences:
            all_trades.append(trade_details(
                transaction_log, sequence, return_as_tuple=True))

        return pd.DataFrame.from_dict(all_trades)