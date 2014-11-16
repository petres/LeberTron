#!/usr/bin/python2
import serial, sys, traceback
import time as timeLib
import curses
import random
import input2 as inp
from curses import wrapper

STD_SPEED = 5


time = 0

obstacle1 = [
         '''/O0O\ ''',
        '''/     \ ''',
        '''\_____/ '''
    ]

spaceShipSigns = [
         '''/T\ ''',
        '''/ _ \ ''',
        '''TT TT '''
    ]

def getFromFile(fileName):
    f = open("./objects/" + fileName + ".txt", 'r')
    content = f.read()
    signsArray = []
    for line in content.split("\n"):
        temp = line.strip()
        signsArray.append(temp)
    return signsArray


class Object:
    objects = []
    def __init__(self, coords = None, signs = getFromFile("stone"), speed = None, randomX = False):
        self.coords = coords
        self.signs  = signs

        if speed is None:
            self.speed = random.randint(STD_SPEED - 2, STD_SPEED + 2)

        Object.objects.append(self)

        self.info = {}
        self.info['maxHeight'] = len(signs)
        self.info['maxWidth'] = 0


        self.info['rHeight'] = (len(signs) - 1)/2

        self.info['widths'] = []

        for line in signs:
            self.info['widths'].append(len(line))

        self.info['maxWidth'] = max(self.info['widths'])
        self.info['rWidth']  = (self.info['maxWidth'] - 1)/2

        if randomX:
            self.setRandomXPos()

    def setRandomXPos(self, y = None):
        if y is None:
            y = -time/self.speed
        x = random.randint(2 + self.info['rWidth'], fieldSize[0] - 2 - self.info['rWidth'])
        self.coords = (x, y)


    def getPosArray(self):
        posArray = []
        x, y = self.getMapCoords()
        for i, width in enumerate(self.info["widths"]):
            for j in range(width):
                posArray.append((x - (width - 1)/2 + j, y - self.info["rHeight"] + i))
        return posArray


    def check(self):
        global points

        x, y = self.getMapCoords()
        if y > fieldSize[1] + self.info['rHeight']:
            Object.objects.remove(self)

        if len(set(self.getPosArray()).intersection(spaceShip.getPosArray())) > 0:
            Object.objects.remove(self)
            points += 1



    def getMapCoords(self):
        return (self.coords[0], self.coords[1] + time/self.speed)


    def draw(self):
        x, y = self.getMapCoords()
        if y < 0:
            return

        for i, line in enumerate(self.signs):
            py = y - (len(self.signs) - 1)/2 + i
            if py <= fieldSize[1]:
                addSign((x - (len(line) - 1)/2, py), line, True)


class SpaceShip(Object):
    def getMapCoords(self):
        return (self.coords[0], self.coords[1])
    def check(self):
        return


def printField():
    for i in range(fieldPos[0] - 1, fieldPos[0] + fieldSize[0] + 2):
        addSign((i, fieldPos[1] - 1), "X")
        addSign((i, fieldPos[1] + fieldSize[1] + 1), "X")

    for i in range(fieldPos[1] - 1, fieldPos[1] + fieldSize[1] + 2):
        addSign((fieldPos[0] - 1, i), "X")
        addSign((fieldPos[0] + fieldSize[0] + 1, i), "X")



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

        timeLib.sleep(120)
        exit();



rightStatusWidth = 30

def init():
    global fieldPos, fieldSize, statusPos

    screen.clear()
    screen.nodelay(1)
    #screen.curs_set(0)
    curses.curs_set(0)
    curses.start_color()

    y, x = screen.getmaxyx()
    y -= 3
    x -= 3 + rightStatusWidth
    fieldPos = (1, 1)
    fieldSize = (x, y)
    statusPos = (x + 5, 0)








spaceShip = SpaceShip(signs = getFromFile("spaceShip"))

spaceShip.coords = (0, 0)
#print spaceShip.getPosArray()
#exit()

def initGame():
    global time

    time = 0
    spaceShip.coords = (fieldSize[0]/2, fieldSize[1] - 2)


moveStepSize = 3
points = 0



def printStatus():
    x, y = statusPos
    addSign((x, 1), "Sensor:")
    addSign((x, 2), "cm:      " + str(inp.curr))
    addSign((x, 3), "margins: " + str(inp.L_MAX) + " | " + str(inp.R_MAX))
    addSign((x, 4), "dir:     " + str(inp.state))

    addSign((x, 6), "Game:")
    addSign((x, 7), "points:  " + str(points))
    addSign((x, 9), "time:    " + str(time))
    addSign((x,10), "objects: " + str(len(Object.objects)))




#def printSpaceShip():
#    x, y = spaceShipPos
#    for i, line in enumerate(spaceShipSigns):
#        addSign((x - (len(line) - 1)/2, y - (len(spaceShipSigns) - 1)/2 + i),  line, True)



distSize = (5, 30)

def main(s):
    global screen, spaceShipPos, time
    screen = s

    inp.main()

    init()

    initGame()

    while True:
        c = screen.getch()
        x = spaceShip.coords[0]
        if c == ord('q'):
            break  # Exit the while loop
        elif c == curses.KEY_LEFT or inp.state == -1:
            if (x - moveStepSize - spaceShip.info['maxWidth']/2) > 0:
                x -= moveStepSize
        elif c == curses.KEY_RIGHT or inp.state == 1:
            if (x + moveStepSize + spaceShip.info['maxWidth']/2) < fieldSize[0]:
                x += moveStepSize

        #p = int(float(inp.curr - distSize[0])/(distSize[1] - distSize[0])*fieldSize[0])

        if x > fieldSize[0] - spaceShip.info['maxWidth']:
            x = fieldSize[0] - spaceShip.info['maxWidth']
        elif x < spaceShip.info['maxWidth']:
            x = spaceShip.info['maxWidth']

        spaceShip.coords = (x, spaceShip.coords[1])

        screen.clear()
        printField()

        for o in list(Object.objects):
            o.check()

        for o in list(Object.objects):
            o.draw()

        #printSpaceShip()
        printStatus()
        timeLib.sleep(.02)
        if time%40 == 0:
            Object(randomX = True)
        time += 1

    inp.exitFlag = 1
    screen.refresh()

wrapper(main)
