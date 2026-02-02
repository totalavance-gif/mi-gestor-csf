from fpdf import FPDF
import qrcode
import io
import hashlib
import base64
from datetime import datetime

def generar_constancia_pdf(datos, rfc_usuario, idcif_usuario, url_sat):
    # 1. Metadatos de Validación
    fecha_actual = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    lugar_fecha = f"CUAUHTEMOC, CIUDAD DE MEXICO, A {datetime.now().strftime('%d DE %B DE %Y').upper()}"
    
    # Cadena Original estilo SAT
    cadena = f"||{fecha_actual}|{rfc_usuario}|CONSTANCIA DE SITUACIÓN FISCAL|{idcif_usuario}||"
    sello = base64.b64encode(hashlib.sha256(cadena.encode()).digest()).decode('utf-8')[:120]

    # 2. Crear QR
    qr_img = qrcode.make(url_sat)
    qr_io = io.BytesIO()
    qr_img.save(qr_io, format='PNG')
    qr_io.seek(0)

    # 3. Iniciar PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # --- ENCABEZADO ---
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(100, 5, "Hacienda", ln=0)
    pdf.cell(0, 5, "SAT", ln=1, align='R')
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(100, 4, "Secretaría de Hacienda y Crédito Público", ln=0)
    pdf.cell(0, 4, "SERVICIO DE ADMINISTRACIÓN TRIBUTARIA", ln=1, align='R')
    
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "CONSTANCIA DE SITUACIÓN FISCAL", ln=True, align='C')
    pdf.ln(2)

    # --- CÉDULA DE IDENTIFICACIÓN (CUADRO QR) ---
    # Dibujar marco de la cédula
    curr_y = pdf.get_y()
    pdf.rect(10, curr_y, 190, 50) 
    
    pdf.image(qr_io, x=12, y=curr_y + 2, w=40)
    
    pdf.set_xy(55, curr_y + 5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 6, rfc_usuario, ln=True)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_x(55)
    pdf.cell(0, 4, "Registro Federal de Contribuyentes", ln=True)
    
    pdf.ln(3)
    pdf.set_x(55)
    pdf.set_font("Helvetica", "B", 10)
    nombre_full = f"{datos.get('Nombre', datos.get('Nombre (s)', ''))} {datos.get('Apellido Paterno', '')} {datos.get('Apellido Materno', '')}".strip()
    pdf.multi_cell(0, 5, nombre_full.upper())
    pdf.set_x(55)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 4, "Nombre, denominación o razón social", ln=True)
    
    pdf.ln(4)
    pdf.set_x(55)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 5, f"idCIF: {idcif_usuario}", ln=True)

    # --- LUGAR Y FECHA DE EMISIÓN ---
    pdf.set_xy(10, curr_y + 52)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(40, 5, "Lugar y Fecha de Emisión:")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 5, lugar_fecha, ln=True)
    pdf.ln(5)

    # --- TABLA: DATOS DE IDENTIFICACIÓN ---
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, " Datos de Identificación del Contribuyente", ln=True, fill=True)
    
    def agregar_fila(label, valor):
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(60, 5, f"{label}:", border='B')
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(0, 5, f" {valor}", border='B', ln=True)

    agregar_fila("RFC", rfc_usuario)
    agregar_fila("CURP", datos.get('CURP', ''))
    agregar_fila("Estatus en el padrón", datos.get('Situación del contribuyente', 'ACTIVO'))
    agregar_fila("Fecha de último cambio de estado", datos.get('Fecha del último cambio de situación', ''))
    
    pdf.ln(5)

    # --- TABLA: DATOS DEL DOMICILIO ---
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, " Datos del domicilio registrado", ln=True, fill=True)
    
    agregar_fila("Código Postal", datos.get('CP', ''))
    agregar_fila("Nombre de Vialidad", datos.get('Nombre de la vialidad', ''))
    agregar_fila("Número Exterior", datos.get('Número exterior', ''))
    agregar_fila("Número Interior", datos.get('Número interior', ''))
    agregar_fila("Nombre de la Colonia", datos.get('Colonia', ''))
    agregar_fila("Nombre del Municipio", datos.get('Municipio o delegación', ''))
    agregar_fila("Nombre de la Entidad Federativa", datos.get('Entidad Federativa', ''))

    # --- SECCIÓN LEGAL Y SELLOS ---
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 7)
    pdf.multi_cell(0, 3, "Sus datos personales son incorporados y protegidos en los sistemas del SAT, de conformidad con los Lineamientos de Protección de Datos Personales...")
    
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(0, 5, "Cadena Original Sello:", ln=True)
    pdf.set_font("Helvetica", "", 6)
    pdf.multi_cell(0, 3, cadena)
    
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(0, 5, "Sello Digital:", ln=True)
    pdf.set_font("Helvetica", "", 6)
    pdf.multi_cell(0, 3, sello)

    # Pie de página
    pdf.set_y(-20)
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(0, 5, "Página [1] de [1]", align='R')

    # Generar salida
    output = io.BytesIO()
    output.write(pdf.output())
    output.seek(0)
    return output
    
