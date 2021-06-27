from django.shortcuts import render
import io
from django.http import FileResponse
from django.http import HttpResponse
from reportlab.pdfgen import canvas
import pyrebase
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
import csv
import datetime
from reportlab.lib.units import cm, inch
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import *
from reportlab.lib.styles import getSampleStyleSheet

import os
from pathlib import Path
from datetime import datetime



def index(request):

    if 'id' in request.GET:
        message = 'You submitted: %r' % request.GET['id']
    else:
        message = 'You submitted nothing!'

    return HttpResponse(message)

    """buffer = io.BytesIO()

    p = canvas.Canvas(buffer)


    p.drawString(100, 100, "Hello world.")

    p.showPage()
    p.save()


    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='AGH_Drone_Engineering_Trzy_Kolory_Raport.pdf')"""