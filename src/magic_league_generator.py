from datetime import datetime
from re import S
from tkinter import Button, Frame, StringVar, Tk, E, N, W
from tkinter.messagebox import showinfo, showwarning
from tkinter.ttk import Combobox, Entry, Label
from generator import Generator, Mode
from generator_config import GeneratorConfigFile, ConfigKey
from mtga.set_data import all_mtga_cards
from pyperclip import copy, paste

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
        self.generator = Generator(all_mtga_cards)
        self.sets = [""]
        for set in self.generator.get_sets():
            if self.generator.sealedable(set):
                self.sets.append(set)
        self.sets.sort()
        self.config_file = GeneratorConfigFile(self.CONFIG_PATH)
        self.config = self.config_file.load()
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

        # GUI
        self.master.title(self.APP_NAME)
        self.master.geometry("380x260")
        self.master.protocol('WM_DELETE_WINDOW', self.close_window)
        self.master_frame = Frame(self.master)
        self.master_frame.pack()
        self.user_id_label = Label(self.master_frame, text="ユーザー名#ID番号: ", anchor="w")
        self.user_id_label.grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.user_id_entry = Entry(self.master_frame, textvariable=self.sv_user_id, width=32)
        self.user_id_entry.grid(row=0, column=1, sticky=W + E, padx=5, pady=5)
        self.set_label = Label(self.master_frame, text="セット: ", anchor="w")
        self.set_label.grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.sets_frame = Frame(self.master_frame)
        self.sets_frame.grid(row=1, column=1, sticky=W + E, padx=0, pady=0)
        self.set_comboboxs = []
        for i in range(len(self.config[ConfigKey.SETS])):
            self.set_comboboxs.append(Combobox(self.sets_frame, width=6, values=self.sets, textvariable=self.sv_sets[i], state="readonly"))
            self.set_comboboxs[i].current(self.sets.index(self.sv_sets[i].get()) if self.sv_sets[i].get() else 0)
            self.set_comboboxs[i].grid(row=0, column=i, sticky=W, padx=5, pady=5)
        self.pack_mode_label = Label(self.master_frame, text="パック数: ", anchor="w")
        self.pack_mode_label.grid(row=2, column=0, sticky=W + E + N, padx=5, pady=5)
        self.pack_frame = Frame(self.master_frame)
        self.pack_frame.grid(row=2, column=1, sticky=W + E, padx=0, pady=0)
        self.pack_num_entries = []
        for i in range(len(self.config[ConfigKey.PACK_NUMS])):
            self.pack_num_entries.append(Entry(self.pack_frame, textvariable=self.sv_pack_nums[i], width=9))
            self.pack_num_entries[i].grid(row=0, column=i, sticky=W, padx=5, pady=5)
        self.pack_mode_combobox = Combobox(self.pack_frame, width=6, values=self.PACK_MODES, textvariable=self.sv_pack_mode, state="readonly")
        self.pack_mode_combobox.current(self.PACK_MODES.index(self.sv_pack_mode.get()) if self.sv_pack_mode.get() else 0)
        self.pack_mode_combobox.bind('<<ComboboxSelected>>', self.change_pack_mode)
        self.pack_mode_combobox.grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.mode_label = Label(self.master_frame, text="モード: ", anchor="w")
        self.mode_label.grid(row=3, column=0, sticky=W, padx=5, pady=5)
        self.mode_combobox = Combobox(self.master_frame, width=6, values=list(self.MODES.values()), textvariable=self.sv_mode, state="readonly")
        self.mode_combobox.current(self.get_mode_value_index(self.sv_mode.get()) if self.sv_mode.get() else 0)
        self.mode_combobox.bind('<<ComboboxSelected>>', self.change_mode)
        self.mode_combobox.grid(row=3, column=1, sticky=W, padx=5, pady=5)
        self.start_time_label = Label(self.master_frame, text="基準開始日時: ", anchor="w")
        self.start_time_label.grid(row=4, column=0, sticky=W, padx=5, pady=5)
        self.start_time_frame = Frame(self.master_frame)
        self.start_time_frame.grid(row=4, column=1, sticky=W + E, padx=0, pady=0)
        self.start_time_entry = Entry(self.start_time_frame, textvariable=self.sv_start_time, width=24)
        self.start_time_entry.grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.start_time_button = Button(self.start_time_frame, text="現在日時", command=self.set_start_time_now)
        self.start_time_button.grid(row=0, column=1, sticky=W + E, padx=5, pady=5)
        self.end_time_label = Label(self.master_frame, text="基準終了日時: ", anchor="w")
        self.end_time_label.grid(row=5, column=0, sticky=W, padx=5, pady=5)
        self.end_time_entry = Entry(self.master_frame, textvariable=self.sv_end_time, width=24, state='disabled')
        self.end_time_entry.grid(row=5, column=1, sticky=W, padx=5, pady=5)
        self.export_button = Button(self.master_frame, text="エクスポート", command=self.export)
        self.export_button.grid(row=6, column=0, sticky=W + E, padx=5, pady=5)
        self.validate_button = Button(self.master_frame, text="クリップボードから検証", command=self.validate)
        self.validate_button.grid(row=6, column=1, sticky=W + E, padx=5, pady=5)
        self.update_window()

    def close_window(self):
        self.save_config()
        self.master.destroy()

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

    def export(self):
        self.save_config()
        picked_cards = []
        try:
            for i in range(len(self.config.get(ConfigKey.SETS))):
                if not self.sv_sets[i].get() or not self.sv_pack_nums[i].get():
                    continue
                picked_set_cards = self.generator.open_boosters(
                    user_id=self.sv_user_id.get(),
                    set=self.sv_sets[i].get(),
                    mode=self.get_mode_key(self.sv_mode.get()),
                    pack_num=int(self.sv_pack_nums[i].get()),
                    index_dt=
                        datetime.strptime(self.sv_start_time.get(), self.DT_FORMAT)
                        if self.get_mode_key(self.sv_mode.get()) == Mode.STATIC
                        else None
                )
                picked_set_cards = self.generator.sort_cards_by_set_number(picked_set_cards)
                picked_cards += picked_set_cards

            decklist = self.generator.cards_to_decklist(picked_cards)
            copy(decklist)
            print(paste())
            showinfo(self.APP_NAME, message="カードプールがクリップボードにコピーされました。")
        except ValueError as e:
            showwarning(self.APP_NAME, message="カードプールの生成に失敗しました。\nパック数や基準開始日時が不正でないか確認してください。\n" + str(e))

    def validate(self):
        self.save_config()
        invalid_cards = []
        decklist = paste()
        if decklist:
            sets = []
            pack_nums = []
            for i in range(len(self.config.get(ConfigKey.SETS))):
                sets.append(self.sv_sets[i].get())
                pack_nums.append(int(self.sv_pack_nums[i].get()))
            invalid_cards = self.generator.validate_decklist(
                user_id=self.sv_user_id.get(),
                sets=sets,
                decklist=decklist,
                mode=self.get_mode_key(self.sv_mode.get()),
                pack_nums=pack_nums,
                index_dt=
                    datetime.strptime(self.sv_start_time.get(), self.DT_FORMAT)
                    if self.get_mode_key(self.sv_mode.get()) == Mode.STATIC
                    else None
            )
            if not invalid_cards:
                showinfo(self.APP_NAME, message="デッキリストは適正です。")
            else:
                showwarning(self.APP_NAME, message="以下のカードが不正です。\n"+str(invalid_cards))
        else:
            showwarning(self.APP_NAME, message="クリップボードが空です。")
        
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
        self.config_file.save(self.config)

    def run(self):
        self.master.mainloop()

if __name__ == "__main__":
    #param = sys.argv
    root = Tk()
    app = GeneratorApp(master=root)
    app.run()
