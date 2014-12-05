#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import glob
import curses
import locale
import random
import logging
import string
import threading
import time as timeLib
from ConfigParser import SafeConfigParser

# Change working directory to the file directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# setup log file to subdir
logging.basicConfig(filename='log/error.log', level=logging.DEBUG,
                    format='%(levelname)8s - %(asctime)s: %(message)s')


sys.path.append("./lib")

import sound2 as soundLib
from botComm import BotComm

locale.setlocale(locale.LC_ALL, "")

screen = None
inp = None
################################################################################
# HELPER FUNCTIONS
################################################################################

def getFromFile(fileName):
    # f = codecs.open("./objects/" + fileName + ".txt", 'r', "utf-8")
    f = open(fileName, 'r')
    content = f.read().decode('utf-8')
    signsArray = []
    for line in content.split("\n"):
        signsArray.append(line)
    return signsArray


# ################################################################################
# OBJECT CLASS AND CHILDS
################################################################################

class Object(object):
    objects = []
    stdSpeed = 2

    def __init__(self, game, coords=None, signs=None, speed=None, color=None, signsArray=[], switchSignsTime=None):
        self.game            = game
        self.coords          = coords
        self.signs           = signs
        self.color           = color
        self.startTime       = game.time
        self.signsArray      = signsArray
        self.switchSignsTime = switchSignsTime

        if speed is None:
            self.speed = random.randint(
                Object.stdSpeed, Object.stdSpeed * 2)
        else:
            self.speed = speed

        Object.objects.append(self)

        if len(signsArray) > 0:
            self.currentSigns = 0
            self.signs = signsArray[0]

        self.info = {}
        self.info['maxHeight']  = len(signs)
        self.info['rHeight']    = (len(signs) - 1)/2

        tmp  = []
        for line in signs:
            tmp.append(len(line))

        self.info['maxWidth']   = max(tmp)
        self.info['rWidth']     = (self.info['maxWidth'] - 1)/2


    def setRandomXPos(self, output, y=None):
        if y is None:
            y = 0
        x = random.randint(
            2 + self.info['rWidth'], output.fieldSize[0] - 2 - self.info['rWidth'])
        self.coords = (x, y)


    def getPosArray(self):
        posArray = []
        x, y = self.getMapCoords()
        # for i, width in enumerate(self.info["widths"]):
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
            try:
                Object.objects.remove(self)
            except ValueError as e:
                pass
            self.collision()

    def collision(self):
        pass

    def getMapCoords(self):
        return (self.coords[0], self.coords[1] + (self.game.time - self.startTime) / self.speed)

    def draw(self, output):
        x, y = self.getMapCoords()

        if y > output.fieldSize[1] + self.info['rHeight']:
            Object.objects.remove(self)
            return

        if y < -10:
            Object.objects.remove(self)
            return

        if len(self.signsArray) > 0:
            if self.game.time % self.switchSignsTime == 0:
                self.currentSigns += 1
                self.currentSigns = self.currentSigns % len(self.signsArray)
                self.signs = self.signsArray[self.currentSigns]

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



class Shoot(Object):
    soundShooting   = None
    soundCollision  = None
    lastStartTime   = 0
    diffBetween     = 15
    def __init__(self, game, **args):
        logging.debug("init Shoot")
        if Shoot.lastStartTime > game.time - Shoot.diffBetween:
            return

        Shoot.lastStartTime = game.time

        args["signs"] = getFromFile("./objects/shoot.txt")
        args["color"] = 2
        args["speed"] = 1
        if Shoot.soundShooting is not None:
            Shoot.soundShooting.play()
        super(Shoot, self).__init__(game, **args)

    def getMapCoords(self):
        return (self.coords[0], self.coords[1] - (self.game.time - self.startTime) / self.speed)

    def check(self):
        for o in Object.objects:
            if isinstance(o, Obstacle):
                if len(set(self.getPosArray()).intersection(o.getPosArray())) > 0:
                    Object.objects.remove(o)
                    Object.objects.remove(self)
                    if Shoot.soundCollision is not None:
                        Shoot.soundCollision.play()
                    break


class Obstacle(Object):
    obstacles   = []
    cSpaceship  = None

    def collision(self):
        if Obstacle.cSpaceship is not None:
            Obstacle.cSpaceship.play()
        self.game.lifeLost()


    def __init__(self, game, **args):
        if "signs" not in args:
            i = random.randint(0, len(Obstacle.obstacles) - 1)
            args["signs"] = getFromFile(Obstacle.obstacles[i])
            args["color"] = Obstacle.color
        super(Obstacle, self).__init__(game, **args)



class Goody(Object):
    types       = []
    cSpaceship  = None
    portion     = None
    volume      = None
    generateT   = None

    def collision(self):
        if Goody.cSpaceship is not None:
            Goody.cSpaceship.play()
        self.game.status['ml']    += Goody.portion * Goody.types[self.type]["factor"]
        self.game.status['goodies'].append(self.type)

        if self.game.robot is not None:
            self.game.robot.pourBottle(Goody.types[self.type]["arduino"], Goody.portion * Goody.types[self.type]["factor"])
        if self.game.status['ml'] >= Goody.volume:
            self.game.full()

    def __init__(self, game, **args):
        self.type = self.getNextGoodyType(game.status["goodies"])

        args["signs"] = getFromFile(Goody.types[self.type]["design"])
        args["color"] = Goody.types[self.type]["color"]

        super(Goody, self).__init__(game, **args)

    def getNextGoodyType(self, collectedGoodies):
        #return random.randint(0, len(Goody.types) - 1)


        weights = [4096] * len(Goody.types)
        for i, wGoody in enumerate(Goody.types):
            if wGoody['category'] == "A":
                weights[i] = 4096
            else:
                weights[i] = 8192


        # for goody in collectedGoodies:
        #     cat = Goody.types[goody]['category']
        #     for i, wGoody in enumerate(Goody.types):
        #         if cat == "A":
        #             if wGoody['category'] == "A" and i != goody:
        #                 weights[i] = weights[i]/4
        #             if i == goody:
        #                 weights[i] = weights[i]*2
        #         elif cat == "N":
        #             if wGoody['category'] == "N" and i != goody:
        #                 weights[i] = weights[i]/2


        #         if Goody.types[wGoody]['category'] == cat

        if Goody.generateT:
            if Goody.generateT == "N":
                for i, wGoody in enumerate(Goody.types):
                    if wGoody['category'] == "A":
                        weights[i] = 0


        t = random.randint(0, sum(weights))

        s = 0
        for i in range(len(weights)):
            s = s + weights[i]
            if t <= s:
                return i


class SpaceShip(Object):
    design  = getFromFile("./objects/spaceShip.txt")
    designArray = []
    color   = None
    blinkColor = 2
    def __init__(self, game, **args):
        if "signs" not in args:
            args["signs"] = getFromFile(SpaceShip.design)
            signsArray = []
            for design in SpaceShip.designArray:
                signsArray.append(getFromFile(design))
            args["signsArray"] = signsArray
            args["color"] = SpaceShip.color
            args["switchSignsTime"] = 10
            self.switchBlinkTime = 8
            self.switchBlinkDur = 50
            self.blinking = False
        super(SpaceShip, self).__init__(game, **args)

    def getMapCoords(self):
        return (self.coords[0], self.coords[1])

    def check(self):
        if self.blinking:
            if self.blinkTime % self.switchBlinkTime == 0:
                if self.blinkTime > self.switchBlinkDur:
                    self.color, self.blinkColor = self.orgColor, self.orgBlinkColor
                    self.blinking = False
                else:
                    self.color, self.blinkColor  = self.blinkColor, self.color
            self.blinkTime += 1
        return

    def blink(self):
        self.orgColor, self.orgBlinkColor = self.color, self.blinkColor
        self.blinkTime = 0
        self.blinking = True






################################################################################
# OUTPUT CLASSES
################################################################################

class Output(object):
    statusWidth = 28

    def __init__(self):
        screen.nodelay(1)
        curses.curs_set(0)
        curses.start_color()

        curses.use_default_colors()
        for i in range(0, curses.COLORS):
            curses.init_pair(i + 1, i, -1)

        logging.warning("Possible number of different colors: %s" %
                        curses.COLORS)

        self.screenSize = screen.getmaxyx()
        y, x = self.screenSize
        y -= 3
        x -= 3 + Output.statusWidth
        self.fieldPos = (1, 1)
        self.fieldSize = (x, y)
        self.statusPos = (x + 4, 0)
        self.statusSize = (Output.statusWidth - 3,  y + 2)
        self.printField()

    def prepareGame(self):
        screen.clear()
        self.printField()

    def printGame(self, game):
        # screen.clear()

        self.clearField(self.fieldPos, self.fieldSize, sign=" ")
        self.clearField(self.statusPos, self.statusSize, sign=" ")

        # self.printField()
        self.printStatus(game)

        for o in list(Object.objects):
            o.draw(self)

    def printField(self):
        fieldColor = 0
        for i in range(self.fieldPos[0] - 1, self.fieldPos[0] + self.fieldSize[0] + 2):
            self.addSign((i, self.fieldPos[1] - 1), u"█", color = fieldColor)
            self.addSign((i, self.fieldPos[1] + self.fieldSize[1] + 1), u"█", color = fieldColor)

        for i in range(self.fieldPos[1] - 1, self.fieldPos[1] + self.fieldSize[1] + 2):
            self.addSign((self.fieldPos[0] - 1, i), u"█", color = fieldColor)
            self.addSign((self.fieldPos[0] + self.fieldSize[0] + 1, i), u"█", color = fieldColor)

    def clearField(self, pos, size, sign=" "):
        for i in range(pos[1], pos[1] + size[1] + 1):
            self.addSign((pos[0], i), sign * (size[0] + 1))

    def printStatus(self, game):
        x, y = self.statusPos
        x = x + 3
        # self.addSign((x, 1), "Sensor:")
        # if inp is not None:
        #     self.addSign((x, 2), "cm slid: " + str(round(self.inp.position)))
        #     self.addSign((x, 3), "cm now:  " + str(round(inp.currA)))
        #     self.addSign((x, 4), "shoot:   " + str(round(inp.shoot)))
        #     self.addSign((x, 5), "shoot d: " + str(round(inp.shootDist)))

        y = 12
        for i, line in enumerate(getFromFile("./objects/heart.txt")):
            self.addSign((x - 1, y + 1 + i), line, color = 2)
            #self.addSign((x, 10 + i), line, color = curses.COLOR_RED)

        for i, line in enumerate(getFromFile("./objects/lifes/" + str(game.status['lifes']) + ".txt")):
            self.addSign((x, y + 8 + i), line)

        x += 14

        for i, line in enumerate(getFromFile("./objects/bottle2.txt")):
            self.addSign((x, y - 1 + i), line, color = 4)

        for i, line in enumerate(getFromFile("./objects/lifes/" + str(len(game.status['goodies'])) + ".txt")):
            self.addSign((x, y + 8 + i), line)
        # self.addSign((x,10), "count:  " + str(game.status['count']))
        # self.addSign((x,11), "lifes:   " + str(game.status['lifes']))
        # self.addSign((x,12), "time:    " + str(game.time))
        # self.addSign((x,13), "objects: " + str(len(Object.objects)))

        self.printGlass(x - 13, self.screenSize[0] - 23, game.status["goodies"])

        if self.screenSize[0] - 23 - (y + 15) > 10:
            for i, line in enumerate(getFromFile("./objects/lebertron.txt")):
                self.addSign((self.statusPos[0] + 1,  (y + 16) + (self.screenSize[0] - 23 - (y + 15) - 9)/2 + i), line, color = 7)


        self.printRandomSigns((self.statusPos[0] + 1, self.statusPos[1] + 1), (self.statusSize[0], 7), 6)

        if Goody.generateT:
            self.addSign((self.statusPos[0] + 2, self.statusPos[1] + 2), Goody.generateT, color = 6)

    def printCountdown(self, nr):
        self.fieldCenteredOutput("./screens/countdown/" + str(nr) + ".txt")

    def fieldCenteredOutput(self, file):
        signs = getFromFile(file)
        w, h = (len(signs[0]), len(signs))
        x, y = self.fieldSize
        bx = (x - w) / 2
        by = (y - h) / 2
        for i, line in enumerate(signs):
            ty = by + i
            self.addSign((bx, ty), line, True)

    def printGlass(self, x, y, goodies):
        top = getFromFile("./objects/glass/top.txt")
        bottom = getFromFile("./objects/glass/bottom.txt")

        body = []
        h = max(10, len(goodies))
        for i in range(h, -1, -1):
            if i > len(goodies) or len(goodies) == 0:
                body.append("||             ||")
            elif i == len(goodies):
                body.append("|:--.._____..--:|")
            elif i < len(goodies):
                body.append("||" + Goody.types[goodies[i]]["name"].center(13, " ") + "||")

        glass = top[:-1] + body + bottom
        for l in glass:
            y += 1
            self.addSign((x, y), l)

    def printRandomSigns(self, pos, size, color):
        for i in range(size[1]):
            self.addSign((pos[0], pos[1] + i), ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(size[0])), color = color)



    def addSign(self, coords, sign, field=False, color=None):
        x, y = coords
        if field:
            x += self.fieldPos[0]
            y += self.fieldPos[1]
        try:
            if color:
                screen.addstr(
                    y, x, sign.encode('utf_8'), curses.color_pair(color))
            else:
                screen.addstr(y, x, sign.encode('utf_8'))
        except:
            logging.debug("terminalSize: %s" % screen.getmaxyx())
            logging.debug("fieldPos: %s" % self.fieldPos)
            logging.debug("fieldSize: %s" % self.fieldSize)
            logging.debug("error writing sign to: %s" % x, y)
            logging.exception()

            # FIXME what does this sleep? do we really need to block for 2min?
            timeLib.sleep(120)
            raise


################################################################################
# CONTROLLER CLASSES
################################################################################

class Controller(object):
    LEFT    = -1
    RIGHT   =  1
    QUIT    = -10
    RETRY   = -11
    SHOOT   = -12
    PAUSE   = -13
    SWITCH_NON_ALC = -14

    def __init__(self, screen, position):
        self.screen = screen
        self.position = position

    def getInput(self):
        # implemented by sub class
        raise NotImplementedError

    def close(self):
        pass


class UltraSonicController(Controller):
    distPos    = (5, 50)
    def __init__(self, serialPort, twoSensors, screen, position=False):
        import inputComm as ultraSonicInput
        self.inp = ultraSonicInput.InputComm(serialPort, twoSensors = twoSensors,
                        distanceMin = UltraSonicController.distPos[0], distanceMax = UltraSonicController.distPos[1])

        super(UltraSonicController, self).__init__(screen, position)

    def getInput(self):
        c = self.screen.getch()

        if c == ord('q'):
            return Controller.QUIT
        elif c == ord('r'):
            return Controller.RETRY
        elif c == ord('p'):
            return Controller.PAUSE
        elif c == ord('n'):
            Goody.generateT = "N"
        elif c == ord('o'):
            Goody.generateT = "O"
        elif c == ord('c'):
            Goody.generateT = None

        if self.inp.fetchBullet():
            return Controller.SHOOT

        if self.inp.state == -1:
            return Controller.LEFT
        elif self.inp.state == 1:
            return Controller.RIGHT

    def getPosition(self):
        if self.mirror:
            return 1 - float(self.inp.position - self.distPos[0]) / (self.distPos[1] - self.distPos[0])
        else:
            return float(self.inp.position - self.distPos[0]) / (self.distPos[1] - self.distPos[0])

    def close(self):
        self.inp.close()


class KeyboardController(Controller):

    def __init__(self, screen, position):
        super(KeyboardController, self).__init__(screen, position)

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
        elif c == ord(' '):
            return Controller.SHOOT
        elif c == ord('p'):
            return Controller.PAUSE
        elif c == ord('n'):
            Goody.generateT = "N"
        elif c == ord('o'):
            Goody.generateT = "O"
        elif c == ord('c'):
            Goody.generateT = None
        # try:
        #     value = int(c)
        #     return float(value - 1)/8
        # except ValueError:

        return None


################################################################################
# GAME CLASS
################################################################################

class Game(object):
    moveStepSize = 3
    background  = None
    createObjects = False
    countdownTime = 30
    sleepTime     = 100

    obstacleCreationTime = 10
    goodyCreationTime = 10

    def __init__(self, controller, output, robot=None):
        self.time       = 0
        self.controller = controller
        self.output     = output
        self.robot      = robot
        self.pause      = False
        self.spaceShip  = SpaceShip(self)
        self.spaceShip.coords = (
            self.output.fieldSize[0] / 2, self.output.fieldSize[1] - 2)
        self.countdown  = 0

        self.status     = {}
        self.setStartStatus()
        self.overlay    = None
        self.oStatus    = None
        self.oTime      = None
        self.cupThere   = False
        self.gameStarted = False

    def removeObjects(self):
        logging.debug("removing objects")
        Object.objects = [self.spaceShip]

    def setStartStatus(self):
        self.status['goodies'] = []
        self.status['lifes']   = 3
        self.status['ml']      = 0


    def prepare(self):
        self.time   = 0
        self.removeObjects()
        self.createObjects = False
        self.setStartStatus()
        self.output.prepareGame()
        self.countdown = 3
        self.overlay = None
        self.oStatus = None
        self.gameStarted = True
        self.cupThere = False
        Shoot.lastStartTime = 0
        if Game.background is not None:
            Game.background.loop()

    def run(self):
        logging.info('Starting main loop...')
        while True:
            d = self.controller.getInput()

            if d == Controller.QUIT:
                break
            elif d == Controller.SHOOT:
                o = Shoot(self, coords = (self.spaceShip.coords[0], self.spaceShip.coords[1] - self.spaceShip.info['rHeight'] - 1))

            # start game
            if d == Controller.RETRY or (not self.gameStarted and self.cupThere):
                self.prepare()

            if d == Controller.PAUSE:
                self.switchPause()

            if self.controller.position == False:
                m = 0
                if d == Controller.LEFT:
                    m = -1
                elif d == Controller.RIGHT:
                    m = 1

                x = self.spaceShip.coords[0]
                x += m * self.moveStepSize
            else:
                x = int(self.controller.getPosition() * self.output.fieldSize[0])

            # CHECK MARGINS
            if x > self.output.fieldSize[0] - self.spaceShip.info['rWidth'] - 1:
                x = self.output.fieldSize[0] - self.spaceShip.info['rWidth'] - 1
            elif x < self.spaceShip.info['rWidth'] + 1:
                x = self.spaceShip.info['rWidth'] + 1

            self.spaceShip.coords = (x, self.spaceShip.coords[1])

            for o in list(Object.objects):
                o.check()

            self.output.printGame(self)

            # COUNTDOWN
            if self.countdown > 0:
                self.output.printCountdown(self.countdown)
                if self.time > Game.countdownTime:
                    logging.info("countdown=%d" % self.countdown)
                    self.countdown -= 1
                    self.time = 0
                    if self.countdown == 0:
                        self.createObjects = True

            if self.oStatus is not None:
                 self.overlay = self.oStatus


            if self.overlay is not None:
                if self.overlay == "overLifes":
                    self.output.fieldCenteredOutput("./screens/lifes.txt")
                elif self.overlay == "overFull":
                    self.output.fieldCenteredOutput("./screens/full.txt")
                elif self.overlay == "refillBottle":
                    self.output.fieldCenteredOutput("./screens/refill.txt")

            if (self.overlay == 'overLifes' or self.overlay == 'overFull') and not self.cupThere:
                self.gameStarted = False
                self.output.fieldCenteredOutput("./screens/waiting.txt")

            if not self.pause:
                # CREATE OBJECT
                if self.createObjects:
                    if (self.time + 1) % Game.goodyCreationTime == 0:
                        g = Goody(self)
                        g.setRandomXPos(self.output)
                    if self.time  % Game.obstacleCreationTime == 0:
                        o = Obstacle(self)
                        o.setRandomXPos(self.output)
                self.time += 1

            timeLib.sleep(Game.sleepTime)

        self.end("quit")

    def switchPause(self):
        self.pause = not self.pause

    def full(self):
        self.end("overFull")

    def end(self, status):
        logging.info("Ending game now (status=%s)" % status)
        logging.debug("threads alive: %s" % threading.active_count())
        self.oStatus = status
        self.removeObjects()
        logging.debug("clearing screen")
        screen.clear()
        self.output.printField()
        self.createObjects = False
        if Game.background is not None:
            logging.debug("Game.background.stopLoop()")
            Game.background.stopLoop()
            logging.debug("background sound stopped successfully")
        logging.debug("Ending now, threads alive: %s" % threading.active_count())

    def lifeLost(self):
        logging.info("you lost a life!")
        self.status['lifes'] = self.status['lifes'] - 1
        logging.debug("status=%s" % self.status)
        if self.status['lifes'] == 0:
            self.end("overLifes")
        else:
            self.spaceShip.blink()

    def robotMessage(self, message):
        if message == "bottleEmpty":
            self.pause = True
            self.overlay = "refillBottle"
        elif message == "bottleEmptyResume":
            self.pause = False
            self.overlay = None
        elif message == "cupThere":
            self.cupThere = True
        elif message == "cupNotThere":
            self.cupThere = False


def main(s=None):
    global screen
    screen = s
    screen.nodelay(1)

    ############################################################################
    # Sound Config
    ############################################################################
    soundConfig = SafeConfigParser()
    soundConfig.read('./etc/sound.cfg')

    if soundConfig.getboolean('General', 'enabled'):
        Shoot.soundShooting     = soundLib.Sound(soundConfig.get('Shoot', 'shooting'))
        Shoot.soundCollision    = soundLib.Sound(soundConfig.get('Shoot', 'obstacle'))

        Obstacle.cSpaceship     = soundLib.Sound(soundConfig.get('Spaceship', 'obstacle'))
        Goody.cSpaceship        = soundLib.Sound(soundConfig.get('Spaceship', 'goody'))
        Game.background         = soundLib.Sound(soundConfig.get('General', 'background'))


    ############################################################################
    # Design Config
    ############################################################################
    # default factor == 1
    designConfig = SafeConfigParser({'factor': '1'})
    designConfig.read('./etc/design.cfg')

    # Set obstacles files
    folder = os.path.join(designConfig.get('Obstacles', 'folder'), "")
    for obstacleDesign in glob.glob(folder + "*.txt"):
        Obstacle.obstacles.append(obstacleDesign)

    Obstacle.color      = designConfig.getint('Obstacles', 'color')

    SpaceShip.color     = designConfig.getint('Spaceship', 'color')
    SpaceShip.design    = designConfig.get('Spaceship', 'file')

    folder = os.path.join(designConfig.get('Spaceship', 'folder'), "")
    if folder is not None:
        for spaceshipDesign in glob.glob(folder + "*.txt"):
            #logging.debug("spaceshipDesign %s" % spaceshipDesign)
            SpaceShip.designArray.append(spaceshipDesign)

    ingredientsFolder   = designConfig.get('Ingredients', 'folder')
    for nrGoody in range(1, designConfig.getint('Ingredients', 'count') + 1):
        sectionName = 'Ingredient' + str(nrGoody)
        Goody.types.append({
                "color":    designConfig.getint(sectionName, 'color'),
                "design":   os.path.join(ingredientsFolder, designConfig.get(sectionName, 'file')),
                "name":     designConfig.get(sectionName, 'name'),
                "arduino":  designConfig.getint(sectionName, 'arduino'),
                "factor":   designConfig.getint(sectionName, 'factor'),
                "category": designConfig.get(sectionName, 'category')
        })


    ############################################################################
    # Controller Config
    ############################################################################
    controllerConfig = SafeConfigParser()
    controllerConfig.read('./etc/controller.cfg')
    position = False
    if controllerConfig.get('Controller', 'type') == "keyboard":
        controller = KeyboardController(screen, position)
    else:
        position = controllerConfig.getboolean('UltraSonic', 'position')
        UltraSonicController.mirror =  controllerConfig.getboolean('UltraSonic', 'mirror')
        UltraSonicController.distPos = (controllerConfig.getint('UltraSonic', 'minMovDist'),  controllerConfig.getint('UltraSonic', 'maxMovDist'))
        controller = UltraSonicController(controllerConfig.get('UltraSonic', 'serialPort'),
                                        controllerConfig.get('UltraSonic', 'twoSensors'), screen, position)



    ############################################################################
    # Create Game
    ############################################################################
    o = Output()


    ############################################################################
    # Robot Config
    ############################################################################

    robot = None
    robotConfig = SafeConfigParser()
    robotConfig.read('./etc/robot.cfg')

    Game.sleepTime = float(robotConfig.getint('Game', 'sleepTime'))/100
    Game.obstacleCreationTime = robotConfig.getint('Game', 'obstacleCreationTime')
    Game.goodyCreationTime = robotConfig.getint('Game', 'goodyCreationTime')

    g = Game(controller=controller, output=o)

    Goody.portion = robotConfig.getint('Mixing', 'portion')
    Goody.volume = robotConfig.getint('Mixing', 'volume')
    if robotConfig.getboolean('Robot', 'enabled'):
        robot = BotComm(robotConfig.get('Robot', 'serialPort'), g.robotMessage)

    g.robot = robot

    #g.prepare()
    try:
        g.run()
    except Exception, e:
        raise e
    finally:
        # Cleaning Up
        if soundConfig.getboolean('General', 'enabled'):
            Shoot.soundShooting.close()
            Shoot.soundCollision.close()
            Obstacle.cSpaceship.close()
            Goody.cSpaceship.close()
            Game.background.close()

        if robot is not None:
            robot.close()


        controller.close()

        screen.refresh()
    






#main()
curses.wrapper(main)
