from fpdf import FPDF
import qrcode
import io
import hashlib
import base64
from datetime import datetime

def generar_constancia_pdf(datos, rfc_usuario, idcif_usuario, url_sat):
    # Metadatos de Validación
    fecha_emision = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    cadena = f"||{rfc_usuario}|{idcif_usuario}|{fecha_emision}|{datos.get('Situación del contribuyente', 'ACTIVO')}||"
    sello = base64.b64encode(hashlib.sha256(cadena.encode()).digest()).decode('utf-8')

    # Crear QR
    qr_img = qrcode.make(url_sat)
    qr_io = io.BytesIO()
    qr_img.save(qr_io, format='PNG')
    qr_io.seek(0)

    pdf = FPDF()
    pdf.add_page()
    
    # --- ENCABEZADO ESTILO OFICIAL ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 5, "CÉDULA DE IDENTIFICACIÓN FISCAL", ln=True, align='L')
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 4, "SERVICIO DE ADMINISTRACIÓN TRIBUTARIA", ln=True, align='L')
    pdf.ln(5)

    # --- SECCIÓN SUPERIOR: QR + DATOS IDENTIDAD ---
    # Dibujamos el QR
    pdf.image(qr_io, x=10, y=25, w=45)
    
    # Datos a la derecha del QR
    pdf.set_xy(60, 25)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, f"RFC: {rfc_usuario}", ln=True)
    
    pdf.set_x(60)
    pdf.cell(0, 6, f"idCIF: {idcif_usuario}", ln=True) # <-- Aquí incluimos el idCIF solicitado
    
    pdf.set_x(60)
    pdf.cell(0, 6, f"CURP: {datos.get('CURP', 'N/A')}", ln=True)
    
    pdf.set_x(60)
    pdf.set_font("Helvetica", "B", 9)
    nombre = f"{datos.get('Nombre', '')} {datos.get('Apellido Paterno', '')} {datos.get('Apellido Materno', '')}"
    pdf.multi_cell(0, 5, f"NOMBRE, DENOMINACIÓN O RAZÓN SOCIAL:\n{nombre.upper()}")

    # --- SECCIÓN: DATOS DE UBICACIÓN ---
    pdf.set_xy(10, 75)
    pdf.set_fill_color(200, 200, 200) # Gris oscuro para encabezado
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, " DATOS DEL DOMICILIO", ln=True, fill=True)
    
    pdf.set_font("Helvetica", "", 8)
    # Organizamos en formato de tabla simple
    ubicacion = [
        ("Código Postal", datos.get('CP', '')),
        ("Tipo de Vialidad", datos.get('Tipo de vialidad', '')),
        ("Nombre de Vialidad", datos.get('Nombre de la vialidad', '')),
        ("Número Exterior", datos.get('Número exterior', '')),
        ("Número Interior", datos.get('Número interior', 'S/N')),
        ("Nombre de la Colonia", datos.get('Colonia', '')),
        ("Nombre de la Localidad", datos.get('Municipio o delegación', '')),
        ("Nombre del Municipio", datos.get('Municipio o delegación', '')),
        ("Nombre de la Entidad Federativa", datos.get('Entidad Federativa', ''))
    ]

    for label, valor in ubicacion:
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(50, 5, f"{label}:", border='B')
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(0, 5, f" {valor}", border='B', ln=True)

    # --- SECCIÓN: ACTIVIDADES Y RÉGIMENES ---
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, " ACTIVIDADES ECONÓMICAS Y RÉGIMENES", ln=True, fill=True)
    
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(150, 6, "Régimen", border=1)
    pdf.cell(0, 6, "Fecha Inicio", border=1, ln=True)
    
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(150, 6, datos.get('Régimen', 'Sin obligaciones'), border=1)
    pdf.cell(0, 6, datos.get('Fecha de alta', ''), border=1, ln=True)

    # --- SECCIÓN: SELLO DE VALIDACIÓN ---
    pdf.set_y(-45)
    pdf.set_font("Helvetica", "B", 7)
    pdf.cell(0, 4, "Cadena Original:", ln=True)
    pdf.set_font("Helvetica", "", 6)
    pdf.multi_cell(0, 3, cadena)
    
    pdf.set_font("Helvetica", "B", 7)
    pdf.cell(0, 4, "Sello Digital:", ln=True)
    pdf.set_font("Helvetica", "", 6)
    pdf.multi_cell(0, 3, sello)

    # Pie de página final
    pdf.set_y(-15)
    pdf.set_font("Helvetica", "I", 6)
    pdf.cell(0, 5, f"Esta página es una representación impresa de una Constancia de Situación Fiscal. Fecha de consulta: {datetime.now().strftime('%d/%m/%Y')}", align='C')

    output = io.BytesIO()
    output.write(pdf.output())
    output.seek(0)
    return output
    
