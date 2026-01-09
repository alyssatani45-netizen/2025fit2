import pyxel
import random
from dataclasses import dataclass

W, H = 256, 256

# 画像を使う
USE_SPRITES = True

TARGET_STACK = 12
PANCAKE_H = 16

# 画像たち
ASSET_PANCAKE = "pancake.pyxres"
ASSET_BURNT = "kogepancake.pyxres"
ASSET_BUTTER = "butter2.pyxres"


SPR_W, SPR_H = 16, 16

V_STEP=SPR_H

# 1枚の img(0) に並べて配置する場所（v方向に積む）
# pancake: (0,0), burnt: (0,8), butter: (0,16)
SPR_PANCAKE = dict(img=0, u=0, v=0,  w=SPR_W, h=SPR_H)
SPR_BURNT   = dict(img=0, u=0, v= V_STEP,  w=SPR_W, h=SPR_H)
SPR_BUTTER  = dict(img=0, u=0, v=V_STEP*2, w=SPR_W, h=SPR_H)

STATE_TITLE = 0
STATE_PLAY = 1
STATE_GAMEOVER = 2
STATE_CLEAR = 3

KIND_PANCAKE = 0
KIND_BURNT = 1
KIND_BUTTER = 2


@dataclass
class FallingItem:
    kind: int
    x: float
    y: float
    vy: float
    w: int
    h: int


class App:
    def __init__(self):
        pyxel.init(W, H, title="Pancake Stack (Pyxel)")

        if USE_SPRITES:
            self.load_three_assets_into_one_bank()

        self.state = STATE_TITLE
        self.reset()
        pyxel.run(self.update, self.draw)

    # -----------------------------
    # 3つのpyxresから画像を読み出して img(0) にまとめる
    # -----------------------------
    def grab_region(self, img_bank: int, x: int, y: int, w: int, h: int):
        im = pyxel.image(img_bank)
        data = []
        for yy in range(h):
            row = []
            for xx in range(w):
                row.append(im.pget(x + xx, y + yy))
            data.append(row)
        return data

    def paste_region(self, img_bank: int, dst_x: int, dst_y: int, data):
        im = pyxel.image(img_bank)
        h = len(data)
        w = len(data[0]) if h > 0 else 0
        for yy in range(h):
            for xx in range(w):
                im.pset(dst_x + xx, dst_y + yy, data[yy][xx])

    def load_three_assets_into_one_bank(self):
        # 前提：それぞれのpyxresの img(0) の (0,0) にスプライトが置かれている
        pyxel.load(ASSET_PANCAKE)
        pancake_data = self.grab_region(0, 0, 0, SPR_W, SPR_H)

        pyxel.load(ASSET_BURNT)
        burnt_data = self.grab_region(0, 0, 0, SPR_W, SPR_H)

        pyxel.load(ASSET_BUTTER)
        butter_data = self.grab_region(0, 0, 0, SPR_W, SPR_H)

        # 最後に img(0) を「統合スプライトシート」として再構築
        self.paste_region(0, SPR_PANCAKE["u"], SPR_PANCAKE["v"], pancake_data)
        self.paste_region(0, SPR_BURNT["u"],   SPR_BURNT["v"],   burnt_data)
        self.paste_region(0, SPR_BUTTER["u"],  SPR_BUTTER["v"],  butter_data)

    # -----------------------------
    # ゲーム本体
    # -----------------------------
    def reset(self):
        self.paddle_w = 56
        self.paddle_h = 10
        self.paddle_x = (W - self.paddle_w) // 2
        self.paddle_y = H - 28

        self.stack = 0
        self.item: FallingItem | None = None

        self.frame = 0
        self.spawn_interval = 32
        self.butter_spawned = False
        self.flash = 0

    def move_paddle(self):
        speed = 3.2
        dx = 0
        if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT):
            dx -= speed
        if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT):
            dx += speed

        self.paddle_x = max(0, min(W - self.paddle_w, self.paddle_x + dx))

    def spawn_item(self):
        if self.item is not None:
            return

        if (self.stack >= TARGET_STACK) and (not self.butter_spawned):
            kind = KIND_BUTTER
            self.butter_spawned = True
            w, h = 20, 10
            vy = 1.4
        else:
            p_burnt = min(0.08 + self.stack * 0.003, 0.18)
            kind = KIND_BURNT if random.random() < p_burnt else KIND_PANCAKE
            w, h = 22, 10
            vy = 1.2 + min(self.stack * 0.04, 1.8)

        x = random.uniform(0, W - w)
        y = -h - 2
        self.item = FallingItem(kind=kind, x=x, y=y, vy=vy, w=w, h=h)

    def paddle_rect(self):
        stack_height = self.stack * PANCAKE_H
        top_y = self.paddle_y - stack_height
        return (self.paddle_x, top_y, self.paddle_w, self.paddle_h + stack_height)

    def overlaps(self, ax, ay, aw, ah, bx, by, bw, bh):
        return not (ax + aw < bx or bx + bw < ax or ay + ah < by or by + bh < ay)

    def check_catch(self):
        if self.item is None:
            return

        px, py, pw, ph = self.paddle_rect()
        it = self.item

        if self.overlaps(it.x, it.y, it.w, it.h, px, py, pw, ph):
            if it.kind == KIND_BURNT:
                self.state = STATE_GAMEOVER
                self.flash = 15
            elif it.kind == KIND_PANCAKE:
                self.stack += 1
            elif it.kind == KIND_BUTTER:
                self.state = STATE_CLEAR
                self.flash = 20
            self.item = None

    def update(self):
        if self.state == STATE_TITLE:
            if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A):
                self.reset()
                self.state = STATE_PLAY
            return

        if self.state == STATE_PLAY:
            self.frame += 1
            self.move_paddle()

            if (self.frame % self.spawn_interval) == 0:
                self.spawn_item()

            if self.item is not None:
                self.item.y += self.item.vy
                if self.item.y > H + 10:
                    if self.item.kind == KIND_BUTTER:
                        self.state = STATE_GAMEOVER
                        self.flash = 15
                    self.item = None

            self.check_catch()
            self.spawn_interval = max(16, 32 - self.stack)

        elif self.state in (STATE_GAMEOVER, STATE_CLEAR):
            if pyxel.btnp(pyxel.KEY_R) or pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A):
                self.reset()
                self.state = STATE_PLAY
            if pyxel.btnp(pyxel.KEY_ESCAPE):
                self.state = STATE_TITLE

        if self.flash > 0:
            self.flash -= 1

    def draw_sprite_item(self, kind, x, y):
        s = SPR_PANCAKE if kind == KIND_PANCAKE else (SPR_BURNT if kind == KIND_BURNT else SPR_BUTTER)
        pyxel.blt(x, y, s["img"], s["u"], s["v"], s["w"], s["h"], colkey=0)

    def draw_stack(self):
        for i in range(self.stack):
            y = self.paddle_y - (i + 1) * PANCAKE_H
            x = self.paddle_x + (self.paddle_w - 24) // 2
            if USE_SPRITES:
                self.draw_sprite_item(KIND_PANCAKE, x, y)
            else:
                pyxel.rect(x, y, 24, PANCAKE_H, 10)

    def draw(self):
        pyxel.cls(1)
        if self.flash > 0:
            pyxel.rect(0, 0, W, H, 7)

        if self.state == STATE_TITLE:
            pyxel.cls(0)
            pyxel.text(64, 70, "PANCAKE STACK", 7)
            pyxel.text(34, 95, "- Catch pancakes to stack them", 6)
            pyxel.text(34, 108, "- Catch BURNT -> GAME OVER", 6)
            pyxel.text(34, 121, "- After stacking enough,", 6)
            pyxel.text(34, 134, "  catch BUTTER -> CLEAR", 6)
            pyxel.text(44, 168, "Press Enter / Space to Start", 10)
            return

        self.draw_stack()
        pyxel.rect(self.paddle_x, self.paddle_y, self.paddle_w, self.paddle_h, 5)
        pyxel.rectb(self.paddle_x, self.paddle_y, self.paddle_w, self.paddle_h, 7)

        if self.item is not None:
            if USE_SPRITES:
                self.draw_sprite_item(self.item.kind, self.item.x, self.item.y)
            else:
                pyxel.rect(self.item.x, self.item.y, self.item.w, self.item.h, 7)

        pyxel.text(8, 8, f"STACK: {self.stack}/{TARGET_STACK}", 7)
        if self.stack >= TARGET_STACK and not self.butter_spawned:
            pyxel.text(8, 18, "BUTTER INCOMING!", 10)
        elif self.butter_spawned and self.state == STATE_PLAY:
            pyxel.text(8, 18, "CATCH THE BUTTER!", 10)

        if self.state == STATE_GAMEOVER:
            pyxel.rect(0, 90, W, 76, 0)
            pyxel.text(96, 110, "GAME OVER", 8)
            pyxel.text(58, 128, "R/Enter: Retry   Esc: Title", 7)

        if self.state == STATE_CLEAR:
            pyxel.rect(0, 90, W, 76, 0)
            pyxel.text(106, 110, "CLEAR!", 11)
            pyxel.text(52, 128, "R/Enter: Play Again   Esc: Title", 7)


if __name__ == "__main__":
    App()
