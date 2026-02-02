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

    # Datos de validación
    fecha_emision = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    cadena = f"||{fecha_emision}|{rfc_usuario}|CONSTANCIA DE SITUACIÓN FISCAL|{idcif_usuario}||"
    sello = base64.b64encode(hashlib.sha256(cadena.encode()).digest()).decode('utf-8')

    qr = qrcode.QRCode(box_size=10, border=0)
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

    # --- 1. CÉDULA SUPERIOR ---
    pdf.image(qr_io, x=13, y=36, w=33)
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

    # --- 3. TABLA: DATOS DE IDENTIFICACIÓN (BAJAMOS COORDENADAS) ---
    pdf.set_font("Helvetica", "", 8)
    
    # RFC
    pdf.set_xy(43, 83.5) 
    pdf.cell(0, 5, rfc_usuario)
    
    # CURP
    pdf.set_xy(43, 89.2) 
    pdf.cell(0, 5, datos.get('CURP', ''))
    
    # Nombre(s)
    pdf.set_xy(43, 94.8) 
    pdf.cell(0, 5, datos.get('Nombre (s)', '').upper())
    
    # Primer Apellido
    pdf.set_xy(43, 100.5) 
    pdf.cell(0, 5, datos.get('Primer Apellido', '').upper())
    
    # Segundo Apellido
    pdf.set_xy(43, 106.2) 
    pdf.cell(0, 5, datos.get('Segundo Apellido', '').upper())
    
    # Fecha Inicio Operaciones
    pdf.set_xy(43, 111.8) 
    pdf.cell(0, 5, datos.get('Fecha inicio de operaciones', '').upper())
    
    # Estatus en el Padrón
    pdf.set_xy(43, 117.5) 
    pdf.cell(0, 5, datos.get('Estatus en el padrón', 'ACTIVO'))
    
    # Fecha de último cambio de estado
    pdf.set_xy(43, 123.2) 
    pdf.cell(0, 5, datos.get('Fecha de último cambio de estado', datos.get('Fecha del último cambio de situación', '')))

    # --- 4. TABLA: DOMICILIO (AJUSTE DE ALTURA) ---
    pdf.set_xy(43, 147.5) # CP
    pdf.cell(40, 5, datos.get('Código Postal', ''))
    pdf.set_xy(135, 147.5) # Tipo Vialidad
    pdf.cell(0, 5, datos.get('Tipo de Vialidad', ''))
    
    pdf.set_xy(43, 153) # Nombre Vialidad
    pdf.cell(0, 5, datos.get('Nombre de Vialidad', ''))
    pdf.set_xy(135, 153) # Num Exterior
    pdf.cell(0, 5, datos.get('Número Exterior', ''))

    # --- 5. SELLOS ---
    pdf.set_font("Helvetica", "", 5)
    pdf.set_xy(65, 258)
    pdf.multi_cell(130, 2.5, cadena)
    pdf.set_xy(65, 266)
    pdf.multi_cell(130, 2, sello)

    output = io.BytesIO()
    output.write(pdf.output())
    output.seek(0)
    return output
    
