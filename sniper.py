# _*_ coding:utf-8 _*_

import time
from difflib import SequenceMatcher
import json
import re
import sys
import os.path
import os
import requests
# pylint: disable=W0312, C0301, C0111, C0103, C0330, W0602, C0111,

armor_price = []
weps_price = []
div_price = []
map_price = []
flask_price = []


def get_config():
	with open('config.json') as cfg:
		data = json.load(cfg)
		print('Config loaded:\n')
		print(data)
		return data

config = get_config()

def similar(a, b):
	return SequenceMatcher(None, a, b).ratio()

def get_item_value(item_info):
	global armor_price
	global weps_price
	global div_price
	global map_price
	global flask_price

	try:
		for armor in armor_price:
			if armor.get('name') == item_info['name'] and armor.get('itemClass') == item_info['type']:
				return float(armor.get('chaosValue'))

		for weps in weps_price:
			if weps.get('name') == item_info['name'] and weps.get('itemClass') == item_info['type']:
				return float(weps.get('chaosValue'))

		for div in div_price:
			if div.get('name') == item_info['name']:
				return float(div.get('chaosValue'))

		for map_item in map_price:
			if map_item.get('name') == item_info['name']:
				return float(map_item.get('chaosValue'))

		for flask in flask_price:
			if flask.get('name') == item_info['name'] and flask.get('itemClass') == item_info['type']:
				if 'Vinktar' in item_info['name']:
					variation = str(flask.get('variant'))
					explicit = str(item_info['explicit'])
					if 'Penetrates' in explicit and "Penetration" in variation:
						return float(flask.get('chaosValue'))
					elif 'Attacks' in explicit and 'Added Attacks' in variation:
						return float(flask.get('chaosValue'))
					elif 'Spells' in explicit and 'Added Spells' in variation:
						return float(flask.get('chaosValue'))
					elif 'Converted' in explicit and 'Conversion' in variation:
						return float(flask.get('chaosValue'))
				else:
					return float(flask.get('chaosValue'))

	except BaseException as e:
		print('error in get_item_value')
		print(e)

	return 0

def getFrameType(frameType):
	if frameType == 3:
		return "Unique"
	if frameType == 4:
		return "Gem"
	if frameType == 5:
		return "Currency"
	if frameType == 6:
		return "Divination Card"
	if frameType == 9:
		return "Relic"

	return frameType

def vprint(text):
	verbose = config['Output']['ConsoleVerbose']
	if verbose is True or verbose == 'true' or verbose == 'True':
		print(text)

def dprint(text):
	debug = config['Output']['Debug']
	if debug is True or debug == 'true' or debug == 'True':
		print(text)

def writeFile(text):
	t = ''
	filename = config['Output']['FileName']+'.log'

	#Empties File
	if text is 'init' and config['Output']['CleanFile'] == 'true':
		with open(filename, 'w'):
			pass
		return
	elif text is 'init':
		return
	elif isinstance(text, str):
		with open(filename, "a+") as f:
			f.write(str(text))
	else:
		for k, v in sorted(text.items()):
			if k is not 'msg':
				t += str(k)
				t += ': '
			t += str(v)
			t += '\n'
		with open(filename, "a+") as f:
			f.write(t)
			f.write('\n')
		return

def links(sockets):
	link_count = 0
	for socket in sockets:
		# print(socket)
		try:
			temp = socket["group"]
			if temp >= link_count:
				link_count = temp
		except KeyError:
			print('KeyError in links()')
		except BaseException:
			print('Error in links()')

	return link_count

def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file)


def get_first(iterable, default=None):
    if iterable:
        for item in iterable:
            return item
    return default

def validate_item(item):
	## Returns whether item is valid based on price and config settings
	try:
		price = item.get('note', None)
		name = re.sub(r'<<.*>>', '', item.get('name', None))

		if price and name and 'chaos' in price:
			try:
				if not get_first(re.findall(r'\d+', price)):
					return False
				else:
					league = config['Filter']['League']
					frameType = item.get('frameType', None)
					max_spend = int(config['Output']['MaxSpend'])
					price_normalized = float(get_first(re.findall(r'\d+', price)))
					explicit = item.get('explicitMods')
					item_info = {
						'name': name,
						'type': frameType,
						'explicit': explicit
					}
					item_value = get_item_value(item_info)
					profit = float(item_value - price_normalized)
					typeLine = item.get('typeLine', None)
					# sockets = item.get('sockets')
					# sockets_count = len(sockets)
					# links_count = links(sockets)
					ShowCorrupted = config['Filter']['ShowCorrupted']
					AllowCorrupted = config['Filter']['AllowCorrupted']
					IgnoreList = config['Filter']['Ignore']
					MinProfit = float(config['Filter']['MinProfit'])

					# for setting name of div cards
					if name is None or name == "":
						name = typeLine

					# Exclude any items not worth more than chaos
					# Item in correct league
					if str(item.get('league')) != str(league):
						dprint('Filter | League {} not {}'.format(item.get('league'), league))
						return False
					# Item is correct type
					elif int(frameType) != 3 and int(frameType) != 4 and int(frameType) != 5 and int(frameType) != 6 and int(frameType) != 9:
						dprint('Filter | Item type {} is not 3,4,5,6,9'.format(frameType))
						return False
					# Item profit is below defined amount
					elif (item_value is 0) or (profit < MinProfit) or (price_normalized < 1):
						dprint('Filter | "{}" price not within range: {} < {}'.format(name, profit, MinProfit))
						return False
					# Item is corrupted and set to hide corrupted
					if ('chaos' in price) & (price_normalized > max_spend):
						vprint('Filter | Price {} is greater than max spend {}'.format(price_normalized, max_spend))
						return False
					elif (ShowCorrupted != 'True' and ShowCorrupted != 'true') and (getFrameType(frameType) == 'Relic' or getFrameType(frameType) == 'Unique') and (item.get('corrupted') is True):
						for AllowName in AllowCorrupted:
							if AllowName not in name:
								vprint('Filter | "{}" corrupted. Item type: {}|{}'.format(name, getFrameType(frameType), frameType))
								return False
							else:
								return True
					#If item is included in specific ignore list
					else:
						for ignore in IgnoreList:
							if str(ignore) in name:
								vprint('Filter | "{}" name contains "{}"'.format(name, ignore))
								return False
					# Only return true if this block is reached after all filtering, with no errors
					return True
			except BaseException as e:
				exc_type, esc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				print('Error in chaos find: ')
				print(exc_type, fname, exc_tb.tb_lineno)
				return False
				
		else:
			return False
	except BaseException as e:
		exc_type, esc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print('Error in validate_item:')
		print(exc_type, fname, exc_tb.tb_lineno)
		print(e)
		return False

def find_items(stashes):
	# scan stashes available...
	for stash in stashes:
		#accountName = stash['accountName']
		lastCharacterName = stash['lastCharacterName']
		items = stash['items']
		stashName = stash.get('stash')

		# scan items
		for item in items:
			price = item.get('note', None)
			name = re.sub(r'<<.*>>', '', item.get('name', None))

			#Run validation on this item
			item_valid = validate_item(item)

			if item_valid:
				dprint('item valid: {}'.format(item_valid))

			#If item cannot be 6socketed
			# todo - fix this so that it only works on chests / 2h weapons
			# if (skip == False) and ((getFrameType(frameType) == 'Relic' or getFrameType(frameType) == 'Unique') and (int(item.get('ilvl')) < int(config['Filter']['MinIlvl']))):
			# 	vprint('Filter | "{}" ilvl not in range "{}" for item type {}'.format(item.get('ilvl'), config['Filter']['MinIlvl'], getFrameType(frameType)))
			# 	skip = True

			if price and name and 'chaos' in price and item_valid:
				try:
					frameType = item.get('frameType', None)
					price_normalized = float(get_first(re.findall(r'\d+', price)))
					explicit = item.get('explicitMods')
					item_info = {
						'name': name,
						'type': frameType,
						'explicit': explicit
					}
					item_value = get_item_value(item_info)
					profit = float(item_value - price_normalized)
					sockets = item.get('sockets')
					sockets_count = len(sockets)
					links_count = links(sockets)

					price = price.replace("~b/o ", "")
					price = price.replace("~price ", "")
					try:
						cost_vs_average = "{}c/{}c".format(price_normalized, item_value)
						perc_decrease = ((item_value - price_normalized) / item_value) * 100
						profit = round(item_value - price_normalized)
						msg = "@{} Hi, I would like to buy your {} listed for {} in {} (stash tab \"{}\"; position: left {}, top {})".format(lastCharacterName, name, price, config['Filter']['League'], stashName, item.get('x'), item.get('y'))
						console = "{} [{} - {}] {}-{}%".format(lastCharacterName, getFrameType(frameType), name, cost_vs_average, round(perc_decrease))			
						write = True
						alert = False
						alert_percent_high = int(config['Output']['AlertThreshold']['PercentHigh'])
						alert_profit_high = int(config['Output']['AlertThreshold']['ProfitHigh'])
						alert_percent_mid = int(config['Output']['AlertThreshold']['PercentMid'])
						alert_profit_mid = int(config['Output']['AlertThreshold']['ProfitMid'])

						# Checks if item is worth more currency than is set for max spending

						file_content = {
							'Corrupted': item.get('corrupted'),
							'Profit': '{}c'.format(profit),
							'Cost': '{} - {}% profit'.format(cost_vs_average, round(perc_decrease)),
							'Type': getFrameType(frameType),
							'Explicit': '{}'.format(item.get('explicitMods')),
							'Info': '[{}S {}L]'.format(sockets_count, links_count),
							'ILVL': item.get('ilvl'),
							'msg': msg
						}

						if (perc_decrease >= alert_percent_high) or (profit >= alert_profit_high):
							alert = 3
						elif (perc_decrease >= alert_percent_mid) or (profit >= alert_profit_mid):
							alert = 2
						else:
							alert = False

						try:
							if write:
								print(console)
								if alert != False:
									vprint('Alert level: {}'.format(alert))
									for _ in range(alert):
										print('\a')
								writeFile(file_content)
						except BaseException as e:
							print('error writing file')
							print(e)

					except BaseException as e:
						exc_type, esc_obj, exc_tb = sys.exc_info()
						fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
						print('Error in find_items skip block:')
						print(exc_type, fname, exc_tb.tb_lineno)
						print(e)
				except BaseException as e:
					exc_type, esc_obj, exc_tb = sys.exc_info()
					fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
					print('Error in find_items:')
					print(exc_type, fname, exc_tb.tb_lineno)
					print(e)


def main():
	global armor_price
	global weps_price
	global div_price
	global map_price
	global flask_price

	print("\nGimme gimme gimme....\n")
	writeFile('init')
	url_api = "http://www.pathofexile.com/api/public-stash-tabs?id="

	try:
		# get the next change id
		r = requests.get("http://api.poe.ninja/api/Data/GetStats")
		next_change_id = r.json().get('nextChangeId')

		# get unique armour value
		url_ninja = "http://cdn.poe.ninja/api/Data/GetUniqueArmourOverview?league="+ config['Filter']['League'] +"&date=" + time.strftime("%Y-%m-%d")
		r = requests.get(url_ninja)
		armor_price = r.json().get('lines')

		# get unique weapons
		url_ninja = "http://cdn.poe.ninja/api/Data/GetUniqueWeaponOverview?league="+ config['Filter']['League'] +"&date=" + time.strftime("%Y-%m-%d")
		r = requests.get(url_ninja)
		weps_price = r.json().get('lines')

		# get divination card
		url_divi = "http://api.poe.ninja/api/Data/GetDivinationCardsOverview?league="+ config['Filter']['League'] +"&date=" + time.strftime("%Y-%m-%d")
		r = requests.get(url_divi)
		div_price = r.json().get('lines')

		# get maps
		url_map = "http://api.poe.ninja/api/Data/GetMapOverview?league="+ config['Filter']['League'] +"&date=" + time.strftime("%Y-%m-%d")
		r = requests.get(url_map)
		map_price = r.json().get('lines')

		# get flask
		url_map = "http://cdn.poe.ninja/api/Data/GetUniqueFlaskOverview?league="+ config['Filter']['League'] +"&date=" + time.strftime("%Y-%m-%d")
		r = requests.get(url_map)
		flask_price = r.json().get('lines')
	except BaseException as e:
		exc_type, esc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print('Error in main():')
		print(exc_type, fname, exc_tb.tb_lineno)
		print(e)

	while True:
		try:
			params = {'id': next_change_id}
			r = requests.get(url_api, params=params)

			## parsing structure
			data = r.json()

			## setting next change id
			next_change_id = data['next_change_id']

			## attempt to find items...
			find_items(data['stashes'])

			## wait 5 seconds until parsing next structure
			time.sleep(0)
		except KeyboardInterrupt:
			print("Closing sniper.py")
			sys.exit(1)
		except BaseException as e:
			exc_type, esc_obj, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			print('Error in main:')
			print(exc_type, fname, exc_tb.tb_lineno)
			print(e)
			sys.exit(1)


if __name__ == "__main__":
    main()
