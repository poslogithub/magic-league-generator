from mtga.set_data import all_mtga_cards, dynamic

""" 
例：全カード取得
cards = all_mtga_cards.get_cards()
print(len(cards))
print(cards[0].set)
"""


"""
例：指定したセットのカードのみ取得
"""
cards = all_mtga_cards.get_real_cards(set="ZNR")
for card in cards:
    print(card.pretty_name + "\t" + str(card.set_number) + "\t" + str(card.mtga_id))
print(len(cards))

""" for card_set_obj, all_abilities in dynamic.dynamic_set_tuples:
    print(card_set_obj.set_name) """
