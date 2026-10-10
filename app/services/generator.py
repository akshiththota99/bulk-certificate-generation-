# Certificate generation logic
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def generate_certificate(recipient_name, course_name, output_path):
    """Create a single predefined certificate template with recipient-specific details."""
    directory = os.path.dirname(output_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    pdf = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    pdf.setTitle(f"Certificate of Completion - {recipient_name}")
    pdf.setFillColor(colors.darkgreen)

    pdf.setStrokeColor(colors.darkgreen)
    pdf.setLineWidth(3)
    pdf.rect(0.6 * inch, 0.6 * inch, width - 1.2 * inch, height - 1.2 * inch)

    pdf.setFillColor(colors.darkgreen)
    pdf.setFont("Helvetica-Bold", 26)
    pdf.drawCentredString(width / 2, height - 1.2 * inch, "Certificate of Completion")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(width / 2, height - 1.8 * inch, "This certifies that")

    pdf.setStrokeColor(colors.darkgreen)
    pdf.line(1.5 * inch, height - 2.2 * inch, width - 1.5 * inch, height - 2.2 * inch)

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(width / 2, height - 3.0 * inch, recipient_name)

    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(width / 2, height - 4.0 * inch, "has successfully completed")

    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(width / 2, height - 4.9 * inch, course_name)

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, height - 6.4 * inch, "Awarded on " + datetime.now().strftime("%d %B %Y"))

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(1.2 * inch, 1.2 * inch, "Authorized by Bulk Certificate Generator")

    pdf.setFont("Helvetica", 10)
    pdf.drawRightString(width - 1.2 * inch, 1.2 * inch, "Generated electronically")

    pdf.save()