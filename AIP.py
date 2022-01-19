import pandas as pd
import numpy as np
from datetime import date
import datetime
import math
from dateutil.relativedelta import relativedelta

class AIP(object):
    def __init__(self,input_file,start_date,inv_period,time_length,
                 ma_period, function,min_rate,max_rate
                 ):
        """
        :param input_file: the SPY data file name
        :param start_date: the date you want to start do the AIP, the format must be like:
            'YYYY-MM-dd', eg. "2000-01-01"
        :param inv_period: {'weekly','monthly',int}the frequency of investment you want. If you
        type an int, you would investment in that fixed period
        :param time_length: int. How many years you would do the AIP?
        :param ma_period: int. How many days you may consider the moving average backward?
        :param function: {'linear','log','exp','ali','null'},'linear' default,'ali' is the method alipay use
        :param min_rate:the minimum percentage you would invest
        :param max_rate:the maximum percentage you would invest
        """
        self.AIP_data = pd.read_csv(input_file,index_col=0,parse_dates=[0])
        self.start_date = start_date
        self.inv_period = inv_period
        self.time_length = time_length
        self.ma_period = ma_period
        self.function = function
        self.min_rate = min_rate
        self.max_rate = max_rate

    def moving_avg(self, last_day, period=100):
        """
        last_day: the format must be "YYYY-MM-DD",e.g '2020-01-01'
        period: gives the length of days you want to calculate, if the backward day is not the trade day.
        will calculate from the trade day after the backward day.
        """
        last_day_dt = date(int(last_day[:4]), int(last_day[5:7]), int(last_day[8:10]))
        first_day_dt = last_day_dt - datetime.timedelta(days=period)
        first_day = str(first_day_dt)
        data_cal = self.AIP_data.loc[first_day:last_day, 'Adj Close']
        return data_cal.mean()

    def adjust_rate(self,price, ma_price, function='linear', min_rate=0.5, max_rate=1.5):
        """
        min_rate: the minimum rate you should invest
        function:{'linear','log','exp','ali','null'},'linear' default,'ali' is the method alipay use
        """
        percent = -(price - ma_price) / ma_price
        ali_percent = -percent
        rate = min(max(min_rate, 1 + percent), min(1 + percent, max_rate))
        if function == 'linear':
            return rate
        elif function == 'null':
            return 1
        elif function == 'log':
            return max(math.log(rate) + 1, 0)
        elif function == 'exp':
            return math.exp(rate - 1)
        elif function == 'ali':
            if ali_percent > 1:
                return 0.6
            elif ali_percent >= 0.5:
                return 0.7
            elif ali_percent >= 0.15:
                return 0.8
            elif ali_percent > 0:
                return 0.9
            else:
                return 1
        else:
            return "error!!!, check your function parameter"

    def next_trade_day(self,date):
        data = self.AIP_data
        next_date = str(data.loc[date:,].head(1).index[0])
        return next_date

    def daymove(self,start, move='monthly'):
        """
        move: {'monthly','weekly',int}choose the time period you want to automatic invest. If you type in an integer,
        you would invest it for each that period.
        """
        dt = date(int(start[:4]), int(start[5:7]), int(start[8:10]))
        if move == 'monthly':
            return str(dt + relativedelta(months=1))
        elif move == 'weekly':
            return str(dt + datetime.timedelta(days=7))
        elif type(move) == type(1):
            return str(dt + datetime.timedelta(days=move))
        else:
            return "error! check the move variable!!!"

    def get_end_days(self,start, move=3):
        """
        move: the number of year you want to test
        """
        dt = date(int(start[:4]), int(start[5:7]), int(start[8:10]))
        return str(dt + relativedelta(years=move))

    def fit(self):
        money = 1000
        AIP_data = self.AIP_data
        AIP_data['money'] = 0
        AIP_data['quantity'] = 0
        start_date = self.start_date
        time_length = self.time_length
        ma_period = self.ma_period
        inv_period = self.inv_period
        function = self.function
        min_rate = self.min_rate
        max_rate = self.max_rate
        end_date = self.get_end_days(start_date,time_length) # the date to stop calculate
        next_trade_date = self.next_trade_day(start_date)
        next_date = start_date
        while next_trade_date <= end_date:
            ma_price = self.moving_avg(next_trade_date, ma_period)
            AIP_data.loc[next_trade_date, 'money'] = money * self.adjust_rate(ma_price,
                                                                         AIP_data.loc[next_trade_date, 'Adj Close'],
                                                                         function,min_rate, max_rate)
            next_date = self.daymove(next_date, inv_period)
            next_trade_date = self.next_trade_day(next_date)
        end_cal_date = self.daymove(next_trade_date,inv_period)
        data_used = AIP_data.loc[start_date:end_cal_date, :]
        data_used['quantity'] = data_used['money'] / data_used['Adj Close']
        total_quant = data_used['quantity'].sum()
        ret = (total_quant * data_used.tail(1)['Adj Close'].values[0]) / data_used['money'].sum() - 1
        return ret



