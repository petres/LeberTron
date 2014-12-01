#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import logging
import curses
import locale
import random
import os
import glob
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

import sound as soundLib
from botComm import BotComm

inp = None

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
        self.game = game
        self.coords = coords
        self.signs  = signs
        self.color  = color
        self.startTime = game.time
        self.signsArray = signsArray
        self.switchSignsTime = switchSignsTime

        if speed is None:
            self.speed = random.randint(
                Object.stdSpeed / 2, Object.stdSpeed * 2)
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
    diffBetween     = 20
    def __init__(self, game, **args):
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
    portion     = 10
    volume      = 100

    def collision(self):
        if Goody.cSpaceship is not None:
            Goody.cSpaceship.play()
        self.game.status['count'] += 1
        self.game.status['ml']    += Goody.portion
        self.game.status['goodies'].append(self.name)
        if self.game.robot is not None:
            self.game.robot.pourBottle(self.arduino, Goody.portion)
        if self.game.status['ml'] > Goody.volume:
            self.game.full()

    def __init__(self, game, **args):
        if "signs" not in args:
            i = random.randint(0, len(Goody.types) - 1)
            args["signs"] = getFromFile(Goody.types[i]["design"])
            args["color"] = Goody.types[i]["color"]
            self.name = Goody.types[i]["name"]
            self.arduino  = Goody.types[i]["arduino"]
        super(Goody, self).__init__(game, **args)


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
                    self.color = self.orgColor
                    self.blinkColor = self.orgBlinkColor
                    self.blinking = False
                else:
                    tmp = self.color
                    self.color = self.blinkColor
                    self.blinkColor = tmp
            self.blinkTime += 1
        return

    def blink(self):
        self.orgColor = self.color
        self.orgBlinkColor = self.blinkColor
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

        y, x = screen.getmaxyx()
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
        for i in range(self.fieldPos[0] - 1, self.fieldPos[0] + self.fieldSize[0] + 2):
            self.addSign((i, self.fieldPos[1] - 1), u"█")
            self.addSign((i, self.fieldPos[1] + self.fieldSize[1] + 1), u"█")

        for i in range(self.fieldPos[1] - 1, self.fieldPos[1] + self.fieldSize[1] + 2):
            self.addSign((self.fieldPos[0] - 1, i), u"█", color=None)
            self.addSign((self.fieldPos[0] + self.fieldSize[0] + 1, i), u"█")

    def clearField(self, pos, size, sign=" "):
        for i in range(pos[1], pos[1] + size[1] + 1):
            self.addSign((pos[0], i), sign * (size[0] + 1))

    def printStatus(self, game):
        x, y = self.statusPos
        x = x + 3
        self.addSign((x, 1), "Sensor:")
        if inp is not None:
            self.addSign((x, 2), "cm slid: " + str(round(inp.curr)))
            self.addSign((x, 3), "cm now:  " + str(round(inp.currA)))
            self.addSign((x, 4), "shoot:   " + str(round(inp.shoot)))
            self.addSign((x, 5), "shoot d: " + str(round(inp.shootDist)))

        self.addSign((x, 9), " Lifes")
        for i, line in enumerate(getFromFile("./objects/lifes/" + str(game.status['lifes']) + ".txt")):
            self.addSign((x, 10 + i), line)

        x += 13

        self.addSign((x, 9), " Count")
        for i, line in enumerate(getFromFile("./objects/lifes/" + str(game.status['count']) + ".txt")):
            self.addSign((x, 10 + i), line)
        # self.addSign((x,10), "count:  " + str(game.status['count']))
        # self.addSign((x,11), "lifes:   " + str(game.status['lifes']))
        # self.addSign((x,12), "time:    " + str(game.time))
        # self.addSign((x,13), "objects: " + str(len(Object.objects)))

        # self.printGlass(x, 12, game.status["goodies"])

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

    def __init__(self, screen, position):
        self.screen = screen
        self.position = position

    def getInput(self):
        # raise NotImplementedError
        c = self.screen.getch()
        return None


class UltraSonicController(Controller):

    def __init__(self, serialPort, screen, position=False):
        import inputComm as ultraSonicInput
        global inp
        inp = ultraSonicInput
        self.distPos    = (30, 80)
        inp.connect(serialPort)
        inp.start()
        super(UltraSonicController, self).__init__(screen, position)

    def getInput(self):
        c = self.screen.getch()

        if c == ord('q'):
            return Controller.QUIT
        elif c == ord('r'):
            return Controller.RETRY

        if inp.shoot:
            return Controller.SHOOT

        if self.position:
            return float(inp.curr - self.distPos[0]) / (self.distPos[1] - self.distPos[0])

        if inp.state == -1:
            return Controller.LEFT
        elif inp.state == 1:
            return Controller.RIGHT

        return None

    def close(self):
        inp.exitFlag = 1
    # def getPosition(self):
    #     float(inp.curr - self.distPos[0])/(self.distPos[1] - self.distPos[0])


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

    def __init__(self, controller, output, robot=None):
        self.time = 0
        self.controller = controller
        self.output     = output
        self.robot      = robot
        self.spaceShip = SpaceShip(self)
        self.spaceShip.coords = (
            self.output.fieldSize[0] / 2, self.output.fieldSize[1] - 2)
        self.countdown = 0

        self.status = {}
        self.setStartStatus()
        self.overlay = None

    def removeObjects(self):
        logging.debug("removing objects")
        for o in list(Object.objects):
            if not isinstance(o, SpaceShip):
                Object.objects.remove(o)

    def setStartStatus(self):
        self.status['count']   = 0
        self.status['goodies'] = []
        self.status['lifes']   = 3
        self.status['ml']      = 0


    def prepare(self):
        self.time   = 0
        self.setStartStatus()
        self.output.prepareGame()
        self.countdown = 3
        self.overlay = None
        Shoot.lastStartTime = 0
        if Game.background is not None:
            Game.background.loop()

    def run(self):
        logging.info('Starting main loop...')
        while True:
            logging.debug("time=%d" % self.time)
            d = self.controller.getInput()

            if d == Controller.QUIT:
                break
            elif d == Controller.SHOOT:
                o = Shoot(self, coords = (self.spaceShip.coords[0], self.spaceShip.coords[1] - self.spaceShip.info['rHeight'] - 1))

            if d == Controller.RETRY:
                self.prepare()

            if self.controller.position == False:
                m = 0
                if d == Controller.LEFT:
                    m = -1
                elif d == Controller.RIGHT:
                    m = 1

                x = self.spaceShip.coords[0]
                x += m * self.moveStepSize
            else:
                x = int(d*self.output.fieldSize[0])

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

            if self.overlay is not None:
                if self.overlay == "overLifes":
                    self.output.fieldCenteredOutput("./screens/full.txt")
                elif self.overlay == "overFull":
                    self.output.fieldCenteredOutput("./screens/full.txt")

            # CREATE OBJECT
            if self.createObjects:
                if self.time % 60 == 0:
                    g = Goody(self)
                    g.setRandomXPos(self.output)
                if self.time % 40 == 0:
                    o = Obstacle(self)
                    o.setRandomXPos(self.output)
                    #pass

            self.time += 1
            timeLib.sleep(.03)

        self.end("quit")

    def full(self):
        self.end("overFull")

    def end(self, status):
        logging.info("Ending game now (status=%s)" % status)
        self.overlay = status
        self.removeObjects()
        logging.debug("clearing screen")
        screen.clear()
        self.output.printField()
        self.createObjects = False
        if Game.background is not None:
            logging.debug("Game.background.stopLoop()")
            Game.background.stopLoop()

    def lifeLost(self):
        self.status['lifes'] = self.status['lifes'] - 1
        #curses.init_pair(self.spaceShip.color, 3, -1)
        self.removeObjects()
        if self.status['lifes'] == 0:
            self.end("overLifes")
        else:
            self.spaceShip.blink()

    def robotMessage(self, *bla):
        pass


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
    designConfig = SafeConfigParser()
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
                "arduino":  designConfig.getint(sectionName, 'arduino')
        })


    ############################################################################
    # Controller Config
    ############################################################################
    controllerConfig = SafeConfigParser()
    controllerConfig.read('./etc/controller.cfg')
    position = False
    if controllerConfig.get('Controller', 'type') == "keyboard":
        c = KeyboardController(screen, position)
    else:
        position = controllerConfig.getboolean('UltraSonic', 'position')
        c = UltraSonicController(controllerConfig.get('UltraSonic', 'serialPort'), screen, position)



    ############################################################################
    # Create Game
    ############################################################################
    o = Output()


    ############################################################################
    # Robot Config
    ############################################################################

    g = Game(controller = c, output = o)

    robot = None
    robotConfig = SafeConfigParser()
    robotConfig.read('./etc/robot.cfg')
    Goody.portion = robotConfig.getint('Mixing', 'portion')
    Goody.volume = robotConfig.getint('Mixing', 'volume')
    if robotConfig.getboolean('Robot', 'enabled'):
        robot = BotComm(robotConfig.get('Robot', 'serialPort'), g.robotMessage)

    g.robot = robot

    #g.prepare()
    g.run()

    if robot is not None:
        robot.close()
    # Cleaning Up
    if isinstance(c, UltraSonicController):
        c.close()
        timeLib.sleep(0.3)

    screen.refresh()


#main()
curses.wrapper(main)
