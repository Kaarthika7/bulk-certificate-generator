import os

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas


def generate_certificate(name: str, course_name: str, issued_on: str, output_path: str) -> None:
    """Draw one certificate PDF and save it at output_path."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    width, height = landscape(A4)
    c = canvas.Canvas(output_path, pagesize=(width, height))

    # double border
    c.setStrokeColor(HexColor("#1F3A5F"))
    c.setLineWidth(6)
    c.rect(30, 30, width - 60, height - 60)
    c.setLineWidth(1.5)
    c.rect(45, 45, width - 90, height - 90)

    # text, from top to bottom
    c.setFillColor(HexColor("#1F3A5F"))
    c.setFont("Helvetica-Bold", 38)
    c.drawCentredString(width / 2, height - 130, "Certificate of Completion")

    c.setFillColor(HexColor("#333333"))
    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, height - 190, "This is to certify that")

    c.setFont("Helvetica-Bold", 34)
    c.drawCentredString(width / 2, height - 250, name)

    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, height - 300, "has successfully completed")

    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 345, course_name)

    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 420, f"Issued on: {issued_on}")

    c.save()