import os
import reportlab
from reportlab.pdfgen import canvas
from reportlab.pdfgen.canvas import Canvas
folder = os.path.dirname(reportlab.__file__) + os.sep + 'fonts'
afmFile = os.path.join(folder, 'DarkGardenMK.afm')
pfbFile = os.path.join(folder, 'DarkGardenMK.pfb')

from reportlab.pdfbase import pdfmetrics
justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
faceName = 'DarkGardenMK' # pulled from AFM file
pdfmetrics.registerTypeFace(justFace)
justFont = pdfmetrics.Font('DarkGardenMK',
                           faceName,
                           'WinAnsiEncoding')
pdfmetrics.registerFont(justFont)

Canvas.setFont(psfontname='DarkGardenMK', size=32)
Canvas.drawString(10, 150, 'This should be in')
Canvas.drawString(10, 100, 'DarkGardenMK')