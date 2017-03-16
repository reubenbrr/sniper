import time
import requests
import re
import sys
import datetime
from datetime import datetime
import os.path
import configparser, os
import json
from pprint import pprint

armor_price = []
weps_price = []
div_price = []
map_price = []
flask_price = []

def get_config():
	with open('config.json') as config:
		data = json.load(config)
		print('Config loaded:\n')
		print(data)
		return(data)

config = get_config()

def get_item_value(itemName, itemClass):
	global armor_price
	global weps_price
	global div_price
	global map_price
	global flask_price

	for armor in armor_price:
		if armor.get('name') == itemName and armor.get('itemClass') == itemClass:
			return float(armor.get('chaosValue'))

	for weps in weps_price:
		if weps.get('name') == itemName and weps.get('itemClass') == itemClass:
			return float(weps.get('chaosValue'))

	for div in div_price:
		if div.get('name') == itemName:
			return float(div.get('chaosValue'))

	for map in map_price:
		if map.get('name') == itemName:
			return float(map.get('chaosValue'))

	for flask in flask_price:
		if flask.get('name') == itemName:
			return float(map.get('chaosValue'))

	return 0

def getFrameType(frameType):
	if frameType == 3: return "Unique"
	if frameType == 4: return "Gem"
	if frameType == 5: return "Currency"
	if frameType == 6: return "Divination Card"
	if frameType == 9: return "Relic"

	return frameType

def writeFile(text):
	t = ''
	for k,v in text.items():
		if k is not 'msg':
			t += str(k)
			t += ': '
		t += str(v)
		t += '\n'
	with open (config['Output']['FileName']+'.log', "a+") as f:
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
			pass
		except:
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
		accountName = stash['accountName']
		lastCharacterName =  stash['lastCharacterName']
		items = stash['items']
		stashName = stash.get('stash')

		# scan items
		for item in items:

			if item.get('league') == 'Legacy':
				typeLine = item.get('typeLine', None)
				name = re.sub(r'<<.*>>', '', item.get('name',None))
				price = item.get('note', None)
				frameType = item.get('frameType', None)
				sockets = item.get('sockets')
				sockets_count = len(sockets)
				links_count = links(sockets)

				# for divination
				if name is None or name == "":
					name = typeLine

				## compare unique that worth at least 1 chaos.
				if price and name and 'chaos' in price:
					try:
						if not re.findall(r'\d+', price)[0]:
							continue
					except:
						continue

					price_normalized = float(re.findall(r'\d+', price)[0])

					item_value = get_item_value(name, frameType)

					# File output setup
					if item_value is not 0 and (item_value - price_normalized) > 3.0 and price_normalized is not 0:
						if 'Atziri' in name or 'Sadima' in name or 'Drillneck' in name:
							continue

						# If config set to hide corrupted gear
						# if config['Filter']['ShowCorrupted'] is 'true' and (frameType is 'Relic' or 'Unique' and item.get('corrupted') == True):
						# 	print(config.Filter.ShowCorrupted)
						# 	continue
						# else:
						# 	print(config.Filter.ShowCorrupted)

						# If item cannot be 6socketed
						# if (frameType is 'Relic' or 'Unique' and item.get('ilvl') < config['Filter']['MinIlvl']):
						# 	continue

						price = price.replace("~b/o ", "")
						price = price.replace("~price ", "")

						try:
							#time_scanned = datetime.now().time()
							cost_vs_average = "{}c/{}c".format(price_normalized, item_value)
							perc_decrease = ((item_value - price_normalized) / item_value) * 100
							prefix = "[{} - {}c/{}c - {}%]".format(getFrameType(frameType), price_normalized, item_value, round(perc_decrease))
							profit = round(item_value - price_normalized)
							msg = "@{} Hi, I would like to buy your {} listed for {} in Legacy (stash tab \"{}\"; position: left {}, top {})".format(
								lastCharacterName, name, price, stashName, item.get('x'), item.get('y')
							)
							console = "{} [{} - {}] {}-{}%".format(lastCharacterName, getFrameType(frameType), name, cost_vs_average, round(perc_decrease))

							file_content = {
								'Corrupted': item.get('corrupted'),
								'Profit': '{}c'.format(profit),
								'Cost': '{} - {}%'.format(cost_vs_average, round(perc_decrease)),
								'Type': getFrameType(frameType),
								'Info': '{}S {}L'.format(sockets_count, links_count),
								'ILVL': item.get('ilvl'),
								'msg': msg
							}

							if perc_decrease >= 90 and perc_decrease <= 99:
								print('\a\a\a')
								print(console)
								try:
									writeFile(file_content)
								except:
									print('error writing file')
							elif perc_decrease >= 30:
								print('\a')
								print(console)
								try:
									writeFile(file_content)
								except:
									print('error writing file')
							elif perc_decrease >= 10:
								print(console)
								try:
									writeFile(file_content)
								except:
									print('error writing file')

						except:
							pass

						#pprint(stash)

def main():
	global armor_price
	global weps_price
	global div_price
	global map_price
	global flask_price

	print("Gimme gimme gimme....")
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
			r = requests.get(url_api, params = params)

			## parsing structure
			data = r.json()

			## setting next change id
			next_change_id = data['next_change_id']

			## attempt to find items...
			find_items(data['stashes'])

			## wait 5 seconds until parsing next structure
			time.sleep(0)
		except KeyboardInterrupt:
			print("Closing Sniper")
			sys.exit(1)
		except:
			pass


if __name__ == "__main__":
    main()
