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

    # --- Traducción de Fecha a Español ---
    meses = {
        "January": "ENERO", "February": "FEBRERO", "March": "MARZO", 
        "April": "ABRIL", "May": "MAYO", "June": "JUNIO", 
        "July": "JULIO", "August": "AGOSTO", "September": "SEPTIEMBRE", 
        "October": "OCTUBRE", "November": "NOVIEMBRE", "December": "DICIEMBRE"
    }
    fecha_dt = datetime.now()
    mes_es = meses.get(fecha_dt.strftime('%B'), fecha_dt.strftime('%B').upper())
    fecha_espanol = f"{fecha_dt.strftime('%d')} DE {mes_es} DE {fecha_dt.year}"

    # --- Validación y Sellos ---
    fecha_emision_sello = fecha_dt.strftime("%Y/%m/%d %H:%M:%S")
    cadena = f"||{fecha_emision_sello}|{rfc_usuario}|CONSTANCIA DE SITUACIÓN FISCAL|{idcif_usuario}||"
    sello = base64.b64encode(hashlib.sha256(cadena.encode()).digest()).decode('utf-8')

    # --- Generar QR ---
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

    # --- AJUSTES SOLICITADOS ---

    # 1. QR y RFC (Se quedan como estaban, ya confirmaste que están bien)
    pdf.image(qr_io, x=12, y=51, w=33)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(58, 51.5)
    pdf.cell(0, 5, rfc_usuario)
    
    # 2. NOMBRE: Ajuste de área para asegurar que aparezca
    # Lo bajamos a y=64 y damos más ancho (100mm)
    pdf.set_xy(58, 64) 
    nombre_completo = f"{datos.get('Nombre (s)', '')} {datos.get('Primer Apellido', '')} {datos.get('Segundo Apellido', '')}".strip()
    pdf.set_font("Helvetica", "B", 9)
    pdf.multi_cell(100, 5, nombre_completo.upper()) # Aumentamos ancho a 100
    
    # 3. idCIF: 3mm a la izquierda de la posición anterior (antes x=72, ahora x=69)
    # Y lo bajamos un poco más a y=80
    pdf.set_xy(69, 80)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, str(idcif_usuario)) 

    # 4. Lugar y Fecha de Emisión: CORREGIDO A ESPAÑOL
    pdf.set_font("Helvetica", "", 7)
    pdf.set_xy(118, 70)
    texto_lugar = f"CUAUHTEMOC, CIUDAD DE MEXICO, A {fecha_espanol}"
    pdf.cell(80, 4, texto_lugar, align='C')

    # --- RELLENO DE TABLA DE IDENTIFICACIÓN ---
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(43, 102.5) # RFC
    pdf.cell(0, 5, rfc_usuario)
    pdf.set_xy(43, 108.2) # CURP
    pdf.cell(0, 5, datos.get('CURP', ''))
    pdf.set_xy(43, 113.8) # Nombre
    pdf.cell(0, 5, datos.get('Nombre (s)', '').upper())
    pdf.set_xy(43, 119.5) # Primer Apellido
    pdf.cell(0, 5, datos.get('Primer Apellido', '').upper())
    pdf.set_xy(43, 125.2) # Segundo Apellido
    pdf.cell(0, 5, datos.get('Segundo Apellido', '').upper())

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
    
