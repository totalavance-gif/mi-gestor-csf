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

    # Datos de validación para sellos
    fecha_emision = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    cadena = f"||{fecha_emision}|{rfc_usuario}|CONSTANCIA DE SITUACIÓN FISCAL|{idcif_usuario}||"
    sello = base64.b64encode(hashlib.sha256(cadena.encode()).digest()).decode('utf-8')

    # Generar QR dinámico
    qr = qrcode.QRCode(box_size=10, border=0)
    qr.add_data(url_sat)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    qr_io = io.BytesIO()
    img_qr.save(qr_io, format='PNG')
    qr_io.seek(0)

    # Configurar PDF (fpdf2)
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    if os.path.exists(image_path):
        pdf.image(image_path, x=0, y=0, w=210, h=297)

    # --- 1. CÉDULA (EL RECUADRO SUPERIOR) ---
    pdf.image(qr_io, x=13, y=36, w=33) # QR ajustado
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(48, 38)
    pdf.cell(0, 5, rfc_usuario)
    
    pdf.set_xy(48, 48)
    nombre_full = f"{datos.get('Nombre (s)', '')} {datos.get('Primer Apellido', '')} {datos.get('Segundo Apellido', '')}".strip()
    pdf.set_font("Helvetica", "B", 8)
    pdf.multi_cell(55, 3.5, nombre_full.upper())
    
    pdf.set_xy(48, 62)
    pdf.cell(0, 5, f"idCIF: {idcif_usuario}")

    # --- 2. LUGAR Y FECHA ---
    pdf.set_font("Helvetica", "", 7)
    pdf.set_xy(110, 48)
    lugar_fecha = f"CUAUHTEMOC, CIUDAD DE MEXICO, A {datetime.now().strftime('%d DE %B DE %Y').upper()}"
    pdf.cell(90, 4, lugar_fecha, align='C')

    # --- 3. TABLA: DATOS DE IDENTIFICACIÓN ---
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(42, 83) # RFC
    pdf.cell(0, 5, rfc_usuario)
    pdf.set_xy(42, 88.5) # CURP
    pdf.cell(0, 5, datos.get('CURP', ''))
    pdf.set_xy(42, 94) # Nombres
    pdf.cell(0, 5, datos.get('Nombre (s)', ''))
    pdf.set_xy(42, 99.5) # Primer Apellido
    pdf.cell(0, 5, datos.get('Primer Apellido', ''))
    pdf.set_xy(42, 105) # Segundo Apellido
    pdf.cell(0, 5, datos.get('Segundo Apellido', ''))
    pdf.set_xy(42, 110.5) # Fecha Inicio Operaciones
    pdf.cell(0, 5, datos.get('Fecha inicio de operaciones', '25 DE MAYO DE 2012'))
    pdf.set_xy(42, 116) # Estatus
    pdf.cell(0, 5, datos.get('Estatus en el padrón', 'ACTIVO'))

    # --- 4. TABLA: DATOS DEL DOMICILIO ---
    pdf.set_xy(42, 140) # CP
    pdf.cell(40, 5, datos.get('Código Postal', '02300'))
    pdf.set_xy(135, 140) # Tipo Vialidad
    pdf.cell(0, 5, datos.get('Tipo de Vialidad', 'CALLE'))
    
    pdf.set_xy(42, 145.5) # Nombre Vialidad
    pdf.cell(0, 5, datos.get('Nombre de Vialidad', 'PONIENTE 146'))
    pdf.set_xy(135, 145.5) # Num Exterior
    pdf.cell(0, 5, datos.get('Número Exterior', '730'))
    
    pdf.set_xy(42, 156.5) # Colonia
    pdf.cell(40, 5, datos.get('Nombre de la Colonia', 'INDUSTRIAL VALLEJO'))
    pdf.set_xy(135, 156.5) # Municipio
    pdf.cell(0, 5, datos.get('Nombre del Municipio o Demarcación Territorial', 'AZCAPOTZALCO'))

    # --- 5. SELLOS FINALES (AL PIE) ---
    pdf.set_font("Helvetica", "", 5)
    pdf.set_xy(65, 258)
    pdf.multi_cell(130, 2.5, cadena)
    pdf.set_xy(65, 266)
    pdf.multi_cell(130, 2, sello)

    output = io.BytesIO()
    output.write(pdf.output())
    output.seek(0)
    return output
    
