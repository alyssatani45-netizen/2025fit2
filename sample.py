import pyxel

pyxel.init(200,200)

a = 0

direction = 1

def update():
    global a, direction
    a +=  direction

    if a>=200:
        a=200
        direction = -1

    if a<=0:
        a=0
        direction = 1
        
def draw():
    global a
    pyxel.cls(7)
    pyxel.circ(a, a, 10, 0)


pyxel.run(update, draw)
