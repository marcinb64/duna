#!/usr/bin/env python3

import nasa
import sync
import display

import json
import os
import sys
import getopt
import time
import signal
import functools
import re
import logging

# ------------------------------------------------------------------------------

VER = "0.2"


LOG_LEVELS = {
    "main": logging.DEBUG,
    "sync": logging.DEBUG,
    "display": logging.DEBUG,
    "slideshow": logging.DEBUG,
    "panel": logging.DEBUG,
    "QT": logging.DEBUG,
}

logger = logging.getLogger('main')

# ------------------------------------------------------------------------------

def minutes(m):
    return m * 60

def hours(h):
    return h * 60 * 60

def days(d):
    return d * 24 * 60 * 60

SECONDS_IN = {
    's': 1,
    'm': minutes(1),
    'h': hours(1),
    'd': days(1),
}

def parseTimeSpec(spec):
    # if it's just a number, treat it as seconds
    try: return int(spec)
    except ValueError: t = 0

    # Look for days (d), hours (h), minutes (m) and seconds (s)
    # Ex: "1d 2h 3m 4s"
    for i in re.findall('[0-9]+[ ]*[hmsd]', spec):
        number = int(re.findall('[0-9]+', i)[0])
        unit = i[-1]
        t += number * SECONDS_IN[unit]
    return t

# ------------------------------------------------------------------------------

def displayOutputFactory(cfg):
    interval = parseTimeSpec(cfg.get("interval") or "1m")
    updateInterval = parseTimeSpec(cfg.get("updateInterval") or "6h")
    firstUpdateDelay = parseTimeSpec(cfg.get("firstUpdateDelay") or "30s")

    return display.DisplayOutput(
        "Duna Screen v" + VER,
        interval, updateInterval, firstUpdateDelay)

def filesOutputFactory(config):
    import filesout
    baseDir = config["baseDir"]
    return filesout.FilesOutput(baseDir)


outputFactories = {
    "display": displayOutputFactory,
    "files": filesOutputFactory,
}


# ------------------------------------------------------------------------------


def staticChannelFactory(node, globalConfig, output):
    updaterFactory = lambda i: makeUpdater(i, globalConfig)

    sequenceLimit = node.get("sequenceLimit")
    urls = node["urls"]
    updates = map(updaterFactory, node["updates"])

    output.addStatic(urls, list(updates), sequenceLimit)


def makeUpdater(name, globalConfig):
    if name.upper() == 'APOD':
        apiKey = globalConfig["apiKey"]
        return sync.ApodSync(nasa.ApodApi(apiKey), "slideshow")
    else:
        logger.error("Unknown update source: %s", name)
        return None


def roverChannelFactory(node, globalConfig, output):
    apiKey = globalConfig["apiKey"]
    sequenceLimit = node.get("sequenceLimit")
    api = nasa.makeApi(apiKey, validateRoverName(node["name"]))
    camera = node["camera"]

    output.addRover(api, camera, sequenceLimit)


def validateRoverName(name):
    valid = functools.reduce(lambda a,b: a and b.isalnum(), name, True)
    if not valid: raise ValueError("Invalid rover name: " + str(name))
    return name.lower()


channelFactories = {
    "static": staticChannelFactory,
    "rover": roverChannelFactory,
}


# ------------------------------------------------------------------------------


class App():
    def __init__(self, config, outputFactories, channelFactories):
        self.outputFactories = outputFactories
        self.channelFactories = channelFactories

        self.output = self.buildOutputFromConfig(config)
        self.buildChannelsFromConfig(config)
        self.controlPanel = self.buildControlPanel(config)


    def buildOutputFromConfig(self, config):
        k = list(config["output"].keys())[0]
        logger.info("Configuring output: " + k)
        factory = self.outputFactories[k]
        return factory(config["output"][k])


    def buildChannelsFromConfig(self, config):
        for i in config["channels"]:
            k = list(i.keys())[0]
            logger.info("Adding channel: " + k)
            factory = self.channelFactories[k]
            factory(i[k], config, self.output)


    def buildControlPanel(self, config):
        slideshow = self.output.getSlideshow()
        panelConfig = config.get("controllers")
        if (slideshow is None) or (panelConfig is None): return

        import control_panel
        pins = panelConfig["grayRotary"]["pins"]
        sequence = panelConfig["grayRotary"]["sequence"]
        rotary = control_panel.Rotary(pins, sequence)
        return control_panel.ControlPanel(slideshow, rotary)


    def onSignal(self, sig, frame):
        logger.info("Received signal %d", sig)
        if sig == signal.SIGUSR1:
            self.output.getSlideshow().nextImage()
        elif sig == signal.SIGUSR2:
            self.output.getSlideshow().prevImage()
        else:
            self.output.kill()


    def main(self):
        logger.debug("enter App.main()")
        self.output.run()
        logger.debug("exit App.main()")



# ------------------------------------------------------------------------------

def main(argv):
    setupLogging()
    sync.setup()

    configFile, = parseCommandLine(argv)
    config = json.load(open(configFile or 'duna.json'))
    app = App(config, outputFactories, channelFactories)

    setupSignalHandler(app)
    app.main()


def setupLogging():
    logging.basicConfig(format="%(asctime)s [%(name)-10s] %(levelname)-7s %(message)s",
                        level=logging.ERROR, datefmt="%Y-%m-%d %H:%M:%S")
    for (n, l) in LOG_LEVELS.items():
        logging.getLogger(n).setLevel(l)


def parseCommandLine(argv):
    try:
        opts, args = getopt.getopt(argv[1:], "hc:",
                                   ["help", "config="])
    except getopt.GetoptError as e:
        logger.exception("Parse command line", e)
        sys.exit(1)

    configFile = None
    for o, a in opts:
        if o in ("-h", "--help"):
            printUsage()
            sys.exit()
        elif o in ("-c", "--config"):
            configFile = a
        else:
            assert False, "unhandled option"

    return (configFile, )


def printUsage():
    print("Usage:", sys.argv[0],"[--help] [--config=<config file>]")


def setupSignalHandler(app):
    signal.signal(signal.SIGINT, app.onSignal)
    signal.signal(signal.SIGTERM, app.onSignal)
    signal.signal(signal.SIGUSR1, app.onSignal)
    signal.signal(signal.SIGUSR1, app.onSignal)


if __name__ == '__main__':
    main(sys.argv)
