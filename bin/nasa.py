import requests


def getFileName(url):
    return url.split('/')[-1]


def makeApi(apiKey, name):
    if name == CuriosityApi.ROVER:
        return CuriosityApi(apiKey)
    elif name == PerseveramceApi.ROVER:
        return PerseveramceApi(apiKey)
    elif name.lower() == "APOD":
        return ApodApi(apiKey)
    else:
        raise KeyError("Unknown API: " + str(name))


# ------------------------------------------------------------------------------


class NasaApi:
    BASE_URL = "https://api.nasa.gov"

    def __init__(self, apiKey):
        self.apiKey = apiKey


    def buildUrl(self, path):
        return self.BASE_URL + path + '?api_key=' + self.apiKey


    def get(self, url):
        ''' Perform a GET request to the specified URL
        and return the response as JSON or raise an exception
        in case of failure.
        '''
        response = requests.get(url)
        response.raise_for_status()
        return response.json()


# ------------------------------------------------------------------------------


class ApodApi(NasaApi):
    ''' Astronomy Picture Of the Day Endpoint '''

    PATH = "/planetary/apod"

    def __init__(self, apiKey):
        super().__init__(apiKey)


    def getLatestImage(self):
        ''' Return the URL of the latest APOD image '''
        url = self.buildUrl(self.PATH)
        r = self.get(url)
        return  (r["media_type"], r["url"])


# ------------------------------------------------------------------------------


class RoverApi(NasaApi):
    ''' Rover Images Endpoint '''

    def __init__(self, apiKey, rover):
        super().__init__(apiKey)
        self.manifestUrl = self.buildUrl("/mars-photos/api/v1/rovers/" + rover)
        self.imagesUrl = self.buildUrl("/mars-photos/api/v1/rovers/" + rover + "/photos")


    def getLastSol(self):
        ''' Return the latest available sol numer '''
        return int(self.get(self.manifestUrl)["rover"]["max_sol"])


    def listCameras(self, sol):
        ''' Return a list of cameras that provided images at given sol '''
        manifest = self.get(self.manifestUrl)
        solManifest = self.findSolManifest(manifest, sol)
        if solManifest:
            return solManifest["cameras"]
        else:
            return None


    def findSolManifest(self, manifest, sol):
        for i in manifest["photo_manifest"]["photos"]:
            if i["sol"] == sol:
                return i
        return None


    def listImages(self, sol, camera=None):
        ''' Return a list of URLs to images from given camera at given sol '''
        url = self.imagesUrl + "&sol=" + str(sol)
        if camera:
            url += "&camera=" + camera
        response = self.get(url)
        return map(lambda i: (i["img_src"], i["camera"]["name"]), response["photos"])


    def wantImage(self, url):
        ''' Determine if given image URL should be downloaded for sync.
        Derived classes may optionally filter out some images.
        By default, accepts all URLs. '''
        return True


    def getFullresImg(self, url):
        ''' In some cases, the image reported by the REST API is a scaled-down image.
        Full resolution image can be downloaded at a different URL. Derived classes
        may transform the URL to determin the full-res URL.
        By default returns the input URL.
        '''
        return url


# ------------------------------------------------------------------------------


class CuriosityApi(RoverApi):
    ROVER = "curiosity"
    DEFAULT_CAMERA = "NAVCAM"
    NAVCAM = "NAVCAM"
    MASTCAM = "MAST"

    def __init__(self, apiKey):
        super().__init__(apiKey, "curiosity")


    def wantImage(self, img):
        name = getFileName(img[0])
        cat = name[22:25]
        # Cxx and Exx images from mastcam seem to be the most interesting
        return (cat[0] == "C" or cat[0] == "E") or \
            'NCAM' in name


# ------------------------------------------------------------------------------


class PerseveramceApi(RoverApi):
    ROVER = "perseverance"
    DEFAULT_CAMERA = "MCZ_LEFT"
    NAVCAM_L = "NAVCAM_LEFT"
    NAVCAM_R = "NAVCAM_RIGHT"
    MASTCAM_L = "MCZ_LEFT"
    MASTCAM_R = "MCZ_RIGHT"

    def __init__(self, apiKey):
        super().__init__(apiKey, "perseverance")


    def wantImage(self, img):
        name = getFileName(img[0])
        # "EBY" seem to be the most interesting
        # 3rd char is the filter. 0 and 7 is no filter.
        return ('EBY' in name) \
            and (name[2] == '0' or name[2] == '7') \
            and ('CAM01000' not in name)


    def getFullresImg(self, url):
        # Higher resolution images can be obtained by cutting the _1200 suffix
        # and replacing jpg with png
        return url.replace('_1200.jpg', '.png')
