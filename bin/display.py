import sync
import slideshow
import sched
import qtviews
import logging

logger = logging.getLogger("display")

class DisplayOutput():
    def __init__(self, title, interval, updateInterval, firstUpdateDelay):
        qtviews.init([])
        self.channels = []
        self.root = slideshow.SlideshowChannels()
        self.viewer = qtviews.UniversalViewer(title)
        self.scheduler = sched.Scheduler()

        self.scheduler.runPeriodically(interval, self.nextImage)
        self.scheduler.runPeriodically(updateInterval, self.update)
        self.scheduler.runAfter(firstUpdateDelay, self.update)


    def addRover(self, api, camera, sequenceLimit):
        ch = RoverDisplayChannel(self.viewer, api, camera)
        self.channels.append(ch)
        self.root.add(ch.slideshow, sequenceLimit)


    def addStatic(self, urls, updates, sequenceLimit):
        ch = StaticDisplayChannel(self.viewer, urls, updates)
        self.channels.append(ch)
        self.root.add(ch.slideshow, sequenceLimit)


    def update(self):
        for i in self.channels:
            logger.info("Update %s", i)
            try:
                i.update()
            except Exception:
                logger.exception("Error updating %s", i)


    def getSlideshow(self):
        return self.root


    def nextImage(self):
        self.root.nextImage()


    def run(self):
        self.nextImage()
        qtviews.main()
        self.scheduler.kill()


    def kill(self):
        self.scheduler.kill()
        qtviews.exit()


# ------------------------------------------------------------------------------


class RoverDisplayChannel():
    def __init__(self, viewer, api, camera):
        self.api = api
        self.slideshow = slideshow.Slideshow(viewer)
        self.camera = camera

        for i in [ sync.RoverCameraSync, sync.RoverHazcamSync ]:
            tmp = i.listLatestImages(api)
            if tmp: self.slideshow.add(tmp)


    def update(self):
        newFiles = []
        actions = [
            sync.RoverCameraSync(self.api, sol=None, camera=self.camera),
            sync.RoverHazcamSync(self.api, sol=None),
        ]

        for i in actions:
            newFiles.extend(i.sync() or [])

        logger.debug("New files after sync: %d", len(newFiles))

        if len(newFiles) > 0:
            self.slideshow.clear()
            self.slideshow.add(newFiles)


    def __str__(self):
        return self.api.ROVER + " channel"


# ------------------------------------------------------------------------------


class StaticDisplayChannel:
    def __init__(self, viewer, urls, updates):
        self.slideshow = slideshow.Slideshow(viewer)
        self.slideshow.add(urls)
        self.updates = updates


    def update(self):
        for i in self.updates:
            i.sync()

    def __str__(self):
        return "Slideshow channel"
