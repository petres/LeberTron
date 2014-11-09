#!/usr/bin/python
import serial, sys, traceback
import time
import curses
import random
import input2 as inp
from curses import wrapper


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
        ys = y + t/4
        
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
        screen.addstr(y, x, sign, curses.A_BLINK)
    except Exception as e:
        print >> sys.stderr, "terminalSize:", screen.getmaxyx()
        print >> sys.stderr, "fieldPos:", fieldPos
        print >> sys.stderr, "fieldSize:", fieldSize
        print >> sys.stderr, "error writing sign to:", x, y
        print >> sys.stderr, traceback.format_exc()

        time.sleep(120)
        exit();



rightStatusWidth = 30

def init():
    global fieldPos, fieldSize, statusPos
    y, x = screen.getmaxyx()
    y -= 3 
    x -= 3 + rightStatusWidth
    fieldPos = (1, 1)
    fieldSize = (x, y)
    statusPos = (x + 5, 0)
    

moveStepSize = 3
spaceShipWidth = 6
points = 0

def printStatus():
    x, y = statusPos
    addSign((x, 1), "Sensor:")
    addSign((x, 2), "cm:      " + str(inp.curr))
    addSign((x, 3), "margins: " + str(inp.L_MAX) + " | " + str(inp.R_MAX))
    addSign((x, 4), "dir:     " + str(inp.state))

    addSign((x, 6), "Game:")
    addSign((x, 7), "points:  " + str(points))
    addSign((x, 7), "pos:     " + str(p))


def printSpaceShip(p):
    addSign((p, fieldSize[1] - 1), "I", True)
    addSign((p + 1, fieldSize[1] - 1), "/", True)
    addSign((p + 2, fieldSize[1] - 1), "\\", True)
    addSign((p - 1, fieldSize[1] - 1), "\\", True)
    addSign((p - 2, fieldSize[1] - 1), "/", True)

    addSign((p + 1, fieldSize[1] - 2), "\\", True)
    addSign((p, fieldSize[1] - 2), "I", True)
    addSign((p - 1, fieldSize[1] - 2), "/", True)


distSize = (5, 30)
p = 0

def main(s):
    global screen, p

    inp.main()

    screen = s
    screen.clear()
    screen.nodelay(1)
    #screen.curs_set(0)
    curses.curs_set(0)
    curses.start_color()
    init()
    t = 0
    p = fieldSize[0]/2
    while True:
        c = screen.getch()
        if c == ord('q'):
            break  # Exit the while loop
        #elif c == curses.KEY_LEFT or inp.state == -1:
        #    if (p - moveStepSize - spaceShipWidth/2) > 0: 
        #        p -= moveStepSize
        #elif c == curses.KEY_RIGHT or inp.state == 1:
        #    if (p + moveStepSize + spaceShipWidth/2) < fieldSize[0]: 
        #        p += moveStepSize

        p = int(float(inp.curr - distSize[0])/(distSize[1] - distSize[0])*fieldSize[0])

        if p > fieldSize[0] - spaceShipWidth:
            p = fieldSize[0] - spaceShipWidth
        elif p < spaceShipWidth:
            p = spaceShipWidth
        #p = 10

        screen.clear()
        printField()
        printObjects(t)
        printSpaceShip(p)
        printStatus()
        time.sleep(.02)
        if t%10 == 0:
            Object.createRandom(-t)
        t += 1

    inp.exitFlag = 1
    #t1.join()
    #t2.join()

    screen.refresh()

wrapper(main)