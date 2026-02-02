from fpdf import FPDF
import qrcode
import io
import hashlib
import base64
from datetime import datetime

def generar_constancia_pdf(datos, rfc, idcif, url_orig):
    # 1. Crear Metadatos de Validación
    fecha_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    cadena = f"||{rfc}|{idcif}|{fecha_iso}||"
    sello = base64.b64encode(hashlib.sha256(cadena.encode()).digest()).decode('utf-8')

    # 2. Crear QR
    qr_img = qrcode.make(url_orig)
    qr_io = io.BytesIO()
    qr_img.save(qr_io, format='PNG')
    qr_io.seek(0)

    # 3. Dibujar PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Estética tipo SAT
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "CONSTANCIA DE SITUACIÓN FISCAL", ln=True, align='C')
    pdf.ln(5)

    # Bloque de Identidad con QR
    pdf.image(qr_io, x=10, y=30, w=40)
    pdf.set_xy(55, 35)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, f"RFC: {rfc}", ln=True)
    pdf.set_x(55)
    nombre = f"{datos.get('Nombre', '')} {datos.get('Apellido Paterno', '')} {datos.get('Apellido Materno', '')}"
    pdf.multi_cell(0, 7, f"NOMBRE: {nombre}")

    # Tabla de Datos Extraídos
    pdf.set_xy(10, 80)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 8, " INFORMACIÓN TRIBUTARIA", ln=True, fill=True)
    
    pdf.set_font("Helvetica", "", 9)
    for k, v in datos.items():
        if k not in ['Nombre', 'Apellido Paterno', 'Apellido Materno']:
            pdf.cell(60, 6, f"{k}:", border='B')
            pdf.cell(0, 6, f" {v}", border='B', ln=True)

    # Pie con Validación
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(0, 5, "Cadena Original:", ln=True)
    pdf.set_font("Helvetica", "", 7)
    pdf.multi_cell(0, 4, cadena)
    
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(0, 5, "Sello Digital:", ln=True)
    pdf.set_font("Helvetica", "", 7)
    pdf.multi_cell(0, 4, sello)

    # Salida binaria
    out = io.BytesIO()
    out.write(pdf.output())
    out.seek(0)
    return out
  
