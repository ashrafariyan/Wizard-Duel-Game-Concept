import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk
import os, random, math
import copy

HP_BAR_WIDTH = 200
HP_BAR_HEIGHT = 20

class Character:
    def __init__(self, name, hp, spells, limited_uses=None):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.spells = spells
        self.status_effects = {}
        self.limited_uses = limited_uses if limited_uses else {}
        self.xp = 0
        self.level = 1
        self.next_level_xp = 50

    def cast_spell(self, spell):
        dmg_range, stype = self.spells[spell]
        return random.randint(*dmg_range), stype

    def gain_xp(self, amount):
        self.xp += amount
        leveled_up = False
        while self.xp >= self.next_level_xp:
            self.xp -= self.next_level_xp
            self.level += 1
            self.next_level_xp = int(self.next_level_xp * 1.5)
            leveled_up = True
        return leveled_up

class DuelGUI(tk.Tk):
    def __init__(self, player, initial_limited_uses):
        super().__init__()
        self.title("Hogwarts Duel")
        self.geometry("800x600")
        self.resizable(False, False)

        self.player = player
        self.initial_limited_uses = copy.deepcopy(initial_limited_uses)  # saved reset state
        self.player_defense = False
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        # Load background
        self.bg_img = Image.open(os.path.join(self.BASE_DIR, "assets", "duel_bg.jpeg")).resize((800, 400))
        self.bg = ImageTk.PhotoImage(self.bg_img)

        # Load player sprite
        self.player_img = Image.open(os.path.join(self.BASE_DIR, "assets", "player_wizard.png")).resize((400, 300))
        self.player_sprite = ImageTk.PhotoImage(self.player_img)

        # Load enemy sprites (sizes kept as in your last code)
        self.enemy_imgs = [
            Image.open(os.path.join(self.BASE_DIR, "assets", "enemy_wizard.png")).resize((400, 300)),
            Image.open(os.path.join(self.BASE_DIR, "assets", "enemy_wizard2.png")).resize((150, 190)),
            Image.open(os.path.join(self.BASE_DIR, "assets", "enemy_wizard3.png")).resize((150, 300))
        ]
        self.enemy_names = ["Dark Wizard", "Dark Sorcerer", "Necromancer"]
        self.enemy_index = 0
        self.enemy_base_hp = [60, 80, 100]  # base HP for each enemy
        self.set_enemy(self.enemy_index)  # creates self.enemy and self.enemy_sprite

        # Canvas (battlefield)
        self.canvas = tk.Canvas(self, width=800, height=400)
        self.canvas.pack()
        self.canvas.create_image(0, 0, image=self.bg, anchor="nw")

        # place sprites (player and enemy)
        self.player_sprite_id = self.canvas.create_image(100, 120, image=self.player_sprite, anchor="nw")
        self.enemy_sprite_id = self.canvas.create_image(350, 150, image=self.enemy_sprite, anchor="nw")

        # Level/XP display text
        self.level_text = self.canvas.create_text(80, 20,
                                                  text=f"Lv {self.player.level} XP {self.player.xp}/{self.player.next_level_xp}",
                                                  font=("Consolas", 12, "bold"),
                                                  fill="yellow")

        # HP bars and name texts (store references so we can update them)
        self.create_hp_display()

        # Control panel (spells + messages)
        self.control_frame = tk.Frame(self, height=200, bg="#111111")
        self.control_frame.pack(fill="x", side="bottom")

        self.spell_frame = tk.Frame(self.control_frame, bg="#111111")
        self.spell_frame.pack(side="left", padx=10, pady=10, fill="y")

        self.spell_buttons = {}
        self.create_spell_buttons()

        self.message_box = tk.Text(self.control_frame, height=10, width=50, wrap="word",
                                   bg="#000000", fg="#ffffff",
                                   font=("Consolas", 12, "bold"),
                                   padx=8, pady=8, relief="ridge")
        self.message_box.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        self.message_box.configure(state="disabled")

        self._message_queue = []
        self._message_running = False

        # initial message
        self.show_message(f"A wild {self.enemy.name} appeared! {self.player.name}, what will you do?")

    # --- Enemy setup ---
    def set_enemy(self, index):
        # enemy max HP increases by 20 each time
        hp = self.enemy_base_hp[index] + index * 20
        self.enemy = Character(self.enemy_names[index], hp, {
            "Crucio":((7,14),"Curse"),
            "Avada Kedavra":((15,25),"Curse"),
            "Imperio":((5,10),"Curse")
        })
        # enemy sprite image object (ImageTk.PhotoImage)
        self.enemy_sprite = ImageTk.PhotoImage(self.enemy_imgs[index])
        # if canvas sprite exists, update its image; otherwise it will be used when created
        if hasattr(self, 'enemy_sprite_id'):
            self.canvas.itemconfigure(self.enemy_sprite_id, image=self.enemy_sprite)
        # update enemy name text on HUD if created
        if hasattr(self, 'enemy_name_text'):
            self.canvas.itemconfigure(self.enemy_name_text, text=self.enemy.name)
        # ensure enemy HP text is updated
        if hasattr(self, 'enemy_hp_text'):
            self.canvas.itemconfigure(self.enemy_hp_text, text=f"{self.enemy.hp}/{self.enemy.max_hp}")

    # --- Spell buttons (create) ---
    def create_spell_buttons(self):
        type_colors = {"Charm":"blue","Curse":"red","Defense":"green","Heal":"lime","Stun":"purple","Poison":"orange"}
        for spell, (dmg_range, stype) in self.player.spells.items():
            frame = tk.Frame(self.spell_frame, bg="#111111")
            frame.pack(anchor="w", pady=5)

            btn_text = spell
            if spell in self.player.limited_uses:
                btn_text = f"{spell} ({self.player.limited_uses[spell]})"

            btn = tk.Button(frame, text=btn_text, width=15, font=("Arial",13,"bold"),
                            bg="#dddddd", fg="black",
                            activebackground="#bbbbbb", activeforeground="black",
                            command=lambda s=spell: self.player_attack(s))
            btn.pack(side="left")

            lbl = tk.Label(frame, text=f"[{stype}]", font=("Arial",12,"bold"),
                           bg="#111111", fg=type_colors.get(stype,"white"))
            lbl.pack(side="left", padx=6)

            self.spell_buttons[spell] = btn

    def update_spell_buttons(self):
        for spell, btn in self.spell_buttons.items():
            if spell in self.player.limited_uses:
                remaining = self.player.limited_uses[spell]
                btn.configure(text=f"{spell} ({remaining})")
                if remaining <= 0:
                    btn.configure(state="disabled")
            else:
                btn.configure(state="normal")

    def update_level_xp(self):
        self.canvas.itemconfigure(self.level_text, text=f"Lv {self.player.level} XP {self.player.xp}/{self.player.next_level_xp}")

    # --- HP display (creates and stores references) ---
    def create_hp_display(self):
        # player name and HP bar
        self.player_name_text = self.canvas.create_text(50+HP_BAR_WIDTH//2, 330,
                                                        text=self.player.name,
                                                        font=("Consolas", 12, "bold"),
                                                        fill="white")
        self.canvas.create_rectangle(50,350,50+HP_BAR_WIDTH,350+HP_BAR_HEIGHT,fill="#555555")
        self.player_hp_fg = self.canvas.create_rectangle(50,350,50+HP_BAR_WIDTH,350+HP_BAR_HEIGHT,fill="#4caf50")
        self.player_hp_text = self.canvas.create_text(50+HP_BAR_WIDTH//2, 360,
                                                      text=f"{self.player.hp}/{self.player.max_hp}",
                                                      font=("Consolas",10,"bold"), fill="white")

        # enemy name and HP bar (store references)
        self.enemy_name_text = self.canvas.create_text(550+HP_BAR_WIDTH//2, 330,
                                                       text=self.enemy.name,
                                                       font=("Consolas", 12, "bold"),
                                                       fill="white")
        self.canvas.create_rectangle(550,350,550+HP_BAR_WIDTH,350+HP_BAR_HEIGHT,fill="#555555")
        self.enemy_hp_fg = self.canvas.create_rectangle(550,350,550+HP_BAR_WIDTH,350+HP_BAR_HEIGHT,fill="#4caf50")
        self.enemy_hp_text = self.canvas.create_text(550+HP_BAR_WIDTH//2, 360,
                                                     text=f"{self.enemy.hp}/{self.enemy.max_hp}",
                                                     font=("Consolas",10,"bold"), fill="white")

    def update_hp_display(self):
        pr = max(0, min(1, self.player.hp / self.player.max_hp))
        pw = HP_BAR_WIDTH * pr
        self.canvas.coords(self.player_hp_fg, 50, 350, 50 + pw, 350 + HP_BAR_HEIGHT)
        self.canvas.itemconfigure(self.player_hp_text, text=f"{self.player.hp}/{self.player.max_hp}")
        self.canvas.itemconfigure(self.player_hp_fg, fill=self.hp_color(pr))

        er = max(0, min(1, self.enemy.hp / self.enemy.max_hp))
        ew = HP_BAR_WIDTH * er
        self.canvas.coords(self.enemy_hp_fg, 550, 350, 550 + ew, 350 + HP_BAR_HEIGHT)
        self.canvas.itemconfigure(self.enemy_hp_text, text=f"{self.enemy.hp}/{self.enemy.max_hp}")
        self.canvas.itemconfigure(self.enemy_hp_fg, fill=self.hp_color(er))

        # update names (in case changed)
        self.canvas.itemconfigure(self.player_name_text, text=self.player.name)
        self.canvas.itemconfigure(self.enemy_name_text, text=self.enemy.name)

    def hp_color(self, ratio):
        if ratio > 0.6: return "#4caf50"
        if ratio > 0.25: return "#f0ad4e"
        return "#e53935"

    # --- Sprite effects ---
    def shake_sprite(self,sprite_id,amplitude=8,cycles=8,interval=30):
        orig = self.canvas.coords(sprite_id)
        if not orig: return
        ox, oy = orig[0], orig[1]
        def _step(i=0):
            if i >= cycles:
                cur = self.canvas.coords(sprite_id)
                if cur:
                    cx, cy = cur[0], cur[1]
                    self.canvas.move(sprite_id, ox - cx, oy - cy)
                return
            offset = amplitude * math.cos(2 * math.pi * i / cycles)
            cur = self.canvas.coords(sprite_id)
            if cur:
                cx, cy = cur[0], cur[1]
                self.canvas.move(sprite_id, (ox + offset) - cx, 0)
            self.after(interval, lambda: _step(i+1))
        _step(0)

    def flash_sprite(self,sprite_id,times=4,interval=100):
        def _flash(i=0):
            if i >= times * 2:
                try:
                    self.canvas.itemconfigure(sprite_id, state='normal')
                except:
                    pass
                return
            state = 'hidden' if i % 2 == 0 else 'normal'
            try:
                self.canvas.itemconfigure(sprite_id, state=state)
            except:
                pass
            self.after(interval, lambda: _flash(i+1))
        _flash()

    def attack_animation(self,sprite_id,distance=30,duration=150,callback=None):
        steps = 10
        delay = max(1, duration // (2 * steps))
        def forward(i=0):
            if i >= steps:
                backward()
                return
            try:
                self.canvas.move(sprite_id, distance/steps, 0)
            except:
                pass
            self.after(delay, lambda: forward(i+1))
        def backward(i=0):
            if i >= steps:
                if callback: callback()
                return
            try:
                self.canvas.move(sprite_id, -distance/steps, 0)
            except:
                pass
            self.after(delay, lambda: backward(i+1))
        forward()

    def cast_spell_visual(self,caster_id,target_id,spell_type,callback=None):
        cx, cy = self.canvas.coords(caster_id)
        tx, ty = self.canvas.coords(target_id)
        color = {"Charm":"blue","Curse":"red","Defense":"green","Heal":"lime","Stun":"purple","Poison":"orange"}.get(spell_type,"white")
        beam = self.canvas.create_line(cx+200, cy+150, cx+200, cy+150, fill=color, width=5)
        steps = 20
        dx = (tx - cx) / steps
        dy = (ty - cy) / steps
        def animate(i=0):
            if i >= steps:
                try:
                    self.canvas.delete(beam)
                except:
                    pass
                if callback: callback()
                return
            try:
                self.canvas.move(beam, dx, dy)
            except:
                pass
            self.after(25, lambda: animate(i+1))
        animate()

    # --- Player attack ---
    def player_attack(self, spell):
        # check limited uses
        if spell in self.player.limited_uses:
            if self.player.limited_uses[spell] <= 0:
                self.show_message(f"No more uses left for {spell}!")
                return
            self.player.limited_uses[spell] -= 1
            self.update_spell_buttons()

        dmg, stype = self.player.cast_spell(spell)
        stype = self.player.spells[spell][1]

        if stype == "Defense":
            self.player_defense = True
            self.show_message(f"{self.player.name} casts {spell}! Block the next attack! (+3 XP)")
            self.flash_sprite(self.player_sprite_id, times=6, interval=80)
            if self.player.gain_xp(3):
                self.show_message(f"{self.player.name} leveled up to Lv {self.player.level}!")
            self.update_level_xp()
            self.after(800, self.enemy_turn)
            return

        if stype == "Heal":
            healed = min(dmg, self.player.max_hp - self.player.hp)
            self.player.hp = min(self.player.max_hp, self.player.hp + dmg)
            self.update_hp_display()
            self.show_message(f"{self.player.name} casts {spell}! Heals {healed} HP! (+{healed//2} XP)")
            if self.player.gain_xp(healed//2):
                self.show_message(f"{self.player.name} leveled up to Lv {self.player.level}!")
            self.update_level_xp()
            self.flash_sprite(self.player_sprite_id, times=6, interval=80)
            self.after(800, self.enemy_turn)
            return

        # normal damage spells
        self.attack_animation(self.player_sprite_id, 30, 150,
                              callback=lambda:
                                  self.cast_spell_visual(self.player_sprite_id, self.enemy_sprite_id, stype,
                                                         callback=lambda: self._finish_player_attack(spell, dmg)))

    def _finish_player_attack(self, spell, dmg):
        self.enemy.hp = max(0, self.enemy.hp - dmg)
        self.flash_sprite(self.enemy_sprite_id)
        self.update_hp_display()
        self.show_message(f"{self.player.name} casts {spell}! It dealt {dmg} damage! (+{dmg//2} XP)")
        if self.player.gain_xp(dmg//2):
            self.show_message(f"{self.player.name} leveled up to Lv {self.player.level}!")
        self.update_level_xp()

        if self.enemy.hp <= 0:
            # give XP for victory
            self.player.gain_xp(50)
            self.update_level_xp()
            self.show_message(f"{self.enemy.name} fainted! (+50 XP)")

            # --- Reset player and advance enemy ---
            # increase max HP by 20 and restore current HP to full
            self.player.max_hp += 20
            self.player.hp = self.player.max_hp

            # reset limited uses to initial values
            self.player.limited_uses = copy.deepcopy(self.initial_limited_uses)
            self.update_spell_buttons()
            self.update_hp_display()

            # advance enemy index and either set next enemy or end game
            self.enemy_index += 1
            if self.enemy_index < len(self.enemy_imgs):
                # small delay so player sees victory message first
                self.after(900, lambda: self.set_enemy(self.enemy_index))
                # update sprite image on canvas (set_enemy handles sprite update)
                # update HP display after sprite set
                self.after(1000, self.update_hp_display)
                self.after(1100, lambda: self.show_message(
                    f"A wild {self.enemy.name} appeared! Your HP was restored and max HP increased by 20. Spell uses reset. "
                    f"Enemy HP increased by 20!"))
            else:
                # defeated all enemies: final victory
                messagebox.showinfo("Victory", "You defeated all enemies!")
                self.destroy()
            return

        # otherwise enemy turn
        self.after(800, self.enemy_turn)

    # --- Enemy turn ---
    def enemy_turn(self):
        if "stun" in self.enemy.status_effects and self.enemy.status_effects["stun"] > 0:
            self.show_message(f"{self.enemy.name} is stunned and cannot attack!")
            self.enemy.status_effects["stun"] = 0
            self.after(1000, self.check_poison)
            return
        self.enemy_attack()

    def check_poison(self):
        if "poison" in self.enemy.status_effects and self.enemy.status_effects["poison"] > 0:
            dmg = 3
            self.enemy.hp = max(0, self.enemy.hp - dmg)
            self.enemy.status_effects["poison"] -= 1
            self.show_message(f"{self.enemy.name} takes {dmg} poison damage!")
            self.update_hp_display()
            if self.enemy.hp <= 0:
                # handle death from poison same as normal finish
                self._finish_player_attack("<poison>", 0)
                return
        self.after(800, self.enemy_attack)

    def enemy_attack(self):
        spell = random.choice(list(self.enemy.spells.keys()))
        dmg, stype = self.enemy.cast_spell(spell)
        stype = self.enemy.spells[spell][1]

        if self.player_defense:
            self.show_message(f"{self.enemy.name} used {spell}, but Protego blocked it!")
            self.player_defense = False
            self.flash_sprite(self.player_sprite_id, times=6, interval=80)
        else:
            # animate enemy attack then apply damage
            def finish_hit():
                self.player.hp = max(0, self.player.hp - dmg)
                self.flash_sprite(self.player_sprite_id)
                self.update_hp_display()
                self.show_message(f"{self.enemy.name} used {spell}! It dealt {dmg} damage!")
                if self.player.hp <= 0:
                    self.show_message(f"{self.player.name} fainted... Game Over.")
                    messagebox.showinfo("Defeat", f"{self.player.name} fainted...")
                    self.destroy()
            self.attack_animation(self.enemy_sprite_id, -30, 150,
                                  callback=lambda: self.cast_spell_visual(self.enemy_sprite_id, self.player_sprite_id, stype, callback=finish_hit))

    # --- Message queue (typewriter) ---
    def show_message(self, text):
        self._message_queue.append(text)
        if not self._message_running:
            self._run_next_message()

    def _run_next_message(self):
        if not self._message_queue:
            self._message_running = False
            return
        self._message_running = True
        msg = self._message_queue.pop(0)
        self._type_message(msg, 0)

    def _type_message(self, msg, i, delay=25):
        self.message_box.configure(state="normal")
        if i == 0:
            self.message_box.delete("1.0", tk.END)
        if i < len(msg):
            self.message_box.insert(tk.END, msg[i])
            self.message_box.see(tk.END)
            self.message_box.configure(state="disabled")
            self.after(delay, lambda: self._type_message(msg, i+1, delay))
        else:
            self.after(600, self._run_next_message)

# ----------------- Main -----------------
if __name__ == "__main__":
    # ask player name
    root = tk.Tk()
    root.withdraw()
    name = simpledialog.askstring("Name", "Enter your wizard's name:")
    if not name:
        name = "You"
    root.destroy()

    # player spells
    player_spells = {
        "Expelliarmus":((8,15),"Charm"),
        "Stupefy":((5,12),"Charm"),
        "Sectumsempra":((10,20),"Curse"),
        "Protego":((0,0),"Defense"),
        "Episkey":((10,20),"Heal"),
        "Stupefying Stun":((0,0),"Stun"),
        "Poison Cloud":((0,0),"Poison")
    }

    # limited uses initial set (used for resetting on new enemy)
    limited_uses = {"Episkey":2, "Sectumsempra":1}

    player = Character(name, 60, player_spells, limited_uses.copy())

    app = DuelGUI(player, limited_uses)
    app.mainloop()
