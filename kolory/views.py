import datetime
import io
from datetime import datetime

import haversine as hs
import numpy as np
import pyrebase
import requests
from django.http import FileResponse, HttpResponse, HttpRequest
from haversine import Unit
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import *


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

    def get_detections(self, x):
        return self.database.child("drones").child(x).child("detections").get()


class PdfCreator:

    @staticmethod
    def createPdf(data, x):
        buffer = io.BytesIO()

        story = []
        styles = getSampleStyleSheet()
        normal = styles['Normal']
        bold = styles['Heading3']

        small = ParagraphStyle(name="small", fontSize=12)

        styleH = styles['Heading1']

        now = datetime.now()

        mytime = now.strftime("%d/%m/%Y o godzinie: %H:%M:%S")

        text = "Raport zostal wygenerowany automatycznie przez druzyne AGH Drone Engineering. <br></br>" \
               "<br></br>Report zostal utworzony dnia: " + mytime + ".<br></br>"

        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=2 * cm, leftMargin=2 * cm,
                                topMargin=2 * cm, bottomMargin=2 * cm)

        doc.title = "Trzy Kolory AGH Drone Engineering"

        img = Image('logo.png', 8 * cm, 2 * cm)
        img.hAlign = 'RIGHT'

        story.append(img)
        P = Paragraph("Misja Trzy Kolory<br /><br /><br />", styleH)

        story.append(P)
        P = Paragraph(text, small)
        story.append(P)

        drone_nr = "<br />Raport zostal wygenerowany dla drona nr: " + x + ".<br></br>"
        P = Paragraph(drone_nr, small)
        story.append(P)

        P = Paragraph("Celem tego raportu jest udokumentowanie danych misji dostarczonych przez drony do "
                      "Firebase'a.<br /><br />", small)
        story.append(P)

        P = Paragraph("1. Tabela zawieraca wykrycia, ich lokalizacje oraz zdjecia:<br></br>", bold)
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

    if 'id' in request.GET:

        firebaseConnection = FirebaseConnection()

        x = request.GET['id']

        targets = firebaseConnection.get_detections(x)

        data = [['Area', 'Description', 'Latitude', 'Longitude', 'Photo']]
        cord = []

        desc = []
        seen_kap = []
        seen_praw = []
        seen_fyt = []
        all_val = {}

        for target in targets.each():

            desc.append({target.key(): target.val()["description"]})

            if target.val()["description"] == "Maczniak prawdziwy":
                seen_praw.append((target.key(), target.val()["seen_times"]))
                cord.append((target.key(), (target.val()["latitude"], target.val()["longitude"])))
            elif target.val()["description"] == "Maczniak rzekomy kapustowatych":
                seen_kap.append((target.key(), target.val()["seen_times"]))
                cord.append((target.key(), (target.val()["latitude"], target.val()["longitude"])))
            elif target.val()["description"] == "Fytoftoroza":
                seen_fyt.append((target.key(), target.val()["seen_times"]))
                cord.append((target.key(), (target.val()["latitude"], target.val()["longitude"])))
            else:
                pass

            all_val[target.key()] = target.val()
            del target.val()['seen_times']

        seen_fyt.sort(key=lambda tup: (-tup[1], tup[0]))
        seen_praw.sort(key=lambda tup: (-tup[1], tup[0]))
        seen_kap.sort(key=lambda tup: (-tup[1], tup[0]))

        distances = []
        for i in range(len(cord)):
            point1 = cord[i][1]
            for j in range(len(cord)):
                point2 = cord[j][1]
                distances.append((cord[i][0], cord[j][0], hs.haversine(point1, point2, unit=Unit.METERS)))

        distances.sort(key=lambda tup: tup[2])
        distances = distances[len(cord):]
        del distances[::2]

        barszcz = []
        for i, val in enumerate(distances):
            if val[2] <= 3:
                barszcz.append(val[0])
                barszcz.append(val[1])

        barszcz = np.unique(barszcz)
        lat = 0
        lon = 0
        area = 0

        if len(barszcz) == 3:
            for i in barszcz:
                lat += all_val[i]['latitude']
                lon += all_val[i]['longitude']
                area += all_val[i]['area']
                sample_barszcz = i
            if all_val[i]['description'] == 'Maczniak rzekomy kapustowatych':
                sample_barszcz = i
                all_val[sample_barszcz]['photo'] = all_val[i]['photo']

            all_val[sample_barszcz]['latitude'] = lat / 3
            all_val[sample_barszcz]['longitude'] = lon / 3
            all_val[sample_barszcz]['area'] = area
            all_val[sample_barszcz]['description'] = 'Barszcz sosnowskiego'

            data.append(list(all_val[sample_barszcz].values()))

        elif len(barszcz) == 2:
            for i in barszcz:
                lat += all_val[i]['latitude']
                lon += all_val[i]['longitude']
                area += all_val[i]['area']
                sample_barszcz = i
            if all_val[i]['description'] == 'Maczniak rzekomy kapustowatych':
                sample_barszcz = i

            all_val[sample_barszcz]['latitude'] = lat / 2
            all_val[sample_barszcz]['longitude'] = lon / 2
            all_val[sample_barszcz]['area'] = area * 3 / 2
            all_val[sample_barszcz]['description'] = 'Barszcz sosnowskiego'

            data.append(list(all_val[sample_barszcz].values()))

        for i, val in enumerate(seen_praw):
            if seen_praw[i][0] not in barszcz:
                data.append(list(all_val[seen_praw[i][0]].values()))
            if i == 3:
                break

        for i, val in enumerate(seen_kap):
            if seen_kap[i][0] not in barszcz:
                data.append(list(all_val[seen_kap[i][0]].values()))
            if i == 3:
                break

        for i, val in enumerate(seen_fyt):
            if seen_fyt[i][0] not in barszcz:
                data.append(list(all_val[seen_fyt[i][0]].values()))
            if i == 3:
                break

        for i, val in enumerate(data[1:]):
            data[i + 1][0] = "%.2f" % float(data[i + 1][0])
            data[i + 1][2] = "%.7f" % float(data[i + 1][2])
            data[i + 1][3] = "%.7f" % float(data[i + 1][3])

            url = firebaseConnection.storage.child(data[i + 1][-1]).get_url(None)

            response = requests.get(url)

            image = Image(io.BytesIO(response.content))

            image.drawHeight = 5 * cm
            image.drawWidth = 5 * cm
            data[i + 1][-1] = image

        buffer = PdfCreator.createPdf(data, x)
        return FileResponse(buffer, as_attachment=True, filename='AGH_Drone_Engineering_Trzy_Kolory_Rapor3 t.pdf')

    else:
        message = 'Some error occurred!'

        return HttpResponse(message)



"""def index(request):

    if 'id' in request.GET:
        message = 'You submitted: %r' % request.GET['id']
    else:
        message = 'You submitted nothing!'

    return HttpResponse(message)
    buffer = io.BytesIO()

    p = canvas.Canvas(buffer)


    p.drawString(100, 100, "Hello world.")

    p.showPage()
    p.save()


    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='AGH_Drone_Engineering_Trzy_Kolory_Raport.pdf')"""