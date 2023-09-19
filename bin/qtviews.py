from PyQt5 import QtWidgets, QtGui, QtCore

try:
    from PyQt5.QtWebEngineWidgets import *
    QWebView = QWebEngineView
except ModuleNotFoundError:
    from PyQt5.QtWebKitWidgets import *

import logging

# ------------------------------------------------------------------------------

logger = logging.getLogger("QT")

activeView = None

class Signal(QtCore.QObject):
    sig = QtCore.pyqtSignal(str)

    def __init__(self, actual):
        super().__init__()
        self.sig.connect(actual)

    def __call__(self, arg):
        self.sig.emit(arg)


class ImageViewer():
    def __init__(self, title):
        self.width = screenGeometry.width()
        self.height = screenGeometry.height()
        self.label = QtWidgets.QLabel()
        self.label.setWindowTitle(title)
        self.label.setStyleSheet("background-color: black")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setCursor(QtCore.Qt.BlankCursor)

        self.loadSignal = Signal(self.actuallyShow)

    def show(self, url):
        logger.debug("ImageViewer show " + str(url))
        self.loadSignal(url)

    def actuallyShow(self, imagePath):
        self.makeVisible()
        p = imagePath.replace('file://', '')
        logger.debug("ImageViewer load " + p)
        pixmap = QtGui.QPixmap(p)
        pixmap = pixmap.scaled(self.width, self.height, QtCore.Qt.KeepAspectRatio)
        self.label.setPixmap(pixmap)

    def makeVisible(self):
        global activeView
        if activeView is self: return
        logger.debug("Switching viewer to ImageViewer")
        if activeView: activeView.hide()
        if not self.label.isVisible(): self.label.showFullScreen()
        activeView = self

    def hide(self):
        self.label.hide()


class WebViewer():
    def __init__(self, title):
        self.webview = QWebView()
        self.webview.setWindowTitle(title)
        self.webview.setCursor(QtCore.Qt.BlankCursor)
        self.loadSignal = Signal(self.actuallyShow)

    def show(self, url):
        logger.debug("WebViewer show " + str(url))
        self.loadSignal(url)

    def actuallyShow(self, url):
        logger.debug("WebViewer load " + str(url))
        self.webview.load(QtCore.QUrl(url))
        self.makeVisible()

    def makeVisible(self):
        global activeView
        if activeView is self: return
        logger.debug("Switching viewer to WebViewer")
        if activeView: activeView.hide()
        if not self.webview.isVisible(): self.webview.showFullScreen()
        activeView = self

    def hide(self):
        self.webview.hide()


class UniversalViewer:
    def __init__(self, title):
        self.imageViewer = ImageViewer(title)
        self.webViewer = WebViewer(title)


    def show(self, url):
        if url.startswith('http://') or url.startswith('https://'):
            self.webViewer.show(url)
        else:
            self.imageViewer.show(url)


# ------------------------------------------------------------------------------

app = None
screenGeometry = None
timer = None

def init(argv):
    global app, screenGeometry
    app = QtWidgets.QApplication(argv)
    screenGeometry = app.screens()[0].geometry()
    workaroundToAllowSignalProcessing()


def workaroundToAllowSignalProcessing():
    # Qt main prevents python signal handlers from running
    # until a Qt event happens. To work around this,
    # we start a timer and give it an empty function to run
    # periodically. Each timer the timer triggers, python
    # will have a chance to run signal handlers.
    global timer, foo
    timer = QtCore.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)


def main():
    return app.exec_()


def exit():
    app.exit(0)
