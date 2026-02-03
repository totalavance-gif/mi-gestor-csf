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

    # --- Traducción de Fecha ---
    meses = {"January": "ENERO", "February": "FEBRERO", "March": "MARZO", "April": "ABRIL", "May": "MAYO", "June": "JUNIO", "July": "JULIO", "August": "AGOSTO", "September": "SEPTIEMBRE", "October": "OCTUBRE", "November": "NOVIEMBRE", "December": "DICIEMBRE"}
    fecha_dt = datetime.now()
    mes_es = meses.get(fecha_dt.strftime('%B'), "FEBRERO")
    fecha_espanol = f"{fecha_dt.strftime('%d')} DE {mes_es} DE {fecha_dt.year}"

    # --- QR y Sellos ---
    qr = qrcode.QRCode(version=1, box_size=10, border=0)
    qr.add_data(url_sat)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    qr_io = io.BytesIO()
    img_qr.save(qr_io, format='PNG')
    qr_io.seek(0)

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    if os.path.exists(image_path):
        pdf.image(image_path, x=0, y=0, w=210, h=297)

    # --- BLOQUE SUPERIOR (Ya validado por ti) ---
    pdf.image(qr_io, x=12, y=51, w=33)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(58, 51.5)
    pdf.cell(0, 5, rfc_usuario)
    
    # Intento de NOMBRE en Cédula (con red de seguridad)
    pdf.set_xy(58, 64)
    nom = datos.get('Nombre (s)', '')
    pa = datos.get('Primer Apellido', '')
    sa = datos.get('Segundo Apellido', '')
    nombre_full = f"{nom} {pa} {sa}".strip().upper()
    if not nombre_full: nombre_full = "VERIFICAR DATOS EN FORMULARIO"
    pdf.multi_cell(100, 5, nombre_full)
    
    # idCIF: x=69, y=80 (3mm a la izquierda de la anterior y bajado)
    pdf.set_xy(69, 80)
    pdf.cell(0, 5, str(idcif_usuario))

    # Lugar y Fecha (Español)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_xy(118, 70)
    pdf.cell(80, 4, f"CUAUHTEMOC, CIUDAD DE MEXICO, A {fecha_espanol}", align='C')

    # --- BLOQUE DE IDENTIFICACIÓN (BASADO EN TU MAPEO DE PÍXELES) ---
    pdf.set_font("Helvetica", "", 8)
    
    # 1. RFC (Coords: 987, 1255 px -> y=105 approx)
    pdf.set_xy(82, 105.5)
    pdf.cell(0, 5, rfc_usuario)
    
    # 2. CURP (Coords: 995, 1357 px -> y=114 approx)
    pdf.set_xy(82, 114)
    pdf.cell(0, 5, datos.get('CURP', ''))
    
    # 3. Nombre(s) (Calculado proporcionalmente)
    pdf.set_xy(82, 122.5)
    pdf.cell(0, 5, nom.upper())
    
    # 4. Primer Apellido (Coords: 981, 1559 px -> y=131 approx)
    pdf.set_xy(82, 131)
    pdf.cell(0, 5, pa.upper())
    
    # 5. Segundo Apellido (Coords: 995, 1645 px -> y=138 approx)
    pdf.set_xy(82, 138.5)
    pdf.cell(0, 5, sa.upper())
    
    # 6. Fecha inicio de operaciones (Coords: 995, 1730 px -> y=145 approx)
    pdf.set_xy(82, 145.5)
    pdf.cell(0, 5, datos.get('Fecha inicio de operaciones', '').upper())
    
    # 7. Estatus del padrón (Coords: 981, 1831 px -> y=154 approx)
    pdf.set_xy(82, 154)
    pdf.cell(0, 5, datos.get('Estatus en el padrón', 'ACTIVO').upper())
    
    # 8. Fecha de último cambio de estado (Calculado)
    pdf.set_xy(82, 162.5)
    pdf.cell(0, 5, datos.get('Fecha de último cambio de estado', '').upper())

    # --- SELLOS FINALES ---
    pdf.set_font("Helvetica", "", 5)
    pdf.set_xy(65, 258)
    # Cadena y sello omitidos para brevedad pero deben ir aquí según código previo
    
    output = io.BytesIO()
    output.write(pdf.output())
    output.seek(0)
    return output
    
