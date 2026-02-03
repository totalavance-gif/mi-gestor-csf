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
    meses = {
        "January": "ENERO", "February": "FEBRERO", "March": "MARZO", 
        "April": "ABRIL", "May": "MAYO", "June": "JUNIO", 
        "July": "JULIO", "August": "AGOSTO", "September": "SEPTIEMBRE", 
        "October": "OCTUBRE", "November": "NOVIEMBRE", "December": "DICIEMBRE"
    }
    fecha_dt = datetime.now()
    mes_es = meses.get(fecha_dt.strftime('%B'), "FEBRERO")
    fecha_espanol = f"{fecha_dt.strftime('%d')} DE {mes_es} DE {fecha_dt.year}"

    # --- QR ---
    qr = qrcode.QRCode(version=1, box_size=10, border=0)
    qr.add_data(url_sat)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    qr_io = io.BytesIO()
    img_qr.save(qr_io, format='PNG')
    qr_io.seek(0)

    # Inicializar PDF
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    if os.path.exists(image_path):
        pdf.image(image_path, x=0, y=0, w=210, h=297)

    # --- 1. BLOQUE CÉDULA ---
    pdf.image(qr_io, x=12, y=51, w=33)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(58, 51.5)
    pdf.cell(0, 5, str(rfc_usuario))
    
    # Nombre en Cédula (Usando "Nombre (s)" del JSON)
    pdf.set_xy(58, 64)
    nom = str(datos.get('Nombre (s)', '')).upper()
    pa = str(datos.get('Primer Apellido', '')).upper()
    sa = str(datos.get('Segundo Apellido', '')).upper()
    nombre_completo = f"{nom} {pa} {sa}".strip()
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.multi_cell(100, 4, nombre_completo if nombre_completo else "CONTRIBUYENTE")
    
    # idCIF
    pdf.set_xy(69, 80)
    pdf.cell(0, 5, str(idcif_usuario))

    # Lugar y Fecha
    pdf.set_font("Helvetica", "", 7)
    pdf.set_xy(118, 70)
    pdf.cell(80, 4, f"CUAUHTEMOC, CIUDAD DE MEXICO, A {fecha_espanol}", align='C')

    # --- 2. TABLA DE IDENTIFICACIÓN ---
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(82, 107) # RFC
    pdf.cell(0, 5, str(rfc_usuario))
    pdf.set_xy(82, 116) # CURP
    pdf.cell(0, 5, str(datos.get('CURP', '')).upper())
    pdf.set_xy(82, 122.5) # Nombre
    pdf.cell(0, 5, nom)
    pdf.set_xy(82, 131) # Apellido 1
    pdf.cell(0, 5, pa)
    pdf.set_xy(82, 138.5) # Apellido 2
    pdf.cell(0, 5, sa)
    pdf.set_xy(82, 145.5) # Inicio Op
    pdf.cell(0, 5, str(datos.get('Fecha inicio de operaciones', '01 DE ENERO DE 2015')))
    pdf.set_xy(82, 156) # Estatus
    pdf.cell(0, 5, str(datos.get('Estatus en el padrón', 'ACTIVO')))

    # --- 3. DOMICILIO (Datos del JSON) ---
    pdf.set_xy(43, 185) # CP
    pdf.cell(40, 5, str(datos.get('Código Postal', '06300')))
    pdf.set_xy(135, 185) # Tipo Vialidad
    pdf.cell(0, 5, str(datos.get('Tipo de Vialidad', 'CALLE')))
    pdf.set_xy(43, 191) # Calle
    pdf.cell(0, 5, str(datos.get('Nombre de Vialidad', 'AV. HIDALGO')))
    pdf.set_xy(135, 191) # Num Ext
    pdf.cell(0, 5, str(datos.get('Número Exterior', '77')))
    pdf.set_xy(43, 202) # Colonia
    pdf.cell(0, 5, str(datos.get('Nombre de la Colonia', 'GUERRERO')))
    pdf.set_xy(135, 208) # Municipio
    pdf.cell(0, 5, str(datos.get('Nombre del Municipio o Demarcación Territorial', 'CUAUHTEMOC')))
    pdf.set_xy(43, 214) # Estado
    pdf.cell(0, 5, str(datos.get('Nombre de la Entidad Federativa', 'CIUDAD DE MEXICO')))

    # --- 4. SELLOS FINALES ---
    pdf.set_font("Helvetica", "", 5)
    cadena_original = f"||{fecha_dt.strftime('%Y/%m/%d')}|{rfc_usuario}|CONSTANCIA|{idcif_usuario}||"
    sello_digital = base64.b64encode(hashlib.sha256(cadena_original.encode()).digest()).decode('utf-8')
    pdf.set_xy(65, 258)
    pdf.multi_cell(130, 2.5, cadena_original)
    pdf.set_xy(65, 266)
    pdf.multi_cell(130, 2, sello_digital)

    # Retorno compatible con Vercel
    pdf_output = io.BytesIO()
    pdf_output.write(pdf.output())
    pdf_output.seek(0)
    return pdf_output
    
