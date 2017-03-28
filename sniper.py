import time
import requests
import re
import sys
import datetime
from datetime import datetime
import os.path
import configparser
import os
import json
from pprint import pprint
from difflib import SequenceMatcher
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
				if 'Vinktar' in item_info['name'] and flask.get('variation') in item_info['explicit']:
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
	elif hasattr(text, "__len__"):
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
	else:
		with open(filename, "a+") as f:
			f.write(str(text))

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

def find_items(stashes):
	# scan stashes available...
	for stash in stashes:
		#accountName = stash['accountName']
		lastCharacterName = stash['lastCharacterName']
		items = stash['items']
		stashName = stash.get('stash')
		league = config['Filter']['League']
		# scan items
		for item in items:
			typeLine = item.get('typeLine', None)
			name = re.sub(r'<<.*>>', '', item.get('name', None))
			price = item.get('note', None)
			frameType = item.get('frameType', None)
			sockets = item.get('sockets')
			sockets_count = len(sockets)
			links_count = links(sockets)
			skip = False
			explicit = item.get('explicitMods')

			ShowCorrupted = config['Filter']['ShowCorrupted']
			AllowCorrupted = config['Filter']['AllowCorrupted']
			IgnoreList = config['Filter']['Ignore']

			# if 'Vinktar' in name:
			# 	print(item)
			# 	writeFile(item)

			if (not skip) and item.get('league') != league:
				dprint('Filter | League {} not {}'.format(item.get('league'), league))
				skip = True

			if (not skip) and (int(frameType) != 3 and int(frameType) != 4 and int(frameType) != 5 and int(frameType) != 6 and int(frameType) != 9):
				dprint('Filter | Item type {} is not 3,4,5,6,9'.format(frameType))
				skip = True

			# for divination
			if name is None or name == "":
				name = typeLine

			## compare unique that worth at least 1 chaos.
			if price and name and 'chaos' in price:
				try:
					if not re.findall(r'\d+', price)[0]:
						continue
				except BaseException:
					continue

				price_normalized = float(re.findall(r'\d+', price)[0])
				item_info = {
					'name': name,
					'type': frameType,
					'explicit': explicit,
				}
				item_value = get_item_value(item_info)

				# File output setup
				if (not skip) and ((item_value is 0) or ((item_value - price_normalized) < 3.0) or (price_normalized is 0)):
					dprint('Filter | "{}" price not within range'.format(name))
					skip = True

				# If config set to hide corrupted gear
				if (not skip) and (ShowCorrupted != 'True' and ShowCorrupted != 'true') and (getFrameType(frameType) == 'Relic' or getFrameType(frameType) == 'Unique') and (item.get('corrupted') is True):
					for AllowName in AllowCorrupted:
						if AllowName not in name:
							vprint('Filter | "{}" corrupted. Item type: {}|{}'.format(name, getFrameType(frameType), frameType))
							skip = True

				#If item is included in ignore list
				if not skip:
					for ignore in IgnoreList:
						if str(ignore) in name:
							skip = True
							vprint('Filter | "{}" name contains "{}"'.format(name, ignore))

				#If item cannot be 6socketed
				# todo - fix this so that it only works on chests / 2h weapons
				# if (skip == False) and ((getFrameType(frameType) == 'Relic' or getFrameType(frameType) == 'Unique') and (int(item.get('ilvl')) < int(config['Filter']['MinIlvl']))):
				# 	vprint('Filter | "{}" ilvl not in range "{}" for item type {}'.format(item.get('ilvl'), config['Filter']['MinIlvl'], getFrameType(frameType)))
				# 	skip = True

				if skip == False:
					price = price.replace("~b/o ", "")
					price = price.replace("~price ", "")

					try:
						cost_vs_average = "{}c/{}c".format(price_normalized, item_value)
						perc_decrease = ((item_value - price_normalized) / item_value) * 100
						profit = round(item_value - price_normalized)
						msg = "@{} Hi, I would like to buy your {} listed for {} in Legacy (stash tab \"{}\"; position: left {}, top {})".format(lastCharacterName, name, price, stashName, item.get('x'), item.get('y'))
						console = "{} [{} - {}] {}-{}%".format(lastCharacterName, getFrameType(frameType), name, cost_vs_average, round(perc_decrease))
						alert = False
						alert_percent_high = config['Output']['AlertThreshold']['PercentHigh']
						alert_profit_high = config['Output']['AlertThreshold']['ProfitHigh']
						alert_percent_mid = config['Output']['AlertThreshold']['PercentMid']
						alert_profit_mid = config['Output']['AlertThreshold']['ProfitMid']

						file_content = {
							'Corrupted': item.get('corrupted'),
							'Profit': '{}c'.format(profit),
							'Cost': '{} - {}%'.format(cost_vs_average, round(perc_decrease)),
							'Type': getFrameType(frameType),
							'Explicit': '{}'.format(item.get('explicitMods')),
							'Info': '[{}S {}L]'.format(sockets_count, links_count),
							'ILVL': item.get('ilvl'),
							'msg': msg
						}

						# if (perc_decrease >= alert_percent_high) or (profit >= alert_profit_high):
						#  	alert = 3
						# elif (perc_decrease >= alert_percent_mid) or (profit >= alert_profit_mid):
						#  	alert = 2
						# else:
						# 	alert = False


						# if price > 0:
						# if alert != False:
						# 	console.log('Alert level: '+alert)
						# 	for x in alert:
						# 		print('\a')
						print(console)
						try:
							writeFile(file_content)
						except:
							print('error writing file')
						# else:
						# 	print('Price is {} so skipping').format(price)
					except BaseException as e:
						exc_type, esc_obj, exc_tb = sys.exc_info()
						fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
						print('Error in find_items:')
						print(exc_type, fname, exc_tb.tb_lineno)
						print(e)
						pass

def main():
	global armor_price
	global weps_price
	global div_price
	global map_price
	global flask_price

	print("\nGimme gimme gimme....\n")
	writeFile('init')
	url_api = "http://www.pathofexile.com/api/public-stash-tabs?id="

	# get the next change id
	r = requests.get("http://api.poe.ninja/api/Data/GetStats")
	next_change_id = r.json().get('nextChangeId')

	# get unique armour value
	url_ninja = "http://cdn.poe.ninja/api/Data/GetUniqueArmourOverview?league=Legacy&date=" + time.strftime("%Y-%m-%d")
	r = requests.get(url_ninja)
	armor_price = r.json().get('lines')

	# get unique weapons
	url_ninja = "http://cdn.poe.ninja/api/Data/GetUniqueWeaponOverview?league=Legacy&date=" + time.strftime("%Y-%m-%d")
	r = requests.get(url_ninja)
	weps_price = r.json().get('lines')

	# get divination card
	url_divi = "http://api.poe.ninja/api/Data/GetDivinationCardsOverview?league=Legacy&date=" + time.strftime("%Y-%m-%d")
	r = requests.get(url_divi)
	div_price = r.json().get('lines')

	# get maps
	url_map = "http://api.poe.ninja/api/Data/GetMapOverview?league=Legacy&date=" + time.strftime("%Y-%m-%d")
	r = requests.get(url_map)
	map_price = r.json().get('lines')

	# get flask
	url_map = "http://cdn.poe.ninja/api/Data/GetUniqueFlaskOverview?league=Legacy&date=" + time.strftime("%Y-%m-%d")
	r = requests.get(url_map)
	flask_price = r.json().get('lines')


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
