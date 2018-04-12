#!/usr/bin/env python2

from __future__ import print_function, division, unicode_literals
import ccxt
import time
import math
import requests
import json

from uuid import uuid4 as uid
from config import bitmex_auth
from config import bitmex_test

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

apitrylimit = 20
apisleep = 8

bitmex = ccxt.bitmex(bitmex_auth)
if(bitmex_test):
	bitmex.urls['api'] = bitmex.urls['test']

ordersym = u'BTC/USD'
possym = u'XBTUSD'

orders = []

def market_order(side, qty, symbol = ordersym):
	orderdata = None
	apitry = 0
	while not orderdata and apitry < apitrylimit:
	#for i in range(0, apitrylimit):
		try:
			orderdata = bitmex.create_order(symbol, 'market', side, qty)
		except (ccxt.ExchangeError, ccxt.DDoSProtection, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as error:
			time.sleep(apisleep+2*apitry)
			apitry = apitry+1

	orders.append(orderdata)
	if(orderdata['info']['cumQty'] != qty):
		log.warning("Filled quantity %d does not match requested quantity of %d" % (orderdata['info']['cumQty'], qty))
	return orderdata

def market_buy(qty, symbol = ordersym):
	return market_order('buy', qty, symbol)
	
def market_sell(qty, symbol = ordersym):
	return market_order('sell', qty, symbol)

def get_positions():
	positions = []
	apitry = 0
	while(not positions and apitry < apitrylimit):
		try:
			positions = bitmex.private_get_position()
		except (ccxt.ExchangeError, ccxt.DDoSProtection, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as error:
			time.sleep(apisleep+2*apitry)
			apitry = apitry + 1
	return positions

def get_open_orders(symbol = ordersym):
	oorders = None
	apitry = 0
	while(oorders == None and apitry < apitrylimit):
		try:
			oorders = bitmex.fetch_open_orders(symbol)
		except (ccxt.ExchangeError, ccxt.DDoSProtection, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as error:
			time.sleep(apisleep+2*apitry)
			apitry = apitry + 1
	return oorders

def print_positions():
	#logmesg = "Symbol\tQty\tEntry\t\tLiq\n"

	orderstring = "POSITION: Symbol: %s\tQty: %d\tEntry: %.2f\tLiq: %.2f"
	for position in get_positions():
		if position['currentQty'] != 0:	
		#logmesg = logmesg + position['symbol']+"\t"+str(position['currentQty'])+"\t"+str(position['avgCostPrice'])+"\t"+str(position['liquidationPrice'])+"\n"
			log.info(orderstring % (position['symbol'], position['currentQty'], position['avgCostPrice'], position['liquidationPrice']))
	#log.info(logmesg)

def get_stoppx(order):
	rvalue = None
	if order['type'] == 'stop':
		for key, value in order['info'].items():
			if key == 'stopPx':
				rvalue = value
	return rvalue

def print_open_orders():
	#logmesg = "Amount\tPrice\tSide\tType\tText\n"
	orderstring = "ORDER: Amount: %d\tPrice: %.2f\tSide: %s\tType: %s"
	price = 0.0
	for order in get_open_orders():
		if(order['type'] == 'stop'):
			price = get_stoppx(order)
		else:
			price = order['price']
		#logmesg = logmesg+ str(order['amount'])+"\t"+str(price)+"\t"+order['side']+"\t"+order['type']+"\t"+order['info']['text']+"\n"
		log.info(orderstring % ( order['amount'], price, order['side'], order['type']))

def market_close_all(pos_symbol = possym, order_symbol = ordersym):
	close_longs(pos_symbol, order_symbol)
	close_shorts(pos_symbol, order_symbol)

def close_longs(pos_symbol = possym, order_symbol = ordersym):
	positions = get_positions()

	for position in positions:
		if(position['symbol'] == pos_symbol):
			if(position['currentQty'] > 0):
				market_sell(position['currentQty'], order_symbol)

def close_shorts(pos_symbol = possym, order_symbol = ordersym):
	positions = get_positions()

	for position in positions:
		if(position['symbol'] == pos_symbol):
			if(position['currentQty'] < 0):
				market_buy(position['currentQty'])

def market_stop(side, qty, price, symbol = ordersym):

	orderdata = None
	apitry = 0
	while not orderdata and apitry < apitrylimit:
	#for i in range(0, apitrylimit):
		try:
			orderdata = bitmex.create_order(symbol, 'Stop', side, qty, params={ 'stopPx': price, 'orderQty': qty })
		except (ccxt.ExchangeError, ccxt.DDoSProtection, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as error:
			time.sleep(apisleep+2*apitry)
			apitry = apitry+1
	return orderdata

def market_stop_close(side, qty, price, symbol = ordersym, params=None):
	orderdata = None
	apitry = 0
	myparams = { 'stopPx': price, 'orderQty': qty, 'execInst': 'Close' }
	if(params):
		myparams.update(params)

	while not orderdata and apitry < apitrylimit:
	#for i in range(0, apitrylimit):
		try:
			orderdata = bitmex.create_order(symbol, 'Stop', side, qty, params=myparams)
		except (ccxt.ExchangeError, ccxt.DDoSProtection, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as error:
			time.sleep(apisleep+2*apitry)
			apitry = apitry+1
	return orderdata

def limit_order(side, qty, price, params=None, symbol=ordersym):
	orderdata = None
	apitry = 0
	while not orderdata and apitry < apitrylimit:
	#for i in range(0, apitrylimit):
		try:
			orderdata = bitmex.create_order(symbol, 'limit', side, qty, price, params)
		except (ccxt.ExchangeError, ccxt.DDoSProtection, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as error:
			time.sleep(apisleep+2*apitry)
			apitry = apitry+1
	orders.append(orderdata)
	return orderdata

def limit_close(side, qty, price, symbol = ordersym, params = None):
	myparams = { 'execInst': 'ReduceOnly' }
	if(params):
		myparams.update(params)
			
        orderdata = limit_order(side, qty, price, params=myparams, symbol=symbol)
        return orderdata

def limit_buy(qty, price, symbol = ordersym, params=None):
	return limit_order('buy', qty, price, symbol, params=params)

def limit_sell(qty, price, symbol = ordersym, params=None):
	return limit_order('sell', qty, price, symbol, params=params)

def cancel_open_orders(symbol = ordersym, text=None):
	for order in get_open_orders():
		if(order['symbol'] != symbol):
			continue
		if(text and not text in order['info']['text']):
			continue
		response = None
		apitry = 0
		while not response and apitry < apitrylimit:
			try:
				response = bitmex.cancel_order(order['id'])
			except (ccxt.ExchangeError, ccxt.DDoSProtection, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as error:
				time.sleep(apisleep+2*apitry)
				apitry = apitry+1

def create_or_update_order(ordertype, side, newamount, price=None, symbol=ordersym, params=None):
	neworder = None
	orderfound = False
	ordertext = None
	if params and 'text' in params.keys():
		ordertext = params['text']
	if(price):
		price = math.floor(price)
	for order in get_open_orders():
		if(order['symbol'] == symbol and order['type'] == ordertype and order['side'] == side and (not ordertext or ordertext in order['info']['text']) and not orderfound):
			if(order['type'] == 'stop'):
				params.update({'stopPx': price, 'execInst': 'Close' })
				neworder = bitmex.edit_order(order['id'], symbol, ordertype, side, newamount, params=params) 
				orderfound = True
				log.debug("Updating order %s" % order['id'])
			else:
				neworder = bitmex.edit_order(order['id'], symbol, ordertype, side, newamount, math.floor(price), params)
				orderfound = True
				log.debug("Updating order %s" % order['id'])
		elif(order['symbol'] == symbol and order['type'] == ordertype and order['side'] == side and (not ordertext or ordertext in order['info']['text']) and orderfound):
			# once found one, close any others
			bitmex.cancel_order(order['id'])
			log.debug("Canceling order %d" % order['id'])
	if(not orderfound):
		if(ordertype == 'limit'):
			neworder = limit_close(side, newamount, price, symbol, params=params)
		elif(ordertype == 'stop'):
			neworder = market_stop_close(side, newamount, price, symbol, params=params)
	return neworder

def get_position_size(side, symbol=possym):
	position_size = 0
	for position in get_positions():
		if(position['symbol'] != symbol):
			continue
		currentqty = position['currentQty']
		if(side == 'long' and currentqty > 0):
			position_size = currentqty
		elif(side == 'short' and currentqty < 0):
			position_size = -1*currentqty
	return position_size

def add_to_order(ordertype, side, addamount, price=None, pos_symbol=possym, order_symbol=ordersym):
	#print("Updating order type %s side %s addamount %f price %f" % (ordertype, side, addamount, price))
	currentsize = 0
	if(side == 'sell'):
		currentsize = get_position_size('long', pos_symbol)
	elif(side == 'buy'):
		currentsize = get_position_size('short', pos_symbol)
	#print("New size %f new price %f" % (currentsize+addamount, price))
	return create_or_update_order(ordertype, side, currentsize+addamount, price, ordersym)

def get_bidasklast(symbol = ordersym):
	ticker = bitmex.fetch_ticker(symbol)
	return (ticker['bid'], ticker['ask'], ticker['last'])

def update_bracket_pct(sl, tp, pos_symbol=possym, order_symbol=ordersym):
	slpct = sl/100.
	tppct = tp/100.
	ordertxt = 'bracket'
	myparams = { 'text' : ordertxt }
	my_positions = get_positions()
	for position in my_positions:
		rawqty = position['currentQty']
		symbol = position['symbol']
		price = position['avgCostPrice']
		slprice = price
		tpprice = price
		if(abs(rawqty) > 0 and symbol == pos_symbol):
			if(rawqty > 0):
				slprice = price-price*slpct
				tpprice = price+price*slpct
				create_or_update_order('limit', 'sell', rawqty, tpprice, order_symbol, params=myparams)
				create_or_update_order('stop', 'sell', rawqty, slprice, order_symbol, params=myparams)
			else:
				slprice = price+price*slpct
				tpprice = price-price*slpct
				create_or_update_order('limit', 'buy', -rawqty, tpprice, order_symbol, params=myparams)
				create_or_update_order('stop', 'buy', -rawqty, slprice, order_symbol, params=myparams)
	if(len(my_positions) == 0 or (len(my_positions) == 1 and my_positions[0]['currentQty'] == 0)):
		cancel_open_orders(text=ordertxt)
	
	return True

def smart_order(side, qty, symbol=ordersym):
	bid, ask, last = get_bidasklast()
	
	ocoorders = []
	# if bid is 7000 ask is 7005
	# to buy, bid 7004.5, hope it moves down
	# if next trade moves up, market buy
	if side == 'Buy':
		limitprice = ask - 1 
		stopprice = ask + 2.
	if side == 'Sell':
		limitprice = bid + 1
		stopprice = bid - 2.

	#print "bid %f, ask %f, last %f, limit %f, stop %f" % (bid, ask, last, limitprice, stopprice)

	ocoid = uid().hex
	ordertext = 'smart_order'
	orderObj = {
		'orders' : [{
			'clOrdLinkID' : ocoid,
			'contingencyType' : 'OneCancelsTheOther',
			'symbol' : possym,
			'ordType' : 'Stop',
			'side' : side,
			'stopPx' : stopprice,
			'orderQty' : qty,
			'text' : ordertext,
			'execInst' : 'LastPrice'
			},{
			'clOrdLinkID' : ocoid,
			'contingencyType' : 'OneCancelsTheOther',
			'symbol' : possym,
			'ordType' : 'Limit',
			'side' : side,
			'price' : limitprice,
			'orderQty' : qty,
			'text' : ordertext
			}
			]}
	
	result = None
	apitry = 0
	while(not result  and apitry < apitrylimit):
		try:
		#result = requests.post(bitmex.urls['api'], json = [ limitOrder, stopOrder ])
			result = bitmex.private_post_order_bulk(orderObj)
 		except Exception as err:
 			result = None
 			log.warning("Failed to place smart order, trying again")
 			log.warning(err)
 			time.sleep(apisleep+apitry*2)
 			apitry = apitry + 1

	return result
