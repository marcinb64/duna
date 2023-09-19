#!/usr/bin/env python3

import nasa
import sync

import os
import sys
import getopt

# ------------------------------------------------------------------------------

class SlideshowRoverSync(sync.SyncRoverAction):
    def __init__(self, api, camera, sol, keepDirs=1):
        super().__init__(api, camera, sol)
        self.keepDirs = keepDirs


    def run(self):
        syncedSol = super().run()
        if syncedSol:
            self.makeLinkInSlideshowDir(self.api.ROVER, syncedSol)
            self.removeOldSolsFromSlideshowDir(self.api.ROVER, self.keepDirs)


    def makeLinkInSlideshowDir(self, rover, sol):
        syncDir = rover + '-' + str(sol)
        target = 'slideshow/' + syncDir
        if os.path.exists(target): os.unlink(target)
        os.symlink('../rovers/' + syncDir, target)


    def removeOldSolsFromSlideshowDir(self, rover, keepDirs):
        d = os.listdir('slideshow')
        d = filter(lambda i: (rover + '-') in i, d)
        d = list(sorted(d))

        for i in d[:-keepDirs]:
            os.unlink('slideshow/' + i)


# ------------------------------------------------------------------------------


DEFAULT_ACTIONS = [ "apod", "curiosity", "perseverance", "haz" ]

def main(argv):
    actions = parseCommandLine(argv)
    runActions(actions)


def printUsage():
    print("Usage:", sys.argv[0], "--apikey=<key>")


def parseCommandLine(argv):
    try:
        opts, args = getopt.getopt(argv[1:], "hs:c:k:",
                                   ["help", "sol=", "camera=", "apikey="])
    except getopt.GetoptError as e:
        print(e)
        sys.exit(1)

    sol = None
    camera = None
    apiKey = None
    actions = []
    for o, a in opts:
        if o in ("-h", "--help"):
            printUsage()
            sys.exit()
        elif o in ("-s", "--sol"):
            sol = int(a)
        elif o in ("-c", "--camera"):
            camera = a
        elif o in ("-k", "--apikey"):
            apiKey = a
        else:
            assert False, "unhandled option"

    if apiKey is None or apiKey == "":
        print("Missing api key")
        sys.exit(1)

    if len(args) == 0:
        args = DEFAULT_ACTIONS

    for i in args:
        a = makeAction(i, apiKey, camera, sol)
        if a: actions.append(a)

    return actions


def makeAction(key, apiKey, camera, sol):
    if "apod".startswith(key):
        return sync.ApodAction(nasa.ApodApi(apiKey), "slideshow/nasa-apod.jpg")
    elif "perseverance".startswith(key):
        return SlideshowRoverSync(nasa.PerseveramceApi(apiKey), camera, sol)
    elif "curiosity".startswith(key):
        return SlideshowRoverSync(nasa.CuriosityApi(apiKey), camera, sol)
    elif "haz".startswith(key):
        return sync.SyncHazAction(nasa.PerseveramceApi(apiKey), sol)
    else:
        print("Unknown action: " + i)


def runActions(actions):
    for a in actions:
        print(str(a))
        a.run()


if __name__ == '__main__':
    main(sys.argv)
