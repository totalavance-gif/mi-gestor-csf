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

    # --- Traducción de Fecha a Español (Corrección de February) ---
    meses = {
        "January": "ENERO", "February": "FEBRERO", "March": "MARZO", 
        "April": "ABRIL", "May": "MAYO", "June": "JUNIO", 
        "July": "JULIO", "August": "AGOSTO", "September": "SEPTIEMBRE", 
        "October": "OCTUBRE", "November": "NOVIEMBRE", "December": "DICIEMBRE"
    }
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

    # --- 1. BLOQUE CÉDULA (QR, RFC, NOMBRE) ---
    pdf.image(qr_io, x=12, y=51, w=33) # QR ya quedó
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(58, 51.5) # RFC ya quedó
    pdf.cell(0, 5, rfc_usuario)
    
    # NOMBRE (Corrección para que aparezca sí o sí)
    pdf.set_xy(58, 64)
    # Buscamos el nombre en todas las posibles llaves que envía el extractor
    nom_val = datos.get('Nombre (s)', datos.get('Nombre', '')).upper()
    pa_val = datos.get('Primer Apellido', '').upper()
    sa_val = datos.get('Segundo Apellido', '').upper()
    nombre_full = f"{nom_val} {pa_val} {sa_val}".strip()
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.multi_cell(100, 4, nombre_full if nombre_full else "DATOS NO DETECTADOS")
    
    # idCIF: 3mm a la izquierda (x=69) y bajado (y=80)
    pdf.set_xy(69, 80)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, str(idcif_usuario))

    # Lugar y Fecha (Ya quedó, en español)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_xy(118, 70)
    pdf.cell(80, 4, f"CUAUHTEMOC, CIUDAD DE MEXICO, A {fecha_espanol}", align='C')

    # --- 2. BLOQUE IDENTIFICACIÓN (CON TUS AJUSTES DE BAJADA) ---
    pdf.set_font("Helvetica", "", 8)
    
    # RFC (Bajado a 107)
    pdf.set_xy(82, 107)
    pdf.cell(0, 5, rfc_usuario)
    
    # CURP (Bajado a 116)
    pdf.set_xy(82, 116)
    pdf.cell(0, 5, datos.get('CURP', '').upper())
    
    # Nombre(s)
    pdf.set_xy(82, 122.5)
    pdf.cell(0, 5, nom_val)
    
    # Primer Apellido
    pdf.set_xy(82, 131)
    pdf.cell(0, 5, pa_val)
    
    # Segundo Apellido
    pdf.set_xy(82, 138.5)
    pdf.cell(0, 5, sa_val)
    
    # Fecha inicio de operaciones
    pdf.set_xy(82, 145.5)
    pdf.cell(0, 5, datos.get('Fecha inicio de operaciones', '').upper())
    
    # Estatus (Bajado a 156)
    pdf.set_xy(82, 156)
    pdf.cell(0, 5, datos.get('Estatus en el padrón', 'ACTIVO').upper())
    
    # Fecha último cambio
    pdf.set_xy(82, 162.5)
    pdf.cell(0, 5, datos.get('Fecha de último cambio de estado', '').upper())

    # --- 3. DOMICILIO (AUTOMATIZADO) ---
    # Usamos los datos genéricos que configuramos en el app.py
    pdf.set_xy(43, 185) # CP
    pdf.cell(40, 5, datos.get('Código Postal', '06300'))
    pdf.set_xy(135, 185) # Tipo Vialidad
    pdf.cell(0, 5, datos.get('Tipo de Vialidad', 'CALLE'))
    
    pdf.set_xy(43, 191) # Calle
    pdf.cell(0, 5, datos.get('Nombre de Vialidad', 'AV. HIDALGO'))
    pdf.set_xy(135, 191) # Num Ext
    pdf.cell(0, 5, datos.get('Número Exterior', '77'))

    # --- 4. SELLOS ---
    pdf.set_font("Helvetica", "", 5)
    fecha_sello = fecha_dt.strftime("%Y/%m/%d %H:%M:%S")
    cadena = f"||{fecha_sello}|{rfc_usuario}|CONSTANCIA DE SITUACIÓN FISCAL|{idcif_usuario}||"
    sello = base64.b64encode(hashlib.sha256(cadena.encode()).digest()).decode('utf-8')
    
    pdf.set_xy(65, 258)
    pdf.multi_cell(130, 2.5, cadena)
    pdf.set_xy(65, 266)
    pdf.multi_cell(130, 2, sello)

    output = io.BytesIO()
    pdf.output(output)
    output.seek(0)
    return output
    
