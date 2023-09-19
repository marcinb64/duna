import wget
import time
import os
import re
import PIL.Image as Image
import tempfile
import shutil
import logging


logger = logging.getLogger("sync")

# ------------------------------------------------------------------------------

def getFileName(url):
    return url.split('/')[-1]

def mkdir(path):
    if not os.path.isdir(path): os.makedirs(path)

def isImageFile(fileName):
    n = fileName.lower()
    return n.endswith('.jpg') or n.endswith('.jpeg') or n.endswith('.png')

def setup():
    mkdir("rovers")
    mkdir("slideshow")

# ------------------------------------------------------------------------------

class RoverSync:
    def __init__(self, api, baseDir, sol=None):
        self.api = api
        self.rover = api.ROVER
        self.sol = self.determineSol(sol)
        self.syncDir = baseDir + '-' + str(self.sol)
        self.captionsDir = self.syncDir + "/captions"
        mkdir(baseDir)

    def determineSol(self, requested):
        if (requested is None):
            s = self.api.getLastSol()
            logger.debug('Latest sol for %s is %d', self.rover, s)
            return s
        else:
            return requested


    def alreadySynced(self):
        return os.path.isdir(self.syncDir)


    def filterImages(self, allImages, camera):
        return filter(lambda i: camera.upper() == i[1].upper(), allImages)


    def downloadImage(self, url, outDir):
        try:
            fullResUrl = self.api.getFullresImg(url)
            logger.debug("Downloading %s", fullResUrl)
            n = wget.download(fullResUrl, outDir, bar=None)
            return n
        except:
            logger.debug("Downloading %s", url)
            n = wget.download(url, outDir, bar=None)
            return n



class RoverCameraSync(RoverSync):
    ''' Sync images from a rover captured at a specific sol '''

    def listLatestImages(api):
        r = re.compile(api.ROVER + '-[0-9]+$')
        tmp = list(sorted(filter(r.match, os.listdir("rovers"))))
        if len(tmp) == 0: return None

        d = os.path.join("rovers", tmp[-1])
        return map(lambda i:os.path.join(d, i),
                   filter(isImageFile, os.listdir(d)))


    def __init__(self, api, sol=None, camera=None):
        ''' RoverCameraSync(api, sol)
        api - API key
        sol - sol number, or None None, to use the latest
        camera - specific camera, or None to use default
        '''
        super().__init__(api, 'rovers/' + api.ROVER, sol)
        self.camera = camera or api.DEFAULT_CAMERA


    def sync(self):
        if self.alreadySynced(): return None

        images = self.api.listImages(self.sol, self.camera)
        selected = list(filter(self.api.wantImage, images))

        if len(selected) == 0: return None

        mkdir(self.syncDir)
        mkdir(self.captionsDir)

        outFiles = []
        for i,c in selected:
            try:
                actual = self.downloadImage(i, self.syncDir)
                outFiles.append(actual)
            except Exception as e:
                logger.exception('Failed to download %s', i)

        return outFiles


class RoverHazcamSync(RoverSync):
    ''' Sync hazcam images from a rover captured at a specific sol.
    Creates a composite image from front/rear left/right HAZCAM images.
    '''

    def listLatestImages(api):
        r = re.compile(api.ROVER + '-haz-[0-9]+$')
        tmp = list(sorted(filter(r.match, os.listdir("rovers"))))
        if len(tmp) > 0:
            return os.path.join("rovers", tmp[-1], "dash-" + api.ROVER + ".png")
        else:
            return None


    def __init__(self, api, sol):
        ''' RoverHazcamSync(api, sol)
        api - API key
        sol - sol number; if None, will use the latest available sol
        '''
        super().__init__(api, 'rovers/' + api.ROVER + '-haz', sol)


    def sync(self):
        if self.alreadySynced(): return None

        allImages = list(self.api.listImages(self.sol))
        hazImages = {
            "FRONT_HAZCAM_LEFT_A": None,
            "FRONT_HAZCAM_RIGHT_A": None,
            "REAR_HAZCAM_LEFT": None,
            "REAR_HAZCAM_RIGHT": None,
        }
        coords = {
            "FRONT_HAZCAM_LEFT_A": (0, 0),
            "FRONT_HAZCAM_RIGHT_A": (1280, 0),
            "REAR_HAZCAM_LEFT": (0, 960),
            "REAR_HAZCAM_RIGHT": (1280, 960),
        }

        n = 0
        for i in hazImages.keys():
            sel = list(self.filterImages(allImages, i))
            if len(sel) > 0:
                sel.sort(key=lambda i:i[0])
                hazImages[i] = sel[-1][0]
                n += 1

        logger.debug("HAZ images (%d): %s", n, hazImages)
        if (n > 0):
            mkdir(self.syncDir)

            dash = Image.new("RGB", (1280*2, 960*2))
            for k,i in hazImages.items():
                if i:
                    filename = self.downloadImage(i, self.syncDir)
                    img = Image.open(filename)
                    dash.paste(img, coords[k])

            logger.debug("Saving HAZ dashboard image")
            dashImg = os.path.join(self.syncDir,  "dash-" + self.api.ROVER + ".png")
            if os.path.exists(dashImg): os.unlink(dashImg)
            dash.save(dashImg)
            return [ dashImg ]
        else:
            return None


# ------------------------------------------------------------------------------


class ApodSync:
    def __init__(self, api, outputDir):
        self.api = api
        self.outputFile = os.path.join(outputDir, "nasa-apod.jpg")


    def sync(self):
        mediaType, url = self.api.getLatestImage()
        logger.info("Latest APOD is %s : %s", mediaType, url)
        if not self.accepts(mediaType): return None

        logger.debug("Downloading %s", url)
        tmp = wget.download(url, tempfile.gettempdir(), bar=None)

        if os.path.getsize(tmp) > 0:
            logger.debug("Downloaded APOD")
            shutil.move(tmp, self.outputFile)
            return self.outputFile
        else:
            logger.warning("Failed to download APOD: %s", url)
            os.unlink(tmp)

        return None


    def accepts(self, mediaType):
        return mediaType == "image"


# ------------------------------------------------------------------------------
