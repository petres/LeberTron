#!/usr/bin/python
import serial
import time
import curses
import random
from curses import wrapper


# ser = serial.Serial('/dev/ttyACM0', 9600)
# while True:
#   print ser.readline()
#   time.sleep(0.1)


# stdscr = curses.initscr()
# curses.noecho()
# curses.cbreak()
# stdscr.keypad(True)


# def end():
#   curses.nocbreak()
#   stdscr.keypad(False)
#   curses.echo()
#   curses.endwin()

class Object:
    objects = []
    def __init__(self, coords):
        self.coords = coords
        self.sign = "O"
        Object.objects.append(self)

    @classmethod
    def createRandom(cls, y = 0):
        x = random.randint(2, fieldSize[0] - 2)
        Object((x,y))




def printField():
    for i in range(fieldPos[0] - 1, fieldPos[0] + fieldSize[0] + 2):
        addSign((i, fieldPos[1] - 1), "X")
        addSign((i, fieldPos[1] + fieldSize[1] + 1), "X")

    for i in range(fieldPos[1] - 1, fieldPos[1] + fieldSize[1] + 2):
        addSign((fieldPos[0] - 1, i), "X")
        addSign((fieldPos[0] + fieldSize[0] + 1, i), "X")

def printObjects(t):
    for o in list(Object.objects):
        x, y = o.coords
        ys = y + t
        
        if ys > fieldSize[1]:
            Object.objects.remove(o)
            continue

        if ys < 0:
            continue

        addSign((x, ys), o.sign, True)

fieldPos  = None
fieldSize = None

def addSign(coords, sign, field = False):
    x, y = coords
    if field:
        x += fieldPos[0]
        y += fieldPos[1]
    try:
        screen.addstr(y, x, sign)
    except Exception as e:
        print "terminalSize:", screen.getmaxyx()
        print "fieldPos:", fieldPos
        print "fieldSize:", fieldSize
        print "error writing sign to:", x, y

        time.sleep(120)
        exit();

rightStatusWidth = 30

def init():
    global fieldPos, fieldSize
    y, x = screen.getmaxyx()
    y -= 3 
    x -= 3 + rightStatusWidth
    fieldPos = (1, 1)
    fieldSize = (x, y)


Object((5,0))

Object((15,0))

Object((30,10))

Object((20,-20))

Object((30,-10))

moveStepSize = 3
spaceShipWidth = 6

def printSpaceShip(p):
    addSign((p, fieldSize[1] - 1), "I", True)
    addSign((p + 1, fieldSize[1] - 1), "*", True)
    addSign((p + 2, fieldSize[1] - 1), "\\", True)
    addSign((p - 1, fieldSize[1] - 1), "*", True)
    addSign((p - 2, fieldSize[1] - 1), "/", True)

    addSign((p + 1, fieldSize[1] - 2), "\\", True)
    addSign((p, fieldSize[1] - 2), "I", True)
    addSign((p - 1, fieldSize[1] - 2), "/", True)

def main(s):
    global screen
    screen = s
    screen.clear()
    screen.nodelay(1)
    #screen.curs_set(0)
    curses.curs_set(0)
    init()
    t = 0
    p = fieldSize[0]/2
    while True:
        c = screen.getch()
        if c == ord('q'):
            break  # Exit the while loop
        elif c == curses.KEY_LEFT:
            if (p - moveStepSize - spaceShipWidth/2) > 0: 
                p -= moveStepSize
        elif c == curses.KEY_RIGHT:
            if (p + moveStepSize + spaceShipWidth/2) < fieldSize[0]: 
                p += moveStepSize


        screen.clear()
        printField()
        printObjects(t)
        printSpaceShip(p)
        time.sleep(.2)
        if t%10 == 0:
            Object.createRandom(-t)
        t += 1

    screen.refresh()

wrapper(main)