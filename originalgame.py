import pyxel
import random

# =====================
# 1) 設定（ここだけ触れば調整できる）
# =====================
W, H = 256, 256

# 画像ファイル（.py と同じフォルダに置く）
PANCAKE_FILE = "pancake.pyxres"
BURNT_FILE   = "kogepancake.pyxres"
BUTTER_FILE  = "butter2.pyxres"

# スプライト（画像）のサイズ
SPR_W, SPR_H = 16, 16

# どれだけ積んだらバターを出すか
TARGET_STACK = 12

# 積み上げの間隔（スプライト高さと同じが分かりやすい）
STACK_STEP_Y = 16


# =====================
# 2) 小さい便利関数（「ぶつかった？」判定）
# =====================
def hit(ax, ay, aw, ah, bx, by, bw, bh):
    """四角形Aと四角形Bが重なっているなら True"""
    return not (ax + aw < bx or bx + bw < ax or ay + ah < by or by + bh < ay)


class App:
    def __init__(self):
        pyxel.init(W, H, title="Pancake Stack (Simple)")

        # ゲームの変数をまとめて初期化
        self.restart()

        pyxel.run(self.update, self.draw)

    # =====================
    # 3) リスタート（全部初期化）
    # =====================
    def restart(self):
        # パッド（受ける板）
        self.pad_w = 56
        self.pad_h = 10
        self.pad_x = (W - self.pad_w) // 2
        self.pad_y = H - 28

        # 積んだ枚数
        self.stack = 0

        # いま落ちている物（無ければ None）
        # item は dict で持つ（初心者に分かりやすい）
        # 例: {"kind":"pancake", "x":..., "y":..., "vy":...}
        self.item = None

        # バターをもう出したか
        self.butter_spawned = False

        # ゲームの状態（文字で持つ：分かりやすさ重視）
        # "title" / "play" / "gameover" / "clear"
        self.mode = "title"

        # 出現タイミング用
        self.frame = 0
        self.spawn_interval = 32

    # =====================
    # 4) パッド移動
    # =====================
    def move_pad(self):
        speed = 3

        if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT):
            self.pad_x -= speed
        if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT):
            self.pad_x += speed

        # 画面外に出ないようにする
        self.pad_x = max(0, min(W - self.pad_w, self.pad_x))

    # =====================
    # 5) 落下物を作る（1個だけ落とす）
    # =====================
    def spawn_item_if_needed(self):
        # すでに落ちているなら作らない
        if self.item is not None:
            return

        # バター出現条件（TARGET_STACK達成後に1回だけ）
        if self.stack >= TARGET_STACK and not self.butter_spawned:
            self.item = {"kind": "butter", "x": random.uniform(0, W - SPR_W), "y": -SPR_H, "vy": 1.4}
            self.butter_spawned = True
            return

        # ふつう or 焦げ を出す
        # 焦げ確率は少しずつ上げる
        burnt_prob = min(0.1 + self.stack * 0.05, 0.6)
        if random.random() < burnt_prob:
            kind = "burnt"
        else:
            kind = "pancake"

        speed = 2 + min(self.stack * 1, 15)

        self.item = {"kind": kind, "x": random.uniform(0, W - SPR_W), "y": -SPR_H, "vy": speed}

    # =====================
    # 6) 当たり判定（取ったらどうする？）
    # =====================
    def check_catch(self):
        if self.item is None:
            return

        # 「積み上がっている高さ」ぶん、当たり判定を上に伸ばす（積むゲームっぽくなる）
        stack_height = self.stack * STACK_STEP_Y
        pad_hit_x = self.pad_x
        pad_hit_y = self.pad_y - stack_height
        pad_hit_w = self.pad_w
        pad_hit_h = self.pad_h + stack_height

        # 落下物の四角
        it_x = self.item["x"]
        it_y = self.item["y"]

        if hit(it_x, it_y, SPR_W, SPR_H, pad_hit_x, pad_hit_y, pad_hit_w, pad_hit_h):
            # 取った！
            if self.item["kind"] == "burnt":
                self.mode = "gameover"
            elif self.item["kind"] == "pancake":
                self.stack += 1
            elif self.item["kind"] == "butter":
                self.mode = "clear"

            self.item = None  # 取ったので消す

    # =====================
    # 7) update（毎フレーム進行）
    # =====================
    def update(self):
        # タイトル：Enterで開始
        if self.mode == "title":
            if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A):
                self.mode = "play"
            return

        # クリア/ゲームオーバー：Rでやり直し、Escでタイトル
        if self.mode in ("gameover", "clear"):
            if pyxel.btnp(pyxel.KEY_R) or pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A):
                self.restart()
                self.mode = "play"
            if pyxel.btnp(pyxel.KEY_ESCAPE):
                self.restart()
            return

        # プレイ中
        self.frame += 1
        self.move_pad()

        # 一定間隔で落下物を作る
        if self.frame % self.spawn_interval == 0:
            self.spawn_item_if_needed()

        # 落下物を動かす
        if self.item is not None:
            self.item["y"] += self.item["vy"]

            # 画面外に落ちたら消す（バターを落としたら負け）
            if self.item["y"] > H + 10:
                if self.item["kind"] == "butter":
                    self.mode = "gameover"
                self.item = None

        # 取ったかチェック
        self.check_catch()

        # 積むほど出現がちょっと早くなる（最低16）
        self.spawn_interval = max(16, 32 - self.stack)

    # =====================
    # 8) 画像を描く（必要なファイルを読み込んでから blt）
    # =====================
    def draw_sprite(self, kind, x, y):
        # kind に応じてファイルを切り替える（合体しない方式）
        if kind == "pancake":
            pyxel.load(PANCAKE_FILE)
        elif kind == "burnt":
            pyxel.load(BURNT_FILE)
        else:
            pyxel.load(BUTTER_FILE)

        # img0 の (0,0) を 16x16 描く
        pyxel.blt(x, y, 0, 0, 0, SPR_W, SPR_H, colkey=0)

    # =====================
    # 9) draw（毎フレーム描画）
    # =====================
    def draw(self):
        pyxel.cls(1)

        # タイトル画面
        if self.mode == "title":
            pyxel.cls(0)
            pyxel.text(72, 80, "PANCAKE STACK", 7)
            pyxel.text(36, 110, "Enter/Space: Start", 10)
            pyxel.text(36, 130, "Catch burnt -> Game Over", 6)
            pyxel.text(36, 145, "After enough stacks, butter comes!", 6)
            return

        # 積み上げ（パンケーキだけ）
        for i in range(self.stack):
            y = self.pad_y - (i + 1) * STACK_STEP_Y
            x = self.pad_x + (self.pad_w - SPR_W) // 2
            self.draw_sprite("pancake", x, y)

        # パッド
        pyxel.rect(self.pad_x, self.pad_y, self.pad_w, self.pad_h, 5)
        pyxel.rectb(self.pad_x, self.pad_y, self.pad_w, self.pad_h, 7)

        # 落下物
        if self.item is not None:
            self.draw_sprite(self.item["kind"], self.item["x"], self.item["y"])

        # 表示
        pyxel.text(8, 8, f"STACK: {self.stack}/{TARGET_STACK}", 7)
        if self.stack >= TARGET_STACK and not self.butter_spawned:
            pyxel.text(8, 18, "BUTTER INCOMING!", 10)

        # 結果画面
        if self.mode == "gameover":
            pyxel.rect(0, 90, W, 70, 0)
            pyxel.text(96, 110, "GAME OVER", 8)
            pyxel.text(50, 128, "R/Enter: Retry  Esc: Title", 7)

        if self.mode == "clear":
            pyxel.rect(0, 90, W, 70, 0)
            pyxel.text(110, 110, "CLEAR!", 11)
            pyxel.text(50, 128, "R/Enter: Play Again  Esc: Title", 7)


if __name__ == "__main__":
    App()
