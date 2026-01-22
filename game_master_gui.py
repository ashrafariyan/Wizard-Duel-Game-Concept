# hogwarts_duel_safe.py
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import random
import os

# -------------------- CONFIG --------------------
CANVAS_WIDTH = 700
CANVAS_HEIGHT = 400
PLAYER_POS = (150, 300)
ENEMY_POS = (550, 100)
HP_BAR_WIDTH = 80
HP_BAR_HEIGHT = 10

# -------------------- WIZARD STATE --------------------
class Wizard:
    def __init__(self, name, max_hp, spells):
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.spells = spells

player = Wizard("Harry", 50, ["Expelliarmus", "Stupefy", "Lumos"])
enemy = Wizard("Draco", 50, ["Serpensortia", "Stupefy"])

# -------------------- GUI --------------------
class DuelGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hogwarts Duel")
        self.geometry("800x550")

        # Canvas
        self.canvas = tk.Canvas(self, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
        self.canvas.pack(pady=10)

        # ---------- Paths ----------
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        bg_path = os.path.join(BASE_DIR, "assets", "duel_bg.jpeg")  # <-- updated to .jpeg
        player_path = os.path.join(BASE_DIR, "assets", "player_wizard.png")
        enemy_path = os.path.join(BASE_DIR, "assets", "enemy_wizard.png")

        # ---------- Load Images Safely ----------
        self.bg_photo = self.load_image(bg_path, CANVAS_WIDTH, CANVAS_HEIGHT)
        self.player_photo = self.load_image(player_path, 80, 80)
        self.enemy_photo = self.load_image(enemy_path, 80, 80)

        # Draw images
        self.canvas.create_image(0,0,image=self.bg_photo, anchor="nw")
        self.player_sprite = self.canvas.create_image(*PLAYER_POS, image=self.player_photo, anchor="center")
        self.enemy_sprite = self.canvas.create_image(*ENEMY_POS, image=self.enemy_photo, anchor="center")

        # HP bars
        self.player_hp_bg = self.canvas.create_rectangle(PLAYER_POS[0]-HP_BAR_WIDTH//2,
                                                         PLAYER_POS[1]-60,
                                                         PLAYER_POS[0]+HP_BAR_WIDTH//2,
                                                         PLAYER_POS[1]-60+HP_BAR_HEIGHT,
                                                         fill="grey")
        self.player_hp_fg = self.canvas.create_rectangle(PLAYER_POS[0]-HP_BAR_WIDTH//2,
                                                         PLAYER_POS[1]-60,
                                                         PLAYER_POS[0]-HP_BAR_WIDTH//2 + HP_BAR_WIDTH,
                                                         PLAYER_POS[1]-60+HP_BAR_HEIGHT,
                                                         fill="green")

        self.enemy_hp_bg = self.canvas.create_rectangle(ENEMY_POS[0]-HP_BAR_WIDTH//2,
                                                        ENEMY_POS[1]-60,
                                                        ENEMY_POS[0]+HP_BAR_WIDTH//2,
                                                        ENEMY_POS[1]-60+HP_BAR_HEIGHT,
                                                        fill="grey")
        self.enemy_hp_fg = self.canvas.create_rectangle(ENEMY_POS[0]-HP_BAR_WIDTH//2,
                                                        ENEMY_POS[1]-60,
                                                        ENEMY_POS[0]-HP_BAR_WIDTH//2 + HP_BAR_WIDTH,
                                                        ENEMY_POS[1]-60+HP_BAR_HEIGHT,
                                                        fill="green")

        # Status label
        self.status_var = tk.StringVar(value="Your turn!")
        self.status_label = ttk.Label(self, textvariable=self.status_var, font=("Helvetica", 12))
        self.status_label.pack(pady=5)

        # Spell buttons
        self.spell_frame = ttk.Frame(self)
        self.spell_frame.pack(pady=5)
        self.spell_buttons = []
        for spell in player.spells:
            btn = ttk.Button(self.spell_frame, text=spell, command=lambda s=spell: self.player_attack(s))
            btn.pack(side="left", padx=5)
            self.spell_buttons.append(btn)

        self.turn = "player"

    # ---------- SAFE IMAGE LOADING ----------
    def load_image(self, path, width, height):
        if not os.path.isfile(path):
            messagebox.showerror("Image Not Found", f"Cannot find image: {path}\nMake sure it exists in the assets folder.")
            self.destroy()
            exit()
        img = Image.open(path).resize((width, height))
        return ImageTk.PhotoImage(img)

    # -------------------- HP BAR UPDATE --------------------
    def update_hp_bar(self, wizard, bar_fg):
        hp_width = HP_BAR_WIDTH * (wizard.hp / wizard.max_hp)
        coords = self.canvas.coords(bar_fg)
        x1, y1 = coords[0], coords[1]
        self.canvas.coords(bar_fg, x1, y1, x1 + hp_width, y1 + HP_BAR_HEIGHT)

    # -------------------- SPELL ANIMATION --------------------
    def animate_spell(self, spell_name, player_to_enemy=True):
        colors = {"Expelliarmus":"red", "Stupefy":"blue", "Lumos":"yellow",
                  "Serpensortia":"purple"}
        color = colors.get(spell_name, "white")

        if player_to_enemy:
            start_x, start_y = PLAYER_POS
            target_x, target_y = ENEMY_POS
        else:
            start_x, start_y = ENEMY_POS
            target_x, target_y = PLAYER_POS

        target_x += random.randint(-10,10)
        target_y += random.randint(-10,10)

        spell_id = self.canvas.create_oval(start_x-10, start_y-10, start_x+10, start_y+10, fill=color, outline="")

        steps = 30
        dx = (target_x - start_x)/steps
        dy = (target_y - start_y)/steps

        def move_step(step=0):
            if step < steps:
                self.canvas.move(spell_id, dx, dy)
                self.after(15, lambda: move_step(step+1))
            else:
                flash = self.canvas.create_oval(target_x-15,target_y-15,target_x+15,target_y+15,fill="white",outline="")
                self.after(150, lambda: self.canvas.delete(spell_id))
                self.after(200, lambda: self.canvas.delete(flash))
                self.apply_damage(player_to_enemy)
        move_step()

    # -------------------- APPLY DAMAGE --------------------
    def apply_damage(self, player_to_enemy):
        dmg = random.randint(5,10)
        if player_to_enemy:
            enemy.hp = max(0, enemy.hp - dmg)
            self.update_hp_bar(enemy, self.enemy_hp_fg)
            self.status_var.set(f"{enemy.name} took {dmg} damage!")
        else:
            player.hp = max(0, player.hp - dmg)
            self.update_hp_bar(player, self.player_hp_fg)
            self.status_var.set(f"{player.name} took {dmg} damage!")

        if enemy.hp <= 0:
            messagebox.showinfo("Victory", "You won the duel!")
            self.disable_spells()
        elif player.hp <= 0:
            messagebox.showinfo("Defeat", "You lost the duel!")
            self.disable_spells()
        else:
            if player_to_enemy:
                self.after(500, self.enemy_attack)

    # -------------------- PLAYER ATTACK --------------------
    def player_attack(self, spell_name):
        if self.turn != "player":
            return
        self.status_var.set(f"You cast {spell_name}!")
        self.animate_spell(spell_name, player_to_enemy=True)
        self.turn = "enemy"
        self.disable_spells()

    # -------------------- ENEMY ATTACK --------------------
    def enemy_attack(self):
        spell = random.choice(enemy.spells)
        self.status_var.set(f"{enemy.name} casts {spell}!")
        self.animate_spell(spell, player_to_enemy=False)
        self.turn = "player"
        self.enable_spells()

    # -------------------- UTILITY --------------------
    def disable_spells(self):
        for btn in self.spell_buttons:
            btn.config(state="disabled")
    def enable_spells(self):
        for btn in self.spell_buttons:
            btn.config(state="normal")

# -------------------- RUN --------------------
if __name__=="__main__":
    app = DuelGUI()
    app.mainloop()
