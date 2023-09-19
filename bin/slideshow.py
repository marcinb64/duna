import sys
import os
import time
import threading
import logging


logger = logging.getLogger('slideshow')


class Slideshow():
    def __init__(self, viewer):
        self.viewer = viewer
        self.images = []
        self.currentImage = 0
        self.lock = threading.Lock()
        self.changeListeners = []


    def add(self, images):
        with self.lock:
            if hasattr(images, '__iter__') and type(images) is not str:
                self.images.extend(images)
            else:
                self.images.append(images)

            self.notifyAboutChange()


    def clear(self):
        with self.lock:
            self.images.clear()
            self.notifyAboutChange()


    def nextImage(self):
        with self.lock:
            if len(self.images) == 0: return
            self.currentImage = (self.currentImage + 1) % len(self.images)
            self.showCurrent()


    def prevImage(self):
        with self.lock:
            if len(self.images) == 0: return
            self.currentImage = (self.currentImage - 1) % len(self.images)
            self.showCurrent()


    def showCurrent(self):
            img = self.images[self.currentImage]
            logger.info("Show %s", img)
            self.viewer.show(img)


    def getLength(self):
        with self.lock:
            return len(self.images)


    def addListener(self, listener):
        self.changeListeners.append(listener)


    def notifyAboutChange(self):
        for i in self.changeListeners:
            i()


class SlideshowChannels():
    def __init__(self):
        self.channels = []
        self.currentChannel = 0
        self.sequenceCounter = 0


    def add(self, slideshow, sequenceLimit=None):
        self.channels.append((slideshow, sequenceLimit))
        if len(self.channels) == 1:
            self.nextChannel()


    def nextImage(self):
        if len(self.channels) == 0: return

        self.channels[self.currentChannel][0].nextImage()
        self.sequenceCounter += 1

        slideshow, sequenceLimit = self.channels[self.currentChannel]
        limit = min(sequenceLimit or slideshow.getLength(), slideshow.getLength())
        if self.sequenceCounter >= limit:
            self.nextChannel()


    def prevImage(self):
        if len(self.channels) == 0: return

        self.channels[self.currentChannel][0].prevImage()
        self.sequenceCounter -= 1

        if self.sequenceCounter <= 0:
            self.prevChannel()



    def nextChannel(self):
        self.currentChannel = (self.currentChannel + 1) % len(self.channels)
        self.sequenceCounter = 0


    def prevChannel(self):
        self.currentChannel = (self.currentChannel - 1) % len(self.channels)
        slideshow, sequenceLimit = self.channels[self.currentChannel]
        self.sequenceCounter = min(sequenceLimit or slideshow.getLength(), slideshow.getLength())


    def getLength(self):
        return sum(map(lambda i:len(i), self.channels))


def listImages(imageDir):
    if imageDir is None: return
    dirPath = os.path.abspath(os.path.expanduser(imageDir))
    return map(lambda i:"file://" + i,
               map(lambda i:os.path.join(dirPath, i),
                   filter(isImageFile, os.listdir(dirPath))))


def isImageFile(fileName):
    n = fileName.lower()
    return n.endswith('.jpg') or n.endswith('.jpeg') or n.endswith('.png')


# ------------------------------------------------------------------------------


def slideshowMain(slideshow):
    while(True):
        slideshow.nextImage()
        time.sleep(5)


def buildSlideshowFromDirs(dirs):
    slideshow = SlideshowChannels()
    for i in dirs:
        w = Slideshow(viewer)
        w.add(list(listImages(i)))
        slideshow.add(w)

    return slideshow


def main(argv):
    import qtviews
    qtviews.init(sys.argv)

    if len(argv) < 2:
        print("Usage:", argv[0], " <img dir> [<img dir 2> ... <img dir N>]")
        return 0

    viewer = qtviews.WebViewer("Duna Screen v0.2")
    slideshow = buildSlideshowFromDirs(argv[1:])

    threading.Thread(target=slideshowMain, args=(slideshow,)).start()
    qtviews.main()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
