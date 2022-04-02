from hashlib import md5
from urllib.request import urlopen
from mtgsdk import Card
from PIL import Image
from io import BytesIO

CARD_BACK_IMAGE_MD5 = 'db0c48db407a907c16ade38de048a441'

cards = Card.where(set='NEO').where(number=226).all()    # 漆月魁渡

name = None
image_url = None
for card in cards:
	if card.foreign_names:
		for foreign_name in card.foreign_names:
			if foreign_name['language'] == 'Japanese':
				image_url = foreign_name['imageUrl']
				if image_url:
					with urlopen(url=image_url) as response:
						image_data = response.read()
						content_type = response.info()['Content-Type']
						format = Image.open(BytesIO(image_data)).format
						print('Content-Type: '+content_type)
						print('Format: '+format)
						if md5(image_data).hexdigest() != CARD_BACK_IMAGE_MD5:
							name = foreign_name['name']
						else:
							image_url = None
				break
	if image_url is None:
		name = card.name
		image_url = card.image_url
	if image_url:
		break

print(name, card.set, card.number, image_url)