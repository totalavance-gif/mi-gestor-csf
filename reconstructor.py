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
    
    if os.path.exists(image_path):
        pdf.image(image_path, x=0, y=0, w=210, h=297)

    # --- AJUSTES SEGÚN TU SOLICITUD ---

    # 1. QR: Bajado un poco (y=51)
    pdf.image(qr_io, x=12, y=51, w=33)
    
    # 2. RFC: Movido a la izquierda (x=58)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(58, 51.5)
    pdf.cell(0, 5, rfc_usuario)
    
    # 3. Nombre: Imprime el nombre real del diccionario 'datos'
    pdf.set_xy(58, 63)
    nombre_completo = f"{datos.get('Nombre (s)', '')} {datos.get('Primer Apellido', '')} {datos.get('Segundo Apellido', '')}".strip()
    pdf.set_font("Helvetica", "B", 8)
    pdf.multi_cell(60, 3.5, nombre_completo.upper())
    
    # 4. idCIF: Solo el número y movido a la izquierda (x=60)
    pdf.set_xy(60, 77.5)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, idcif_usuario) # Solo la variable del número

    # --- Lugar y Fecha de Emisión (Sin cambios) ---
    pdf.set_font("Helvetica", "", 7)
    pdf.set_xy(118, 70)
    lugar_fecha = f"CUAUHTEMOC, CIUDAD DE MEXICO, A {datetime.now().strftime('%d DE %B DE %Y').upper()}"
    pdf.cell(80, 4, lugar_fecha, align='C')

    # --- TABLA DE DATOS (Ajuste de alineación base) ---
    pdf.set_font("Helvetica", "", 8)
    # RFC en tabla
    pdf.set_xy(43, 102.5) 
    pdf.cell(0, 5, rfc_usuario)
    # CURP
    pdf.set_xy(43, 108.2)
    pdf.cell(0, 5, datos.get('CURP', ''))
    # Nombre
    pdf.set_xy(43, 113.8)
    pdf.cell(0, 5, datos.get('Nombre (s)', '').upper())
    # Apellidos
    pdf.set_xy(43, 119.5)
    pdf.cell(0, 5, datos.get('Primer Apellido', '').upper())
    pdf.set_xy(43, 125.2)
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
    
