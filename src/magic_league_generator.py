from cmath import pi
from datetime import datetime
from tkinter import Button, Frame, LabelFrame, StringVar, Tk, E, N, W
from tkinter.filedialog import askdirectory, asksaveasfilename
from tkinter.messagebox import askyesno, showinfo, showwarning
from tkinter.ttk import Combobox, Entry, Label
from generator import Generator, Mode
from generator_config import GeneratorConfigFile, ConfigKey
from pyperclip import copy, paste
from os.path import dirname, sep
from subprocess import Popen

class GeneratorApp(Frame):
    def __init__(self, master=None):
        super().__init__(master)

        # 定数
        self.APP_NAME = "Sealed Generator"
        self.CONFIG_PATH = "config\\config.json"
        self.MODES = {
            Mode.DAILY: "日次", 
            Mode.WEEKLY: "週次", 
            Mode.MONTHLY: "月次", 
            Mode.RANDOM: "ランダム", 
            Mode.STATIC: "固定"
        }
        self.PACK_MODES = ["自動", "手動"]
        self.DT_FORMAT = '%Y-%m-%d %H:%M:%S %z'

        # 変数
        self.config_file = GeneratorConfigFile(self.CONFIG_PATH)
        self.config = self.config_file.load()
        self.generator = Generator(json_dir=self.config.get(ConfigKey.JSON_DIR), image_dir=self.config.get(ConfigKey.IMAGE_DIR))
        self.sets = [""]
        for set in self.generator.get_sets():
            if self.generator.sealedable(set):
                self.sets.append(set)
        self.sets.sort()
        self.sv_user_id = StringVar(value=self.config.get(ConfigKey.USER_ID))
        self.sv_sets = []
        for i in range(len(self.config.get(ConfigKey.SETS))):
            self.sv_sets.append(StringVar(value=self.config.get(ConfigKey.SETS)[i] if self.config.get(ConfigKey.SETS)[i] in self.sets else None))
        self.sv_mode = StringVar(value=self.MODES.get(self.config.get(ConfigKey.MODE)))
        self.sv_pack_mode = StringVar(value=self.PACK_MODES[self.config.get(ConfigKey.PACK_MODE)])
        self.sv_pack_nums = []
        for i in range(len(self.config.get(ConfigKey.PACK_NUMS))):
            self.sv_pack_nums.append(StringVar(value=self.config.get(ConfigKey.PACK_NUMS)[i]))
        self.sv_start_time = StringVar()
        self.sv_end_time = StringVar()
        self.sv_card_image_cache_dir = StringVar(value=self.config.get(ConfigKey.IMAGE_DIR))

        # GUI
        self.master.title(self.APP_NAME)
        self.master.geometry("460x380")
        self.master.protocol('WM_DELETE_WINDOW', self.close_window)
        self.master_frame = Frame(self.master)
        self.master_frame.pack()
        ## カードプール生成
        self.pool_frame = LabelFrame(self.master_frame, text="カードプール生成", width=440, height=280)
        self.pool_frame.pack()
        self.pool_frame.propagate(False)
        self.pool_edit_frame = Frame(self.pool_frame)
        self.pool_edit_frame.pack()
        self.user_id_label = Label(self.pool_edit_frame, text="ユーザー名#ID番号: ", anchor="w")
        self.user_id_label.grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.user_id_entry = Entry(self.pool_edit_frame, textvariable=self.sv_user_id, width=32)
        self.user_id_entry.grid(row=0, column=1, sticky=W + E, padx=5, pady=5)
        self.set_pack_label_frame = Frame(self.pool_edit_frame)
        self.set_pack_label_frame.grid(row=1, column=0, sticky=W, padx=0, pady=0)
        self.set_label = Label(self.set_pack_label_frame, text="セット: ", anchor="w")
        self.set_label.grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.pack_num_label = Label(self.set_pack_label_frame, text="パック数: ", anchor="w")
        self.pack_num_label.grid(row=1, column=0, sticky=W + E + N, padx=5, pady=5)
        self.pack_mode_label = Label(self.set_pack_label_frame, text="", anchor="w")
        self.pack_mode_label.grid(row=2, column=0, sticky=W + E + N, padx=5, pady=5)
        self.sets_packes_frame = Frame(self.pool_edit_frame)
        self.sets_packes_frame.grid(row=1, column=1, sticky=W + E, padx=0, pady=0)
        self.set_comboboxs = []
        self.pack_num_entries = []
        for i in range(len(self.config[ConfigKey.SETS])):
            self.set_comboboxs.append(Combobox(self.sets_packes_frame, width=6, values=self.sets, textvariable=self.sv_sets[i], state="readonly"))
            self.set_comboboxs[i].current(self.sets.index(self.sv_sets[i].get()) if self.sv_sets[i].get() else 0)
            self.set_comboboxs[i].grid(row=0, column=i, sticky=W + E, padx=5, pady=5)
            self.pack_num_entries.append(Entry(self.sets_packes_frame, textvariable=self.sv_pack_nums[i], width=9))
            self.pack_num_entries[i].grid(row=1, column=i, sticky=W, padx=5, pady=5)
        self.pack_mode_combobox = Combobox(self.sets_packes_frame, width=6, values=self.PACK_MODES, textvariable=self.sv_pack_mode, state="readonly")
        self.pack_mode_combobox.current(self.PACK_MODES.index(self.sv_pack_mode.get()) if self.sv_pack_mode.get() else 0)
        self.pack_mode_combobox.bind('<<ComboboxSelected>>', self.change_pack_mode)
        self.pack_mode_combobox.grid(row=2, column=0, sticky=W, padx=5, pady=5)
        self.mode_label = Label(self.pool_edit_frame, text="モード: ", anchor="w")
        self.mode_label.grid(row=3, column=0, sticky=W, padx=5, pady=5)
        self.mode_combobox = Combobox(self.pool_edit_frame, width=6, values=list(self.MODES.values()), textvariable=self.sv_mode, state="readonly")
        self.mode_combobox.current(self.get_mode_value_index(self.sv_mode.get()) if self.sv_mode.get() else 0)
        self.mode_combobox.bind('<<ComboboxSelected>>', self.change_mode)
        self.mode_combobox.grid(row=3, column=1, sticky=W, padx=5, pady=5)
        self.start_time_label = Label(self.pool_edit_frame, text="基準開始日時: ", anchor="w")
        self.start_time_label.grid(row=4, column=0, sticky=W, padx=5, pady=5)
        self.start_time_frame = Frame(self.pool_edit_frame)
        self.start_time_frame.grid(row=4, column=1, sticky=W + E, padx=0, pady=0)
        self.start_time_entry = Entry(self.start_time_frame, textvariable=self.sv_start_time, width=24)
        self.start_time_entry.grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.start_time_button = Button(self.start_time_frame, text="現在日時", command=self.set_start_time_now)
        self.start_time_button.grid(row=0, column=1, sticky=W + E, padx=5, pady=5)
        self.end_time_label = Label(self.pool_edit_frame, text="基準終了日時: ", anchor="w")
        self.end_time_label.grid(row=5, column=0, sticky=W, padx=5, pady=5)
        self.end_time_entry = Entry(self.pool_edit_frame, textvariable=self.sv_end_time, width=24, state='disabled')
        self.end_time_entry.grid(row=5, column=1, sticky=W, padx=5, pady=5)
        self.export_frame = Frame(self.pool_frame)
        self.export_frame.pack()
        self.export_button = Button(self.export_frame, text="エクスポート", width=20, command=self.export)
        self.export_button.grid(row=0, column=0, sticky=W + E, padx=5, pady=5)
        self.validate_button = Button(self.export_frame, text="クリップボードから検証", width=20, command=self.validate)
        self.validate_button.grid(row=0, column=1, sticky=W + E, padx=5, pady=5)
        ## デッキリスト画像生成
        self.image_frame = LabelFrame(self.master_frame, text="デッキリスト画像生成", width=440, height=90)
        self.image_frame.pack()
        self.image_frame.propagate(False)
        self.image_edit_frame = Frame(self.image_frame)
        self.image_edit_frame.pack()
        self.card_image_cache_dir_label = Label(self.image_edit_frame, text="カード画像キャッシュフォルダ: ", anchor="w")
        self.card_image_cache_dir_label.grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.card_image_cache_dir_entry = Entry(self.image_edit_frame, textvariable=self.sv_card_image_cache_dir, width=32)
        self.card_image_cache_dir_entry.grid(row=0, column=1, sticky=W + E, padx=5, pady=5)
        self.card_image_cache_dir_button = Button(self.image_edit_frame, text="　参照　", command=self.ref_card_image_cache_dir)
        self.card_image_cache_dir_button.grid(row=0, column=2, sticky=W + E, padx=5, pady=5)
        self.export_image_frame = Frame(self.image_frame)
        self.export_image_frame.pack()
        self.export_deck_image_button = Button(self.export_image_frame, text="クリップボードからデッキリスト画像をエクスポート", width=40, command=self.export_deck_image)
        self.export_deck_image_button.grid(row=0, column=0, sticky=W + E, padx=5, pady=5)
        self.export_deck_image_button = Button(self.export_image_frame, text="セットのカード画像を全てダウンロード", width=40, command=self.download_set_card_images)
        #self.export_deck_image_button.grid(row=1, column=0, sticky=W + E, padx=5, pady=5)
        self.update_window()

    def close_window(self):
        self.save_config()
        self.master.destroy()
    
    def ref_card_image_cache_dir(self):
        path = askdirectory(initialdir=self.sv_card_image_cache_dir.get())
        if path:
            self.sv_card_image_cache_dir.set(path)

    def set_start_time_now(self):
        self.sv_start_time.set(datetime.now().replace(microsecond=0).astimezone().strftime(self.DT_FORMAT))

    def update_window(self, _=None):
        self.change_mode(_)
        self.change_pack_mode(_)
    
    def change_pack_mode(self, _=None):
        if self.PACK_MODES.index(self.pack_mode_combobox.get()) == 0:   # 自動の場合
            for i in range(len(self.config.get(ConfigKey.PACK_NUMS))):
                if i == 0:
                    self.sv_pack_nums[i].set(self.generator.get_pack_num(self.get_mode_key(self.sv_mode.get())))
                else:
                    self.sv_pack_nums[i].set(0)
                self.pack_num_entries[i].configure(state='disable')
        else:
            for i in range(len(self.config.get(ConfigKey.PACK_NUMS))):
                self.pack_num_entries[i].configure(state='normal')

    def change_mode(self, _=None):
        # STATICならば基準開始日時を更新する
        # TODO: configファイルにはUSTで保存して、表示するときはロケールに合わせて、generatorに渡すときはUSTで渡す
        if self.get_mode_key(self.sv_mode.get()) == Mode.STATIC:
            self.start_time_entry.configure(state='normal')
            self.start_time_button.configure(state='normal')
            if self.config.get(ConfigKey.INDEX_TIME):
                self.sv_start_time.set(self.config.get(ConfigKey.INDEX_TIME))
            if not self.sv_start_time.get():
                self.sv_start_time.set(datetime.now().replace(microsecond=0).astimezone().strftime(self.DT_FORMAT))
            if not self.sv_end_time.get():
                self.sv_end_time.set(datetime.now().replace(microsecond=0).astimezone().strftime(self.DT_FORMAT))
        else:
            self.sv_start_time.set(self.generator.get_index_datetime(self.get_mode_key(self.sv_mode.get())).astimezone().strftime(self.DT_FORMAT))
            self.sv_end_time.set(self.generator.get_next_index_datetime(self.get_mode_key(self.sv_mode.get())).astimezone().strftime(self.DT_FORMAT))
            self.start_time_entry.configure(state='disable')
            self.start_time_button.configure(state='disable')
        self.change_pack_mode(_)
        
        # RANDOMならば検証ボタンを無効化する
        if self.get_mode_key(self.sv_mode.get()) == Mode.RANDOM:
            self.validate_button.configure(state='disable')
        else:
            self.validate_button.configure(state='normal')

    def get_mode_key(self, mode_value):
        for key in self.MODES.keys():
            if self.MODES.get(key) == mode_value:
                return key
        return None

    def get_mode_key_index(self, mode_key):
        key_list = list(self.MODES.keys())
        key_list.index(mode_key)

    def get_mode_value_index(self, mode_value):
        value_list = list(self.MODES.values())
        value_list.index(mode_value)

    def get_sets(self):
        sets = {}
        for i in range(len(self.config.get(ConfigKey.SETS))):
            if self.sv_sets[i].get():
                sets[self.sv_sets[i].get()] = int(self.sv_pack_nums[i].get())
        return sets

    def get_pool(self, sets):
        try:
            pool = self.generator.open_boosters(
                user_id=self.sv_user_id.get(),
                sets=list(sets.keys()),
                pack_nums=list(sets.values()),
                mode=self.get_mode_key(self.sv_mode.get()),
                index_dt=
                    datetime.strptime(self.sv_start_time.get(), self.DT_FORMAT)
                    if self.get_mode_key(self.sv_mode.get()) == Mode.STATIC
                    else None
            )
            return pool
        except ValueError as e:
            showwarning(self.APP_NAME, message="カードプールの生成に失敗しました。\nパック数や基準開始日時が不正でないか確認してください。\n" + str(e))
            return None

    def export(self):
        self.save_config()
        sets = self.get_sets()
        picked_cards = self.get_pool(sets)
        decklist = self.generator.cards_to_decklist(picked_cards)
        copy(decklist)
        print(paste())
        showinfo(self.APP_NAME, message="カードプールがクリップボードにコピーされました。")

    def validate(self):
        self.save_config()
        invalid_cards = []
        decklist = paste()
        if decklist:
            sets = self.get_sets()
            pool = self.get_pool(sets)
            invalid_cards = self.generator.validate_decklist(decklist, pool)
            diff_cards = self.generator.get_diff_cards(pool, decklist)
            if not invalid_cards:
                if not diff_cards:
                    showinfo(self.APP_NAME, message="デッキリストは適正です。")
                else:
                    if askyesno(self.APP_NAME, message="デッキリストは適正です。\n不足カードをサイドボードに追加したデッキリストをエクスポートしますか？"):
                        decklist = self.generator.add_diff_to_sideboard(decklist, pool)
                        copy(decklist)
                        print(paste())
                        showinfo(self.APP_NAME, message="デッキリストがクリップボードにコピーされました。")
            else:
                if askyesno(self.APP_NAME, message="以下のカードが不正です。\n\n"+str(invalid_cards)+"\n\n不正カードを除外したデッキリストをエクスポートしますか？"):
                    decklist = self.generator.strip_invalid_cards_from_decklist(decklist, invalid_cards)
                    decklist = self.generator.add_diff_to_sideboard(decklist, pool)
                    copy(decklist)
                    print(paste())
                    showinfo(self.APP_NAME, message="カードプールがクリップボードにコピーされました。")

        else:
            showwarning(self.APP_NAME, message="クリップボードが空です。")
    
    def export_deck_image(self):
        self.save_config()
        decklist = paste()
        if decklist:
            image = self.generator.generate_decklist_image_from_decklist(decklist)
            image_path = asksaveasfilename(initialdir=self.config[ConfigKey.DECKLIST_IMAGE_OUTPUT_DIR], initialfile="decklist.png", filetypes=[("PNG", ".png")], defaultextension="png")
            if image_path:
                image_path = image_path.replace('/', sep)
                self.config[ConfigKey.DECKLIST_IMAGE_OUTPUT_DIR] = dirname(image_path)
                try:
                    image.save(image_path)
                    if askyesno(self.APP_NAME, message="デッキリスト画像を保存しました。\n保存先フォルダを開きますか？"):
                        Popen(['explorer', '/select,'+image_path])
                except Exception as e:
                    showwarning(self.APP_NAME, message="デッキリスト画像の保存に失敗しました。")
                    print(e.args, flush=True)

    def download_set_card_images(self):
        self.save_config()
        sets = self.get_sets()
        for set in sets.keys():
            self.generator.save_set_all_images(set)
        showinfo(self.APP_NAME, "ダウンロードが完了しました。")

        pass
    def save_config(self):
        self.config[ConfigKey.USER_ID] = self.sv_user_id.get()
        for i in range(len(self.config.get(ConfigKey.SETS))):
            self.config[ConfigKey.SETS][i] = self.sv_sets[i].get()
        self.config[ConfigKey.MODE] = self.get_mode_key(self.sv_mode.get())
        if self.get_mode_key(self.sv_mode.get()) == Mode.STATIC:    # モード指定が固定の場合のみ保存
            self.config[ConfigKey.INDEX_TIME] = self.sv_start_time.get()
        self.config[ConfigKey.PACK_MODE] = self.PACK_MODES.index(self.sv_pack_mode.get())
        if self.PACK_MODES.index(self.pack_mode_combobox.get()) == 1:   # パック数指定が手動の場合のみ保存
            for i in range(len(self.config.get(ConfigKey.PACK_NUMS))):
                self.config[ConfigKey.PACK_NUMS][i] = self.sv_pack_nums[i].get()
        self.config[ConfigKey.IMAGE_DIR] = self.sv_card_image_cache_dir.get()
        self.config_file.save(self.config)

    def run(self):
        self.master.mainloop()

if __name__ == "__main__":
    #param = sys.argv
    root = Tk()
    app = GeneratorApp(master=root)
    app.run()
