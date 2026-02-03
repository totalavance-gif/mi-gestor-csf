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

    # --- Validación y Sellos ---
    fecha_emision = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    cadena = f"||{fecha_emision}|{rfc_usuario}|CONSTANCIA DE SITUACIÓN FISCAL|{idcif_usuario}||"
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
    
    # 1. Primero colocamos la plantilla de fondo
    if os.path.exists(image_path):
        pdf.image(image_path, x=0, y=0, w=210, h=297)

    # --- AJUSTES FINALES ---

    # QR: Se queda en la posición que ya te gustó
    pdf.image(qr_io, x=12, y=51, w=33)
    
    # RFC: Se queda en la posición que ya te gustó
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(58, 51.5)
    pdf.cell(0, 5, rfc_usuario)
    
    # NOMBRE: Ajuste de posición y visibilidad
    # Lo moví ligeramente para asegurar que no choque con etiquetas de la plantilla
    pdf.set_xy(58, 65) 
    nombre_completo = f"{datos.get('Nombre (s)', '')} {datos.get('Primer Apellido', '')} {datos.get('Segundo Apellido', '')}".strip()
    pdf.set_font("Helvetica", "B", 8)
    # Usamos multi_cell por si el nombre es largo, pero con x=58 para alinear
    pdf.multi_cell(80, 4, nombre_completo.upper())
    
    # idCIF: Bajado un poco y movido a la derecha (x=72, y=79)
    pdf.set_xy(72, 79)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, str(idcif_usuario)) 

    # Lugar y Fecha de Emisión: Sin cambios (y=70)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_xy(118, 70)
    # Forzamos la fecha a ser igual a la de tu captura exitosa
    fecha_txt = f"CUAUHTEMOC, CIUDAD DE MEXICO, A {datetime.now().strftime('%d DE %B DE %Y').upper()}"
    pdf.cell(80, 4, fecha_txt, align='C')

    # --- TABLA DE DATOS DE IDENTIFICACIÓN ---
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
    
