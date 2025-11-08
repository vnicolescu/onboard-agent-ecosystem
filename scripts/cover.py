from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

width, height = A4
beige = HexColor("#f8f4ed")        # light beige background
blue = HexColor("#91a8d0")         # pastel French blue accent
black = HexColor("#000000")

c = canvas.Canvas("Page_de_couverture.pdf", pagesize=A4)

# background
c.setFillColor(beige)
c.rect(0, 0, width, height, fill=1, stroke=0)

# title
c.setFillColor(black)
c.setFont("Times-Bold", 36)
c.drawCentredString(width/2, height/2 + 40, "Cahier d’étude du français")

# subtitle
c.setFont("Times-Italic", 18)
c.drawCentredString(width/2, height/2 - 5, "Apprendre, écouter, lire, progresser chaque jour")

# accent line
c.setStrokeColor(blue)
c.setLineWidth(3)
c.line(width/3, height/2 - 20, 2*width/3, height/2 - 20)

c.showPage()
c.save()
print("✅  Page_de_couverture.pdf created!")
