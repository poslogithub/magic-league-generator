from threading import Thread
import mtgsdk_wrapper
import scrython_wrapper

def get_set_cards(set, sdk):
    sdk.get_set_cards(set)

sets = ['NEO', 'SNC', 'AFR', 'KHM']

"""
sdk = mtgsdk_wrapper.MtgSdk()
for set in sets:
    get_set_cards(set, sdk)
"""

sdk = scrython_wrapper.ScrythonWrapper()
for set in sets:
    get_set_cards(set, sdk)

""" ScrythonではNG
threads = []
for set in sets:
    sdk = scrython_wrapper.Scrython()
    thread = Thread(target=get_set_cards, args=(set, sdk), daemon=True)
    thread.start()
    threads.append(thread)
for thread in threads:
    thread.join()
"""
"""
sdk = mtgsdk_wrapper.MtgSdk()
threads = []
for set in sets:
    thread = Thread(target=get_set_cards, args=(set, sdk), daemon=True)
    thread.start()
    threads.append(thread)
for thread in threads:
    thread.join()
"""