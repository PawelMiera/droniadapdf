import io
from django.http import FileResponse
from reportlab.lib.pagesizes import A4

from reportlab.lib.styles import ParagraphStyle

from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import *
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from datetime import datetime
import pyrebase
import matplotlib.pyplot as plt

from svglib.svglib import svg2rlg

import requests


class FirebaseConnection:
    def __init__(self):
        config = {
            "apiKey": "AIzaSyAglFX49k28WWJqS33SQEpct3kE_d3JDZs",
            "authDomain": "droniada-f604a.firebaseapp.com",
            "databaseURL": "https://droniada-f604a-default-rtdb.firebaseio.com",
            "projectId": "droniada-f604a",
            "storageBucket": "droniada-f604a.appspot.com",
            "messagingSenderId": "65160484994",
            "appId": "1:65160484994:web:f38e43420da263ba44bc9b"
        }

        self.firebase = pyrebase.initialize_app(config)

        self.database = self.firebase.database()

        self.storage = self.firebase.storage()

    def get_detections(self):
        return self.database.child("circles").child("targets").get().val()


def create_map(latitude_parch, longitude_parch, latitude_maczniak, longitude_maczniak):

    my_map = plt.imread('drzewo.png')

    fig, ax = plt.subplots()

    BBox = (16.22935, 16.23578, 52.23836, 52.24094)

    ax.scatter(longitude_maczniak, latitude_maczniak, c='b', s=10, label="Maczniak jabloni")

    ax.scatter(longitude_parch, latitude_parch, c='r', s=10, label="Parch")

    ax.set_title('Drzewo zycia')

    ax.legend()

    ax.set_xlim(BBox[0], BBox[1])
    ax.set_ylim(BBox[2], BBox[3])

    ax.imshow(my_map, zorder=0, extent=BBox, aspect='equal')

    imgdata = io.BytesIO()

    fig.savefig(imgdata, format='svg', bbox_inches='tight')

    imgdata.seek(0)

    return imgdata


def create_pdf(map_img, data):

    buffer = io.BytesIO()

    story = []
    styles = getSampleStyleSheet()

    normal = styles['Normal']
    bold = styles['Heading3']

    small = ParagraphStyle(name="small", fontSize=12)

    styleH = styles['Heading1']

    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2 * cm, leftMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm)

    doc.title = "Drzewo Zycia AGH Drone Engineering"

    img = Image('logo.png', 8 * cm, 2 * cm)
    img.hAlign = 'RIGHT'

    story.append(img)

    P = Paragraph(u"Misja Drzewo Zycia<br></br><br></br>", styleH)
    story.append(P)

    now = datetime.now()

    mytime = now.strftime("%d/%m/%Y o godzinie: %H:%M:%S")

    text = "Raport zostal wygenerowany automatycznie przez druzyne AGH Drone Engineering. <br></br>" \
           "<br></br>Report zostal utworzony dnia: " + mytime + ".<br></br>"

    P = Paragraph(text, small)
    story.append(P)

    P = Paragraph(
        "<br></br>Celem tego raportu jest udokumentowanie danych misji dostarczonych przez drony do "
        "Firebase'a.<br></br>", normal)
    story.append(P)

    P = Paragraph("<br></br>1. Mapa wszystkich wykryc:<br></br><br></br><br></br>", bold)
    story.append(P)

    img = svg2rlg(map_img)
    story.append(img)

    P = Paragraph("<br></br><br></br>Na mapie zostaly przedstawione wszyskie zlokalizowane choroby jablonek. "
                  "Niebieskie kropki reprezentuja maczniaka jabloni, a czerwone "
                  "parch.<br></br><br></br><br></br><br></br><br></br><br></br><br></br><br></br><br></br><br></br>",
                  normal)
    story.append(P)

    P = Paragraph("<br></br><br></br><br></br>2. Tabela zawieraca wykrycia, ich lokalizacje oraz zdjecia:", bold)
    story.append(P)

    table_style = TableStyle([('ALIGN', (0, 0), (-1, -0), 'CENTER'),
                              ('TEXTCOLOR', (0, 0), (-1, 0), colors.red),
                              ('ALIGN', (0, 1), (0, -0), 'BOTTOM'),
                              ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                              ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                              ])

    t = Table(data, style=table_style)

    story.append(t)

    doc.build(story)

    buffer.seek(0)

    return buffer


def index(request):
    firebaseConnection = FirebaseConnection()

    targets = firebaseConnection.get_detections()

    data = [['Description', 'Latitude', 'Longitude', 'State', 'Photo']]

    latitude_parch = []
    longitude_parch = []

    latitude_maczniak = []
    longitude_maczniak = []

    for target in targets:
        if int(target['eliminated']) == 0:
            state = "Queued"
        elif int(target['eliminated']) == 0:
            state = "Eliminated"
        elif int(target['eliminated']) == 0:
            state = "Not Eliminated"
        else:
            state = "Unknown state"

        url = firebaseConnection.storage.child(target['photo']).get_url(None)

        response = requests.get(url)

        image = Image(io.BytesIO(response.content))
        image.drawHeight = 5 * cm
        image.drawWidth = 5 * cm

        row = [target['description'], "%.7f" % float(target['latitude']), "%.7f" % float(target['longitude']), state, image]

        if int(target['color']) == 0:
            latitude_maczniak.append(target['latitude'])
            longitude_maczniak.append(target['longitude'])
        elif int(target['color']) == 1:
            latitude_parch.append(target['latitude'])
            longitude_parch.append(target['longitude'])

        data.append(row)

    my_map = create_map(latitude_parch, longitude_parch, latitude_maczniak, longitude_maczniak)
    buffer = create_pdf(my_map, data)

    return FileResponse(buffer, as_attachment=True, filename='AGH_Drone_Engineering_Drzewo_Zycia_Raport.pdf')

