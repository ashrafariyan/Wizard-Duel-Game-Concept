import tkinter as tk
from PIL import Image, ImageTk
import os
import sys
import subprocess
from tkinter import messagebox
import textwrap

class Game(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Wizard Adventure - Overworld")
        self.geometry("800x600")
        self.resizable(False, False)

        # --- Canvas ---
        self.canvas = tk.Canvas(self, width=800, height=600)
        self.canvas.pack()

        # --- Background ---
        bg_path = os.path.join("assets", "overworld_bg.jpeg")
        if not os.path.exists(bg_path):
            raise FileNotFoundError(f"Background not found: {bg_path}")
        self.bg_img = ImageTk.PhotoImage(
            Image.open(bg_path).resize((800, 600))
        )
        self.canvas.create_image(0, 0, anchor="nw", image=self.bg_img)

        # --- Player ---
        player_path = os.path.join("assets", "overworld_player.png")
        if not os.path.exists(player_path):
            raise FileNotFoundError(f"Player sprite not found: {player_path}")
        self.player_img = ImageTk.PhotoImage(
            Image.open(player_path).resize((180, 180))
        )
        self.player = self.canvas.create_image(100, 400, anchor="nw", image=self.player_img)

        # --- Enemy NPC ---
        enemy_path = os.path.join("assets", "overworld_npc1.png")
        if not os.path.exists(enemy_path):
            raise FileNotFoundError(f"Enemy sprite not found: {enemy_path}")
        self.enemy_img = ImageTk.PhotoImage(
            Image.open(enemy_path).resize((180, 180))
        )
        self.enemy = self.canvas.create_image(380, 150, anchor="nw", image=self.enemy_img)

        # --- Dialogue Box Elements ---
        self.dialogue_rect = None
        self.dialogue_text = None
        self.dialogue_tail = None

        # --- Movement ---
        self.keys_pressed = {"Up": False, "Down": False, "Left": False, "Right": False}
        self.bind("<KeyPress>", self.key_press)
        self.bind("<KeyRelease>", self.key_release)
        self.bind_all("<space>", self.space_pressed)
        self.canvas.focus_set()

        # --- State ---
        self.enemy_nearby = False
        self.duel_prompted = False
        self.dialogue_animating = False
        self.dialogue_done = False  # Ensure dialogue plays only once

        # Start movement loop
        self.move_loop()

    def key_press(self, event):
        if event.keysym in self.keys_pressed:
            self.keys_pressed[event.keysym] = True

    def key_release(self, event):
        if event.keysym in self.keys_pressed:
            self.keys_pressed[event.keysym] = False

    def move_loop(self):
        dx = dy = 0
        speed = 5
        if self.keys_pressed["Up"]:
            dy -= speed
        if self.keys_pressed["Down"]:
            dy += speed
        if self.keys_pressed["Left"]:
            dx -= speed
        if self.keys_pressed["Right"]:
            dx += speed

        if dx != 0 or dy != 0:
            x1, y1, x2, y2 = self.canvas.bbox(self.player)

            # --- Edge boundaries ---
            if x1 + dx < 0: dx = -x1
            if y1 + dy < 0: dy = -y1
            if x2 + dx > 800: dx = 800 - x2
            if y2 + dy > 600: dy = 600 - y2

            self.canvas.move(self.player, dx, dy)

        # Always check enemy proximity
        self.check_enemy_proximity()

        # Continue loop
        self.after(30, self.move_loop)

    def check_enemy_proximity(self):
        px1, py1, px2, py2 = self.canvas.bbox(self.player)
        ex1, ey1, ex2, ey2 = self.canvas.bbox(self.enemy)
        horizontal_overlap = (px2 > ex1 + 20) and (px1 < ex2 - 20)
        vertical_overlap = (py2 > ey1 + 20) and (py1 < ey2 - 20)

        if horizontal_overlap and vertical_overlap:
            self.enemy_nearby = True
            if not self.dialogue_animating and not self.dialogue_done:
                text = "Dark Wizard: Do you dare challenge me to a duel? Press SPACE to accept!"
                self.animate_dialogue(text)
        else:
            self.enemy_nearby = False
            self.hide_dialogue()
            self.duel_prompted = False
            self.dialogue_animating = False

    def animate_dialogue(self, text):
        """Multi-line RPG style dialogue box with typing animation (no overflow)."""
        self.dialogue_animating = True
        self.dialogue_done = True  # Ensure it plays once
        ex1, ey1, ex2, ey2 = self.canvas.bbox(self.enemy)
        width = 250
        height = 70
        x = ex1 + (ex2-ex1)//2 - width//2
        y = ey1 - height - 10

        # Wrap text to fit box
        wrapped_text = textwrap.wrap(text, width=35)

        # Draw rectangle
        if self.dialogue_rect:
            self.canvas.coords(self.dialogue_rect, x, y, x+width, y+height)
        else:
            self.dialogue_rect = self.canvas.create_rectangle(
                x, y, x+width, y+height, fill="#222222", outline="#00FF00", width=2
            )

        # Draw tail
        if self.dialogue_tail:
            self.canvas.coords(self.dialogue_tail, x+width//2-5, y+height, x+width//2+5, y+height, x+width//2, y+height+10)
        else:
            self.dialogue_tail = self.canvas.create_polygon(
                x+width//2-5, y+height,
                x+width//2+5, y+height,
                x+width//2, y+height+10,
                fill="#222222", outline="#00FF00"
            )

        # Prepare text object
        if self.dialogue_text:
            self.canvas.itemconfigure(self.dialogue_text, text="")
            self.canvas.coords(self.dialogue_text, x+10, y+10)
        else:
            self.dialogue_text = self.canvas.create_text(x+10, y+10, text="", fill="white",
                                                         font=("Arial", 14, "bold"), anchor="nw")

        # Animate each character
        self._animate_text_step(wrapped_text, line_index=0, char_index=0)

    def _animate_text_step(self, lines, line_index, char_index):
        if not self.enemy_nearby:
            self.dialogue_animating = False
            return  # stop if player moved away

        if line_index < len(lines):
            current_line = lines[line_index]
            if char_index <= len(current_line):
                text_to_show = "\n".join(lines[:line_index] + [current_line[:char_index]])
                self.canvas.itemconfigure(self.dialogue_text, text=text_to_show)
                self.after(20, lambda: self._animate_text_step(lines, line_index, char_index+1))
            else:
                # Move to next line
                self.after(200, lambda: self._animate_text_step(lines, line_index+1, 0))
        else:
            self.dialogue_animating = False

    def hide_dialogue(self):
        if self.dialogue_rect:
            self.canvas.delete(self.dialogue_rect)
            self.dialogue_rect = None
        if self.dialogue_tail:
            self.canvas.delete(self.dialogue_tail)
            self.dialogue_tail = None
        if self.dialogue_text:
            self.canvas.delete(self.dialogue_text)
            self.dialogue_text = None

    def space_pressed(self, event):
        if self.enemy_nearby and not self.duel_prompted:
            self.duel_prompted = True
            if messagebox.askyesno("Duel Invitation", "The Dark Wizard challenges you to a duel! Accept?"):
                self.start_duel()
            else:
                self.duel_prompted = False

    def start_duel(self):
        self.destroy()
        python_exe = sys.executable
        duel_file = "hogwarts_duel_ui.py"
        if not os.path.exists(duel_file):
            raise FileNotFoundError(f"Duel file not found: {duel_file}")
        subprocess.Popen([python_exe, duel_file])


# --- Run Overworld ---
if __name__ == "__main__":
    game = Game()
    game.mainloop()
