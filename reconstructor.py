import os
from fpdf import FPDF
import qrcode
import io
import hashlib
import base64
from datetime import datetime

def generar_constancia_pdf(datos, rfc_usuario, idcif_usuario, url_sat):
    # 1. Definir la ruta de la imagen de forma segura para Vercel
    base_path = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(base_path, 'plantilla.png')

    # Generación de sellos
    fecha_emision = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    cadena = f"||{fecha_emision}|{rfc_usuario}|CONSTANCIA DE SITUACIÓN FISCAL|{idcif_usuario}||"
    sello = base64.b64encode(hashlib.sha256(cadena.encode()).digest()).decode('utf-8')

    # Generar QR
    qr = qrcode.QRCode(box_size=10, border=0)
    qr.add_data(url_sat)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    qr_io = io.BytesIO()
    img_qr.save(qr_io, format='PNG')
    qr_io.seek(0)

    pdf = FPDF()
    pdf.add_page()
    
    # 2. Cargar plantilla con verificación de existencia
    if os.path.exists(image_path):
        pdf.image(image_path, x=0, y=0, w=210, h=297)
    else:
        # Si falla, el PDF no sale en blanco pero al menos no tumba el servidor
        pdf.set_font("Helvetica", "B", 12)
        pdf.text(10, 10, "Error: No se encontró plantilla.png en la raíz")

    # --- Los mismos datos de encimado ---
    pdf.image(qr_io, x=13, y=27, w=35)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(50, 31)
    pdf.cell(0, 5, rfc_usuario)
    
    pdf.set_xy(50, 41)
    nombre = f"{datos.get('Nombre (s)', '')} {datos.get('Primer Apellido', '')} {datos.get('Segundo Apellido', '')}".strip()
    pdf.set_font("Helvetica", "B", 8)
    pdf.multi_cell(50, 3.5, nombre.upper())
    
    pdf.set_xy(50, 53)
    pdf.cell(0, 5, f"idCIF: {idcif_usuario}")

    # Datos de tabla
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(42, 71.5)
    pdf.cell(0, 5, rfc_usuario)
    pdf.set_xy(42, 77)
    pdf.cell(0, 5, datos.get('CURP', ''))
    
    # Sellos
    pdf.set_font("Helvetica", "", 5)
    pdf.set_xy(65, 258)
    pdf.multi_cell(130, 2.5, cadena)
    pdf.set_xy(65, 266)
    pdf.multi_cell(130, 2, sello)

    output = io.BytesIO()
    output.write(pdf.output())
    output.seek(0)
    return output
    
