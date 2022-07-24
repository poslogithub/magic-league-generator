from os import makedirs
from os.path import exists, join
from urllib.request import urlopen
from PIL import Image
from io import BytesIO
from sys import _getframe
from threading import Thread
from time import sleep
from scrython_wrapper import ScrythonWrapper

from traceback import print_exc

class CardImageDownloader():
    FORMATS = {
        'PNG': '.png',
        'JPEG': '.jpg',
        'GIF': '.gif',
        'BMP': '.bmp',
        'DIB': '.dib',
        'TIFF': '.tiff',
        'PPM': '.ppm'
    }

    IMAGE_DIR = 'card_image'
    CARD_WIDTH = 265
    CARD_HEIGHT = 370
    ALPHA_CHANNEL_PATH = 'alpha_channel.png'


    def __init__(self, wrapper=None, image_dir=None):
        self.wrapper = wrapper if wrapper else ScrythonWrapper()
        self.image_dir = image_dir if image_dir else self.IMAGE_DIR
    

    def get_card_images(self, set_number_backs):    # set_number_backs: [(set, number, back), ...]
        urls = []
        for set_number_back in set_number_backs:
            url = self.wrapper.get_card_image_url(set_number_back[0], set_number_back[1], set_number_back[2])
            urls.append(url)
        
        self.images = list(range(len(set_number_backs)))
        threads = []
        for i in range(len(set_number_backs)):
            thread = Thread(target=self.get_card_image, args=(set_number_backs[i][0], set_number_backs[i][1], set_number_backs[i][2], urls[i], i), daemon=True)
            thread.start()
            threads.append(thread)
            sleep(0.1)
        
        for i in range(len(threads)):
            threads[i].join(60)
            if threads[i].is_alive():
                print('Timeout occured @ {}.{} {}({}, {}, {}, {}, {})'.format(self.__class__, _getframe().f_code.co_name, 'get_card_image', set_number_backs[i][0], set_number_backs[i][1], set_number_backs[i][2], urls[i], i))
                return None
        
        return self.images


    def get_card_image(self, set, number, back, url, i):
        set_dir = join(self.image_dir, set)
        is_exist = False
        if not exists(set_dir):
            try:
                makedirs(set_dir, exist_ok=True)
            except:
                print_exc()
                self.images[i] = None
                return None
        else:
            for format in self.FORMATS.values():
                image_path = join(set_dir, str(number)+('b' if back else '')+format)
                if exists(image_path):
                    is_exist = True
                    break

        if not is_exist:
            try:
                with urlopen(url, timeout=60) as response:
                    image_data = response.read()
            except:
                print_exc()
                print('{}, {}, {}, {}, {}'.format(set, number, back, url, i))
                self.images[i] = None
                return None
            
            try:
                with Image.open(BytesIO(image_data)) as image:
                    if image.width != self.CARD_WIDTH or image.height != self.CARD_HEIGHT:
                        image = image.resize((self.CARD_WIDTH, self.CARD_HEIGHT))
                    format = image.format
                    if format != 'PNG':
                        try:
                            with Image.open(self.ALPHA_CHANNEL_PATH).convert('L') as alpha_channel:
                                image.putalpha(alpha_channel)
                        except:
                            print_exc()
                    ext = self.FORMATS.get(format)
                    if ext:
                        image_path = join(set_dir, str(number)+('b' if back else '')+self.FORMATS.get('PNG'))
                        try:
                            image.save(image_path)
                            print('{} has been saved.'.format(image_path))
                        except:
                            print_exc()
                            self.images[i] = None
                    else:
                        print('Unknown image format {} @ {}.{}'.format(format, self.__class__, _getframe().f_code.co_name))
                        self.images[i] = None
            except:
                print_exc()
                self.images[i] = None
                
        try:
            return Image.open(image_path)
        except:
            print_exc()
            return None


if __name__ == "__main__":
    from scrython_wrapper import ScrythonWrapper
    from mtgsdk_wrapper import MtgSdkWrapper
    from mtgjson_wrapper import MtgJsonWrapper

    #param = sys.argv
    downloader_scrython = CardImageDownloader(wrapper=ScrythonWrapper())
    downloader_mtgsdk = CardImageDownloader(wrapper=MtgSdkWrapper())
    downloader_mtgjson = CardImageDownloader(wrapper=MtgJsonWrapper())

    set_number_backs = [
        ['NEO', 1, False],
        ['NEO', 2, False],
        ['NEO', 3, False],
        ['NEO', 4, False],
        ['NEO', 5, False],
        ['NEO', 6, False],
        ['NEO', 7, False],
        ['NEO', 8, False],
        ['NEO', 9, False],
        ['NEO', 10, False]
    ]
    downloader_scrython.get_card_images(set_number_backs)

    set_number_backs = [
        ['SNC', 1, False],
        ['SNC', 2, False],
        ['SNC', 3, False],
        ['SNC', 4, False],
        ['SNC', 5, False],
        ['SNC', 6, False],
        ['SNC', 7, False],
        ['SNC', 8, False],
        ['SNC', 9, False],
        ['SNC', 10, False]
    ]
    downloader_mtgsdk.get_card_images(set_number_backs)

    set_number_backs = [
        ['KHM', 1, False],
        ['KHM', 2, False],
        ['KHM', 3, False],
        ['KHM', 4, False],
        ['KHM', 5, False],
        ['KHM', 6, False],
        ['KHM', 7, False],
        ['KHM', 8, False],
        ['KHM', 9, False],
        ['KHM', 10, False]
    ]
    downloader_mtgjson.get_card_images(set_number_backs)
