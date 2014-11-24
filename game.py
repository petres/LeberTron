#!/usr/bin/python2
# -*- coding: utf-8 -*-
import serial, sys, traceback
import time as timeLib
import curses
import random
import input as inp
from curses import wrapper

import codecs

import locale
locale.setlocale(locale.LC_ALL, "")

################################################################################
# HELPER FUNCTIONS
################################################################################

def getFromFile(fileName):
    #f = codecs.open("./objects/" + fileName + ".txt", 'r', "utf-8")
    f = open("./objects/" + fileName + ".txt", 'r')
    content = f.read().decode('utf-8')
    signsArray = []
    for line in content.split("\n"):
        signsArray.append(line)
    return signsArray

# signs = getFromFile("spaceInvadors/1")
#
# print signs
#
# for i, line in enumerate(signs):
#     for j, sign in enumerate(line):
#         print sign
#
# exit()
# ################################################################################
# OBJECT CLASS AND CHILDS
################################################################################

class Object(object):
    objects = []
    stdSpeed = 2
    def __init__(self, game, coords = None, signs = getFromFile("stone"), speed = None, color = None):
        self.game   = game
        self.coords = coords
        self.signs  = signs
        self.color  = color

        if speed is None:
            self.speed = random.randint(Object.stdSpeed/2, Object.stdSpeed*2)

        Object.objects.append(self)

        self.info = {}
        self.info['maxHeight']  = len(signs)
        self.info['rHeight']    = (len(signs) - 1)/2

        self.info['widths']  = []

        for line in signs:
            self.info['widths'].append(len(line))

        self.info['maxWidth']   = max(self.info['widths'])
        self.info['rWidth']     = (self.info['maxWidth'] - 1)/2



    def setRandomXPos(self, output, y = None):
        if y is None:
            y = -self.game.time/self.speed - 10
        x = random.randint(2 + self.info['rWidth'], output.fieldSize[0] - 2 - self.info['rWidth'])
        self.coords = (x, y)


    def getPosArray(self):
        posArray = []
        x, y = self.getMapCoords()
        #for i, width in enumerate(self.info["widths"]):
        #    for j in range(width):
        #        posArray.append((x - (width - 1)/2 + j, y - self.info["rHeight"] + i))
        for i, line in enumerate(self.signs):
            py = y - self.info['rHeight'] + i
            for j, sign in enumerate(line):
                if sign != " ":
                    px = x - self.info['rWidth'] + j
                    posArray.append((px, py))

        return posArray


    def check(self):
        if len(set(self.getPosArray()).intersection(self.game.spaceShip.getPosArray())) > 0:
            Object.objects.remove(self)
            self.collision()


    def collision():
        pass


    def getMapCoords(self):
        return (self.coords[0], self.coords[1] + self.game.time/self.speed)


    def draw(self, output):
        x, y = self.getMapCoords()
        if y > output.fieldSize[1] + self.info['rHeight']:
            Object.objects.remove(self)
            return

        for i, line in enumerate(self.signs):
            py = y - self.info['rHeight'] + i
            if py <= output.fieldSize[1] and py >= 0:
                for j, sign in enumerate(line):
                    if sign != " ":
                        px = x - self.info['rWidth'] + j
                        output.addSign((px, py), sign, field = True, color = self.color)
            #py = y - (len(self.signs) - 1)/2 + i
            #if py <= output.fieldSize[1] and py >= 0:
            #    output.addSign((x - (len(line) - 1)/2, py), line, field = True, color = self.color)



class Obstacle(Object):
    #obstacles = ['spaceInvador', 'bigStone', 'stone']
    obstacles = ['spaceInvadors/1', 'spaceInvadors/2', 'spaceInvadors/3',
                    'spaceInvadors/4', 'spaceInvadors/5']

    def collision(self):
        self.game.lifeLost()

    def __init__(self, game, **args):
        if "signs" not in args:
            i = random.randint(0, len(Obstacle.obstacles) - 1)
            args["signs"] = getFromFile(Obstacle.obstacles[i])
        super(Obstacle, self).__init__(game, **args)



class Goody(Object):
    def collision(self):
        self.game.status['points'] = self.game.status['points'] + 5
        self.game.status['goodies'].append(self)


    def __init__(self, game, **args):
        if "signs" not in args:
            args["signs"] = getFromFile("vodka")
            args["color"] = 2
        super(Goody, self).__init__(game, **args)


class SpaceShip(Object):
    def getMapCoords(self):
        return (self.coords[0], self.coords[1])
    def check(self):
        return








################################################################################
# OUTPUT CLASSES
################################################################################

class Output(object):
    rightStatusWidth = 30
    fieldPos  = None
    fieldSize = None
    statusPos = None

    def __init__(self):

        screen.clear()
        screen.nodelay(1)
        #screen.curs_set(0)
        curses.curs_set(0)
        curses.start_color()

        curses.use_default_colors()
        for i in range(0, curses.COLORS):
            curses.init_pair(i + 1, i, -1)

        y, x = screen.getmaxyx()
        y -= 3
        x -= 3 + Output.rightStatusWidth
        self.fieldPos = (1, 1)
        self.fieldSize = (x, y)
        self.statusPos = (x + 5, 0)


    def printGame(self, game):
        screen.clear()

        self.printField()
        self.printStatus(game)

        for o in list(Object.objects):
            o.draw(self)


    def printField(self):
        for i in range(self.fieldPos[0] - 1, self.fieldPos[0] + self.fieldSize[0] + 2):
            self.addSign((i, self.fieldPos[1] - 1), u"█")
            self.addSign((i, self.fieldPos[1] + self.fieldSize[1] + 1), u"█")

        for i in range(self.fieldPos[1] - 1, self.fieldPos[1] + self.fieldSize[1] + 2):
            self.addSign((self.fieldPos[0] - 1, i), u"█", color = None)
            self.addSign((self.fieldPos[0] + self.fieldSize[0] + 1, i), u"█")

    def printStatus(self, game):
        x, y = self.statusPos
        self.addSign((x, 1), "Sensor:")
        #addSign((x, 2), "cm:      " + str(inp.curr))
        #addSign((x, 4), "dir:     " + str(inp.state))

        self.addSign((x, 6), "Game:")
        self.addSign((x, 7), "points:  " + str(game.status['points']))
        self.addSign((x, 8), "lifes:   " + str(game.status['lifes']))
        self.addSign((x, 9), "time:    " + str(game.time))
        self.addSign((x,10), "objects: " + str(len(Object.objects)))

        # Change list creation :)
        goodies = [goody.signs[0] for goody in game.status["goodies"]]

        self.printGlass(x, 12, goodies)


    def printGlass(self, x, y, goodies):
        top    = getFromFile("glass/top")
        bottom = getFromFile("glass/bottom")

        body    = []
        h = max(6, len(goodies))
        for i in range(h, -1, -1):
            if i > len(goodies) or len(goodies) == 0:
                body.append("||             ||")

            elif i == len(goodies):
                body.append("|:--.._____..--:|")

            elif i < len(goodies):
                body.append("||" + goodies[i].center(13, " ") + "||")

        glass = top + body + bottom
        for l in glass:
            y += 1
            self.addSign((x, y), l)


    def addSign(self, coords, sign, field = False, color = None):
        x, y = coords
        if field:
            x += self.fieldPos[0]
            y += self.fieldPos[1]
        try:
            if color:
                screen.addstr(y, x, sign.encode('utf_8'), curses.color_pair(color))
            else:
                screen.addstr(y, x, sign.encode('utf_8'))
        except Exception as e:
            print >> sys.stderr, "terminalSize:", screen.getmaxyx()
            print >> sys.stderr, "fieldPos:", self.fieldPos
            print >> sys.stderr, "fieldSize:", self.fieldSize
            print >> sys.stderr, "error writing sign to:", x, y
            print >> sys.stderr, traceback.format_exc()

            timeLib.sleep(120)
            exit();


################################################################################
# CONTROLLER CLASSES
################################################################################

class Controller(object):
    LEFT    = -1
    RIGHT   =  1
    QUIT    = 10
    RETRY   = 11
    def getInput(self):
        raise NotImplementedError


class UltraSonicController(object):
    def __init__(self, serialPort):
        self.distPos    = (15, 50)
        inp.connect(serialPort)
        inp.start()

    def getInput(self):
        if inp.state == -1:
            return Controller.LEFT
        elif inp.state == 1:
            return Controller.RIGHT
        return None

    # def getPosition(self):
    #     float(inp.curr - self.distPos[0])/(self.distPos[1] - self.distPos[0])



class KeyboardController(object):
    def __init__(self, screen):
        self.screen = screen
        self.screen.nodelay(1)

    def getInput(self):
        c = self.screen.getch()

        if c == curses.KEY_LEFT:
            return Controller.LEFT
        elif c == curses.KEY_RIGHT:
            return Controller.RIGHT
        elif c == ord('q'):
            return Controller.QUIT
        elif c == ord('r'):
            return Controller.RETRY
        # try:
        #     value = int(c)
        #     return float(value - 1)/8
        # except ValueError:


        return None


################################################################################
# GAME CLASS
################################################################################

class Game(object):
    spaceShip   = None
    time        = None
    status      = None
    moveStepSize = 3

    def __init__(self, controller, output):
        self.controller = controller
        self.output = output

    def prepare(self):
        self.time = 0
        self.status = {}
        self.status['points'] = 0
        self.status['goodies'] = []
        self.status['lifes']  = 3
        self.removeObjectsAndCreateSpaceship()

    def removeObjectsAndCreateSpaceship(self):
        Object.objects = []
        self.spaceShip = SpaceShip(self, signs = getFromFile("spaceShip"), color = 3)
        self.spaceShip.coords = (self.output.fieldSize[0]/2, self.output.fieldSize[1] - 2)


    def run(self):
        while True:
            d = self.controller.getInput()
            m = 0
            if d == Controller.LEFT:
                m = -1
            elif d == Controller.RIGHT:
                m = 1
            elif d == Controller.QUIT:
                break

            x = self.spaceShip.coords[0]
            x += m*self.moveStepSize

            # CHECK MARGINS
            if x > self.output.fieldSize[0] - self.spaceShip.info['maxWidth']:
                x = self.output.fieldSize[0] - self.spaceShip.info['maxWidth']
            elif x < self.spaceShip.info['maxWidth']:
                x = self.spaceShip.info['maxWidth']

            self.spaceShip.coords = (x, self.spaceShip.coords[1])

            for o in list(Object.objects):
                o.check()

            self.output.printGame(self)

            timeLib.sleep(.03)
            if self.time%100 == 0:
                g = Goody(self)
                g.setRandomXPos(self.output)
            if self.time%50 == 0:
                o = Obstacle(self)
                o.setRandomXPos(self.output)

            self.time += 1


    def end(self):
        self.spaceShip = None
        screen.clear()
        self.output.printField()
        self.output.printStatus()
        screen.nodelay(0)
        c = screen.getch()

        if c == ord('r'):
            self.init()
        else:
            exit()

        screen.nodelay(1)

    def lifeLost(self):
        self.status['lifes'] = self.status['lifes'] - 1

        if self.status['lifes'] == 0:
            self.end()
        else:
            self.removeObjectsAndCreateSpaceship()


def main(s):
    global screen
    screen = s

    o = Output()

    #c = UltrasonicController("/dev/ttyACM0")
    c = KeyboardController(screen)

    g = Game(c, o)
    g.prepare()
    g.run()

    inp.exitFlag = 1
    timeLib.sleep(1)
    screen.refresh()

wrapper(main)
