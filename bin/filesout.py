import sync

import psutil
import signal

class FilesOutput:
    def __init__(self, baseDir):
        self.baseDir = baseDir
        self.channels = []
        self.slideshow = FehSlideshow()


    def addRover(self, api, camera, sequenceLimit):
        self.updaters.append(sync.RoverCameraSync(api, sol=None, camera=camera))
        self.updaters.append(sync.RoverHazcamSync(self.api, sol=None))


    def addStatic(self, urls, updates, sequenceLimit):
        self.updaters.extend(updates)


    def update(self):
        pass


    def getSlideshow(self):
        return self.slideshow

# ------------------------------------------------------------------------------

class FehSlideshow:
    ''' Interface to the slideshow process '''

    def nextImage(self):
        p = self.findSlideshowProcess()
        if p: p.send_signal(signal.SIGUSR1)

    def prevImage(self):
        p = self.findSlideshowProcess()
        if p: p.send_signal(signal.SIGUSR2)

    def findSlideshowProcess(self):
        l = list(filter(lambda i:i.name() == "feh", psutil.process_iter()))
        if len(l) > 0:
            return l[0]
        else:
            return None
