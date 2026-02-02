import os
from fpdf import FPDF
import qrcode
import io
import hashlib
import base64
from datetime import datetime

def generar_constancia_pdf(datos, rfc_usuario, idcif_usuario, url_sat):
    # 1. Rutas y Preparación de Sellos
    base_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(base_dir, 'plantilla.png')

    fecha_emision = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    # Cadena Original con formato SAT (Pipes)
    cadena = f"||{fecha_emision}|{rfc_usuario}|CONSTANCIA DE SITUACIÓN FISCAL|{idcif_usuario}||"
    sello = base64.b64encode(hashlib.sha256(cadena.encode()).digest()).decode('utf-8')

    # 2. Generar Código QR (Optimizado para el recuadro)
    qr = qrcode.QRCode(version=1, box_size=10, border=0)
    qr.add_data(url_sat)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    qr_io = io.BytesIO()
    img_qr.save(qr_io, format='PNG')
    qr_io.seek(0)

    # 3. Configuración del Documento
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # Fondo de Plantilla
    if os.path.exists(image_path):
        pdf.image(image_path, x=0, y=0, w=210, h=297)

    # --- BLOQUE A: CÉDULA DE IDENTIFICACIÓN (EL ANCLA) ---
    # Posicionamiento exacto del QR
    pdf.image(qr_io, x=13.5, y=38.5, w=32)
    
    # RFC al lado del QR
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(49, 40)
    pdf.cell(0, 5, rfc_usuario)
    
    # Nombre Completo
    pdf.set_xy(49, 50)
    nombre_full = f"{datos.get('Nombre (s)', '')} {datos.get('Primer Apellido', '')} {datos.get('Segundo Apellido', '')}".strip()
    pdf.set_font("Helvetica", "B", 8)
    pdf.multi_cell(55, 3.5, nombre_full.upper())
    
    # idCIF
    pdf.set_xy(49, 64)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, f"idCIF: {idcif_usuario}")

    # --- BLOQUE B: LUGAR Y FECHA ---
    pdf.set_font("Helvetica", "", 7)
    pdf.set_xy(110, 48)
    fecha_txt = f"CUAUHTEMOC, CIUDAD DE MEXICO, A {datetime.now().strftime('%d DE %B DE %Y').upper()}"
    pdf.cell(90, 4, fecha_txt, align='C')

    # --- BLOQUE C: TABLA DE IDENTIFICACIÓN (AJUSTE BAJO) ---
    pdf.set_font("Helvetica", "", 8)
    
    # RFC
    pdf.set_xy(43, 83.5)
    pdf.cell(0, 5, rfc_usuario)
    
    # CURP
    pdf.set_xy(43, 89.2)
    pdf.cell(0, 5, datos.get('CURP', ''))
    
    # Nombre (s)
    pdf.set_xy(43, 94.8)
    pdf.cell(0, 5, datos.get('Nombre (s)', '').upper())
    
    # Primer Apellido
    pdf.set_xy(43, 100.5)
    pdf.cell(0, 5, datos.get('Primer Apellido', '').upper())
    
    # Segundo Apellido
    pdf.set_xy(43, 106.2)
    pdf.cell(0, 5, datos.get('Segundo Apellido', '').upper())
    
    # Fecha Inicio de Operaciones
    pdf.set_xy(43, 111.8)
    pdf.cell(0, 5, datos.get('Fecha inicio de operaciones', '').upper())
    
    # Estatus en el Padrón
    pdf.set_xy(43, 117.5)
    pdf.cell(0, 5, datos.get('Estatus en el padrón', 'ACTIVO').upper())
    
    # Fecha de último cambio de estado
    pdf.set_xy(43, 123.2)
    pdf.cell(0, 5, datos.get('Fecha de último cambio de estado', datos.get('Fecha del último cambio de situación', '')).upper())

    # --- BLOQUE D: DATOS DEL DOMICILIO ---
    # (Bajamos estas coordenadas para que sigan la lógica de la tabla de arriba)
    pdf.set_xy(43, 147.5) 
    pdf.cell(40, 5, datos.get('Código Postal', ''))
    pdf.set_xy(135, 147.5) 
    pdf.cell(0, 5, datos.get('Tipo de Vialidad', ''))
    
    pdf.set_xy(43, 153.2)
    pdf.cell(0, 5, datos.get('Nombre de Vialidad', ''))
    pdf.set_xy(135, 153.2)
    pdf.cell(0, 5, datos.get('Número Exterior', ''))

    # --- BLOQUE E: SELLOS DE VALIDACIÓN ---
    pdf.set_font("Helvetica", "", 5)
    pdf.set_xy(65, 258)
    pdf.multi_cell(130, 2.5, cadena)
    
    pdf.set_xy(65, 266)
    pdf.multi_cell(130, 2, sello)

    # 4. Finalizar y Retornar
    output = io.BytesIO()
    output.write(pdf.output())
    output.seek(0)
    return output
    
