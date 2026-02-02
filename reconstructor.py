import os
from fpdf import FPDF
import qrcode
import io
import hashlib
import base64
from datetime import datetime

def generar_constancia_pdf(datos, rfc_usuario, idcif_usuario, url_sat):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(base_dir, 'plantilla.png')

    # --- Lógica de Validación ---
    fecha_emision = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    cadena = f"||{fecha_emision}|{rfc_usuario}|CONSTANCIA DE SITUACIÓN FISCAL|{idcif_usuario}||"
    sello = base64.b64encode(hashlib.sha256(cadena.encode()).digest()).decode('utf-8')

    # --- QR Dinámico ---
    qr = qrcode.QRCode(version=1, box_size=10, border=0)
    qr.add_data(url_sat)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    qr_io = io.BytesIO()
    img_qr.save(qr_io, format='PNG')
    qr_io.seek(0)

    # --- Creación del PDF ---
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    if os.path.exists(image_path):
        pdf.image(image_path, x=0, y=0, w=210, h=297)

    # --- BLOQUE A: CÉDULA (BASADO EN TU MAPA DE IMAGEN) ---
    # QR: Coords 92, 562 (px) -> ~12mm, 47.5mm
    pdf.image(qr_io, x=12, y=47.5, w=34)
    
    # RFC: Coords 754, 580 (px) -> ~63mm, 49mm
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(63, 49)
    pdf.cell(0, 5, rfc_usuario)
    
    # Nombre: Coords 706, 730 (px) -> ~59mm, 62mm
    pdf.set_xy(59, 62)
    nombre_full = f"{datos.get('Nombre (s)', '')} {datos.get('Primer Apellido', '')} {datos.get('Segundo Apellido', '')}".strip()
    pdf.set_font("Helvetica", "B", 8)
    pdf.multi_cell(60, 3.5, nombre_full.upper())
    
    # idCIF: Coords 878, 904 (px) -> ~74mm, 76.5mm
    pdf.set_xy(74, 76.5)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, f"idCIF: {idcif_usuario}")

    # --- BLOQUE B: LUGAR Y FECHA ---
    # Coords 1396, 826 (px) -> ~118mm, 70mm
    pdf.set_font("Helvetica", "", 7)
    pdf.set_xy(118, 70)
    fecha_txt = f"CUAUHTEMOC, CIUDAD DE MEXICO, A {datetime.now().strftime('%d DE %B DE %Y').upper()}"
    pdf.cell(80, 4, fecha_txt, align='C')

    # --- BLOQUE C: TABLA DE IDENTIFICACIÓN (AJUSTE PROPORCIONAL) ---
    pdf.set_font("Helvetica", "", 8)
    # RFC en tabla
    pdf.set_xy(43, 102) 
    pdf.cell(0, 5, rfc_usuario)
    # CURP
    pdf.set_xy(43, 107.5)
    pdf.cell(0, 5, datos.get('CURP', ''))
    # Nombre(s)
    pdf.set_xy(43, 113.1)
    pdf.cell(0, 5, datos.get('Nombre (s)', '').upper())
    # Apellidos y fechas siguen la misma proporción (+5.6mm cada uno)
    pdf.set_xy(43, 118.7)
    pdf.cell(0, 5, datos.get('Primer Apellido', '').upper())
    pdf.set_xy(43, 124.3)
    pdf.cell(0, 5, datos.get('Segundo Apellido', '').upper())
    pdf.set_xy(43, 129.9)
    pdf.cell(0, 5, datos.get('Fecha inicio de operaciones', '').upper())
    pdf.set_xy(43, 135.5)
    pdf.cell(0, 5, datos.get('Estatus en el padrón', 'ACTIVO').upper())
    pdf.set_xy(43, 141.1)
    pdf.cell(0, 5, datos.get('Fecha de último cambio de estado', '').upper())

    # --- SELLOS FINALES ---
    pdf.set_font("Helvetica", "", 5)
    pdf.set_xy(65, 258)
    pdf.multi_cell(130, 2.5, cadena)
    pdf.set_xy(65, 266)
    pdf.multi_cell(130, 2, sello)

    output = io.BytesIO()
    output.write(pdf.output())
    output.seek(0)
    return output
    
