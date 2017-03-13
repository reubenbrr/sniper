import time
import requests
import re
import sys
from termcolor import colored, cprint
from pprint import pprint


armor_price = []
weps_price = []
div_price = []
map_price = []
flask_price = []

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
	if frameType == 3: return "UNI"
	if frameType == 4: return "GEM"
	if frameType == 5: return "CUR"
	if frameType == 6: return "DIV"
	if frameType == 9: return "LEG"

	return frameType


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

				# for divination
				if name is None or name == "":
					name = typeLine

				#if "Rain of" in name or "Map" in name:
				#	print (name, get_item_value(name, frameType))

				## compare unique that worth at least 1 chaos.
				if price and name and 'chaos' in price:
					try:
						if not re.findall(r'\d+', price)[0]:
							continue
					except:
						continue

					price_normalized = float(re.findall(r'\d+', price)[0])
					item_value = get_item_value(name, frameType)

					if item_value is not 0 and (item_value - price_normalized) > 3.0 and price_normalized is not 0:
						if 'Atziri' in name or 'Sadima' in name or 'Drillneck' in name:
							continue


						price = price.replace("~b/o ", "")
						price = price.replace("~price ", "")


						try:

							perc_decrease = ((item_value - price_normalized) / item_value) * 100

							msg = "[{} - {}c/{}c - {}%] @{} Hi, I would like to buy your {} listed for {} in Legacy (stash tab \"{}\"; position: left {}, top {}) -- {}".format(
								getFrameType(frameType), price_normalized, item_value, round(perc_decrease),

								lastCharacterName, name, price, stashName, item.get('x'), item.get('y'), item.get('note')
							)

							if perc_decrease >= 50:
								cprint(msg, 'red')
							elif perc_decrease >= 30:
								cprint(msg, 'yellow')
							elif frameType >= 20:
								cprint(msg, 'green')
							elif frameType >= 10:
								cprint(msg, 'white')
							#else:
								#print(msg)

						except:
							pass

						#pprint(stash)

def main():
	global armor_price
	global weps_price
	global div_price
	global map_price
	global flask_price

	print("Searching for mispriced items..." )
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
		params = {'id': next_change_id}
		r = requests.get(url_api, params = params)

		## parsing structure
		data = r.json()

		## setting next change id
		next_change_id = data['next_change_id']

		## attempt to find items...
		find_items(data['stashes'])

		## wait 5 seconds until parsing next structure
		time.sleep(1)

if __name__ == "__main__":
    main()