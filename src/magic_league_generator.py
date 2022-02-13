from tkinter import Button, Frame, StringVar, Tk, E, W
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
        self.APP_NAME = "Magic League Generator"
        self.CONFIG_PATH = "config\\config.json"
        self.MODES = [Mode.RANDOM, Mode.DAILY, Mode.WEEKLY, Mode.MONTHLY]

        # 変数
        self.generator = Generator(all_mtga_cards)
        self.sets = []
        for set in self.generator.get_sets():
            if self.generator.sealedable(set):
                self.sets.append(set)
        self.sets.sort()
        self.config_file = GeneratorConfigFile(self.CONFIG_PATH)
        self.config = self.config_file.load()
        self.sv_user_id = StringVar(value=self.config.get(ConfigKey.USER_ID))
        self.sv_set = StringVar(value=self.config.get(ConfigKey.SET) if self.config.get(ConfigKey.SET) in self.sets else None)
        self.sv_mode = StringVar(value=self.config.get(ConfigKey.MODE))

        # GUI
        self.master.title(self.APP_NAME)
        self.master.geometry("380x140")
        self.master_frame = Frame(self.master)
        self.master_frame.pack()
        self.user_id_label = Label(self.master_frame, text="ユーザー名#ID番号: ", anchor="w")
        self.user_id_label.grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.user_id_entry = Entry(self.master_frame, textvariable=self.sv_user_id, width=32)
        self.user_id_entry.grid(row=0, column=1, sticky=W + E, padx=5, pady=5)
        self.set_label = Label(self.master_frame, text="セット: ", anchor="w")
        self.set_label.grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.set_combobox = Combobox(self.master_frame, width=16, values=self.sets, textvariable=self.sv_set, state="readonly")
        self.set_combobox.current(self.sets.index(self.sv_set.get()) if self.sv_set.get() else 0)
        self.set_combobox.grid(row=1, column=1, sticky=W, padx=5, pady=5)
        self.mode_label = Label(self.master_frame, text="モード: ", anchor="w")
        self.mode_label.grid(row=2, column=0, sticky=W, padx=5, pady=5)
        self.mode_combobox = Combobox(self.master_frame, width=8, values=self.MODES, textvariable=self.sv_mode, state="readonly")
        self.mode_combobox.current(self.MODES.index(self.sv_mode.get()) if self.sv_mode.get() else 0)
        self.mode_combobox.grid(row=2, column=1, sticky=W, padx=5, pady=5)
        self.export_button = Button(self.master_frame, text="エクスポート", command=self.export)
        self.export_button.grid(row=3, column=0, sticky=W + E, padx=5, pady=5)
        self.validate_button = Button(self.master_frame, text="クリップボードから検証", command=self.validate)
        self.validate_button.grid(row=3, column=1, sticky=W + E, padx=5, pady=5)
    
    def export(self):
        self.save_config()
        picked_cards = self.generator.open_boosters(
            user_id=self.config.get(ConfigKey.USER_ID),
            set=self.config.get(ConfigKey.SET),
            mode=self.config.get(ConfigKey.MODE)
        )
        decklist = self.generator.cards_to_decklist(picked_cards)
        copy(decklist)
        print(paste())
        showinfo(self.APP_NAME, message="カードプールがクリップボードにコピーされました。")

    def validate(self):
        self.save_config()
        decklist = paste()
        if decklist:
            invalid_cards = self.generator.validate_decklist(self.config.get(ConfigKey.USER_ID), self.config.get(ConfigKey.SET), decklist)
            if not invalid_cards:
                showinfo(self.APP_NAME, message="デッキリストは適正です。")
            else:
                showwarning(self.APP_NAME, message="以下のカードが不正です。\n"+str(invalid_cards))
        else:
            showwarning(self.APP_NAME, message="クリップボードが空です。")
        
    def save_config(self):
        self.config[ConfigKey.USER_ID] = self.sv_user_id.get()
        self.config[ConfigKey.SET] = self.sv_set.get()
        self.config[ConfigKey.MODE] = self.sv_mode.get()
        self.config_file.save(self.config)

    def run(self):
        self.master.mainloop()

if __name__ == "__main__":
    #param = sys.argv
    root = Tk()
    app = GeneratorApp(master=root)
    app.run()
    app.save_config()
