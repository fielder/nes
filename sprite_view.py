"""
Open a NES rom file and show all contents as NES sprites/patterns. This
simply shows the whole file as sprites. Therefore, there will be plenty
of obviously invalid sprites. This is really a helper to find where a
ROM's sprites exist.
"""

#TODO: allow non-8x8 sprites?
#TODO: allow changing the file byte alignment the sprites are taken from

import sys
import os
import re

import collections

from PyQt4 import QtCore
from PyQt4 import QtGui

# taken from: http://www.zophar.net/fileuploads/2/10690nxpfq/AoRH.htm
nes_palette = [ \
    QtGui.qRgb(0x78, 0x80, 0x84),
    QtGui.qRgb(0x00, 0x00, 0xfc),
    QtGui.qRgb(0x00, 0x00, 0xc4),
    QtGui.qRgb(0x40, 0x28, 0xc4),
    QtGui.qRgb(0x94, 0x00, 0x8c),
    QtGui.qRgb(0xac, 0x00, 0x28),
    QtGui.qRgb(0xac, 0x10, 0x00),
    QtGui.qRgb(0x8c, 0x18, 0x00),
    QtGui.qRgb(0x50, 0x30, 0x00),
    QtGui.qRgb(0x00, 0x78, 0x00),
    QtGui.qRgb(0x00, 0x68, 0x00),
    QtGui.qRgb(0x00, 0x58, 0x00),
    QtGui.qRgb(0x00, 0x40, 0x58),
    QtGui.qRgb(0x00, 0x00, 0x00),
    QtGui.qRgb(0x00, 0x00, 0x00),
    QtGui.qRgb(0x00, 0x00, 0x08),
    QtGui.qRgb(0xbc, 0xc0, 0xc4),
    QtGui.qRgb(0x00, 0x78, 0xfc),
    QtGui.qRgb(0x00, 0x88, 0xfc),
    QtGui.qRgb(0x68, 0x48, 0xfc),
    QtGui.qRgb(0xdc, 0x00, 0xd4),
    QtGui.qRgb(0xe4, 0x00, 0x60),
    QtGui.qRgb(0xfc, 0x38, 0x00),
    QtGui.qRgb(0xe4, 0x60, 0x18),
    QtGui.qRgb(0xac, 0x80, 0x00),
    QtGui.qRgb(0x00, 0xb8, 0x00),
    QtGui.qRgb(0x00, 0xa8, 0x00),
    QtGui.qRgb(0x00, 0xa8, 0x48),
    QtGui.qRgb(0x00, 0x88, 0x94),
    QtGui.qRgb(0x2c, 0x2c, 0x2c),
    QtGui.qRgb(0x00, 0x00, 0x00),
    QtGui.qRgb(0x00, 0x00, 0x00),
    QtGui.qRgb(0xfc, 0xf8, 0xfc),
    QtGui.qRgb(0x38, 0xc0, 0xfc),
    QtGui.qRgb(0x68, 0x88, 0xfc),
    QtGui.qRgb(0x9c, 0x78, 0xfc),
    QtGui.qRgb(0xfc, 0x78, 0xfc),
    QtGui.qRgb(0xfc, 0x58, 0x9c),
    QtGui.qRgb(0xfc, 0x78, 0x58),
    QtGui.qRgb(0xfc, 0xa0, 0x48),
    QtGui.qRgb(0xfc, 0xb8, 0x00),
    QtGui.qRgb(0xbc, 0xf8, 0x18),
    QtGui.qRgb(0x58, 0xd8, 0x58),
    QtGui.qRgb(0x58, 0xf8, 0x9c),
    QtGui.qRgb(0x00, 0xe8, 0xe4),
    QtGui.qRgb(0x60, 0x60, 0x60),
    QtGui.qRgb(0x00, 0x00, 0x00),
    QtGui.qRgb(0x00, 0x00, 0x00),
    QtGui.qRgb(0xfc, 0xf8, 0xfc),
    QtGui.qRgb(0xa4, 0xe8, 0xfc),
    QtGui.qRgb(0xbc, 0xb8, 0xfc),
    QtGui.qRgb(0xdc, 0xb8, 0xfc),
    QtGui.qRgb(0xfc, 0xb8, 0xfc),
    QtGui.qRgb(0xf4, 0xc0, 0xe0),
    QtGui.qRgb(0xf4, 0xd0, 0xb4),
    QtGui.qRgb(0xfc, 0xe0, 0xb4),
    QtGui.qRgb(0xfc, 0xd8, 0x84),
    QtGui.qRgb(0xdc, 0xf8, 0x78),
    QtGui.qRgb(0xb8, 0xf8, 0x78),
    QtGui.qRgb(0xb0, 0xf0, 0xd8),
    QtGui.qRgb(0x00, 0xf8, 0xfc),
    QtGui.qRgb(0xc8, 0xc0, 0xc0),
    QtGui.qRgb(0x00, 0x00, 0x00),
    QtGui.qRgb(0x00, 0x00, 0x00),
]

app = None
win = None
last_dir = ""
filedata = ""

scene = None

# keyed by file offset
pixmaps = collections.OrderedDict()

palette = {}
palette[0] = nes_palette[63]
palette[1] = nes_palette[45]
palette[2] = nes_palette[0]
palette[3] = nes_palette[16]

spacing = 4.0


def _pixmapForNESBytes(b):
    image = QtGui.QImage(8, 8, QtGui.QImage.Format_RGB32)

    lo_bits = b[:8]
    hi_bits = b[8:]

    for y in xrange(8):
        lo_row = ord(lo_bits[y])
        hi_row = ord(hi_bits[y])
        for x in xrange(8):
            bit = 1 << x
            l = (lo_row & bit) == bit
            h = (hi_row & bit) == bit
            pixval = (l << 0) | (h << 1)
            image.setPixel(7 - x, y, palette[pixval])

    return QtGui.QPixmap.fromImage(image)


def _createPixmaps():
    global pixmaps

    pixmaps.clear()
    for file_offset, pic_bytes in _chop(filedata, 16):
        if len(pic_bytes) == 16: # ignore unaligned crap at end of file
            pixmaps[file_offset] = _pixmapForNESBytes(pic_bytes)


def refreshGUI():
    _createPixmaps()

    scene.clear()

    stride = 8.0 + spacing

    idx = 0
    x = 0.0
    y = 0.0
    for file_offset, pixmap in pixmaps.iteritems():
        x += stride

        gitem = scene.addPixmap(pixmap)
        gitem.setToolTip("0x%x" % file_offset)
        gitem.setPos(x, y)

        idx += 1
        if idx > 0 and ((idx % 16) == 0):
            y += stride
            x = 0.0

    scene.views()[0].setSceneRect(scene.itemsBoundingRect())


def _chop(dat, chopsz):
    idx = 0
    while idx < len(dat):
        yield (idx, dat[idx:idx + chopsz])
        idx += chopsz


def openDoc(path):
    global last_dir
    global filedata

    filedata = open(path, "rb").read()

    win.setWindowTitle(path)
    last_dir = os.path.dirname(path)
    refreshGUI()


def _runOpenDoc():
    path = QtGui.QFileDialog.getOpenFileName(parent=win, caption="Open", directory=last_dir)
    path = str(path)
    if not path:
        return

    try:
        openDoc(path)
    except Exception as e:
        QtGui.QMessageBox.warning(win, "Error", str(e))
        return


class BaseColorButton(QtGui.QPushButton):
    def __init__(self, color=None, parent=None):
        super(BaseColorButton, self).__init__(parent=parent)

        self.setObjectName("color_button")
        self.setColor(color)

    def sizeHint(self):
        return QtCore.QSize(32, 32)

    def clearColor(self):
        self.setColor(None)

    def setColor(self, color):
        if not color:
            self.setStyleSheet("")
        else:
            rgb = (color.red(), color.green(), color.blue())
            self.setStyleSheet("#color_button { background-color: rgb(%d,%d,%d) }" % rgb)

    def color(self):
        m = re.compile(r"rgb\((\d+),(\d+),(\d+)\)").search(self.styleSheet())
        if m:
            rgb = (int(m.group(gidx)) for gidx in (1, 2, 3))
            ret = QtGui.QColor(*rgb)
        else:
            ret = None
        return ret


class PickColorDialog(QtGui.QDialog):
    def __init__(self, *args, **kwargs):
        super(PickColorDialog, self).__init__(*args, **kwargs)

        self.setWindowTitle("Choose color")

        vbox = QtGui.QVBoxLayout()
        idx = 0
        for row in xrange(4):
            hbox = QtGui.QHBoxLayout()
            for col in xrange(16):
                b = BaseColorButton()
                b.clicked.connect(self._clicked)
                b.setColor(QtGui.QColor.fromRgb(nes_palette[idx]))
                b.setToolTip("%d" % idx)
                hbox.addWidget(b)
                idx += 1
            vbox.addLayout(hbox)
        self.setLayout(vbox)

        self._selected = None

    def selected(self):
        if self._selected is None:
            raise Exception("no selection")
        return self._selected

    def _clicked(self):
        self._selected = int(self.sender().toolTip())
        self.accept()


class PickColorButton(BaseColorButton):
    colorChanged = QtCore.pyqtSignal(int, object)

    def __init__(self, *args, **kwargs):
        super(PickColorButton, self).__init__(*args, **kwargs)

        self.clicked.connect(self._runColorPicker)

    def _runColorPicker(self):
        dlg = PickColorDialog()
        if dlg.exec_():
            new_color = QtGui.QColor.fromRgb(nes_palette[dlg.selected()])
            self.setColor(new_color)
            self.colorChanged.emit(int(self.toolTip()), new_color)


def _colorChanged(idx, color):
    palette[idx] = color.rgb()
    refreshGUI()


def _changeSpacing():
    global spacing

    try:
        new = float(str(app.sender().text()))
        if new < 0 or new > 16:
            raise ValueError()
    except ValueError:
        return

    if new != spacing:
        spacing = new

        #TODO: don't do a heavy-handed refresh, just rearrange what's
        #      already there
        refreshGUI()


def _mainWidget():
    global scene

    view = QtGui.QGraphicsView()
    view.setRenderHints(view.renderHints() | QtGui.QPainter.Antialiasing)
    view.setScene(QtGui.QGraphicsScene(parent=view))
    view.scale(4.0, 4.0)

    scene = view.scene()

    vbox = QtGui.QVBoxLayout()
    for idx in xrange(4):
        b = PickColorButton()
        b.setColor(QtGui.QColor.fromRgb(palette[idx]))
        b.colorChanged.connect(_colorChanged)
        b.setToolTip("%d" % idx)
        vbox.addWidget(b)

    textbox = QtGui.QLineEdit()
    textbox.setToolTip("spacing")
    textbox.setFixedWidth(32)
    textbox.setText(str(spacing))
    textbox.editingFinished.connect(_changeSpacing)
    vbox.addWidget(textbox)

    vbox.addStretch()

    hbox = QtGui.QHBoxLayout()
    hbox.addWidget(view)
    hbox.addLayout(vbox)

    w = QtGui.QWidget()
    w.setLayout(hbox)

    return w


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    win = QtGui.QMainWindow()

    m = win.menuBar().addMenu("&File")
    a = m.addAction("&Open", _runOpenDoc)
    a.setShortcut(QtGui.QKeySequence.Open)
    a = m.addAction("E&xit", win.close)
    a.setShortcut(QtGui.QKeySequence.Quit)

    win.setCentralWidget(_mainWidget())
    win.setWindowTitle("[No Name]")
    win.setWindowIcon(QtGui.QIcon(":/trolltech/qmessagebox/images/qtlogo-64.png"))
    win.show()
    win.resize(848, 720)

    last_dir = os.path.abspath(".")

    if len(sys.argv) > 1:
        openDoc(sys.argv[1])

    sys.exit(app.exec_())
