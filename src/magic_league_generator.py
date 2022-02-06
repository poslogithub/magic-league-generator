from generator import Generator, Rarity
from mtga.set_data import all_mtga_cards
import pyperclip


""" 
例：全カード取得
cards = all_mtga_cards.get_cards()
print(len(cards))
print(cards[0].set)
"""

""" cards = generator.get_cards(set="VOW")
for card in cards:
    print(card.pretty_name + "\t" + str(card.set_number) + "\t" + str(card.mtga_id))
print(len(cards))
 """
if __name__ == "__main__":
    user_id = "username#00000"
    set = "VOW"
    generator = Generator(all_mtga_cards)
    picked_cards = generator.open_monthly_boosters(user_id, set)
    decklist = generator.cards_to_decklist(picked_cards)
    print(pyperclip.paste())
    invalid_cards = generator.validate_decklist(user_id, set, pyperclip.paste())
    print(invalid_cards)
"""     for card in picked_cards:
        print(card.pretty_name) """

""" for card_set_obj, all_abilities in dynamic.dynamic_set_tuples:
    print(card_set_obj.set_name) """
