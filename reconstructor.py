from fpdf import FPDF
import qrcode
import io
import hashlib
import base64
from datetime import datetime

def generar_constancia_pdf(datos, rfc_usuario, idcif_usuario, url_sat):
    # 1. Generar Metadatos de Validación
    fecha_emision = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    # Cadena Original Estándar
    cadena = f"||{rfc_usuario}|{idcif_usuario}|{fecha_emision}|{datos.get('Situación del contribuyente', 'ACTIVO')}||"
    # Sello Digital (Hash SHA256 en Base64)
    sello = base64.b64encode(hashlib.sha256(cadena.encode()).digest()).decode('utf-8')

    # 2. Crear Código QR en Memoria
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(url_sat)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    qr_buffer = io.BytesIO()
    img_qr.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)

    # 3. Construir el PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado (Simulación oficial)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "CONSTANCIA DE SITUACIÓN FISCAL", ln=True, align='C')
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "SERVICIO DE ADMINISTRACIÓN TRIBUTARIA", ln=True, align='C')
    pdf.ln(10)

    # Bloque de Identificación con QR
    pdf.image(qr_buffer, x=10, y=35, w=40)
    pdf.set_xy(55, 35)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, f"RFC: {rfc_usuario}", ln=True)
    pdf.set_x(55)
    pdf.cell(0, 7, f"CURP: {datos.get('CURP', 'N/A')}", ln=True)
    pdf.set_x(55)
    nombre = f"{datos.get('Nombre', '')} {datos.get('Apellido Paterno', '')} {datos.get('Apellido Materno', '')}"
    pdf.multi_cell(0, 7, f"NOMBRE: {nombre}")

    # Tabla de Datos Fiscales
    pdf.set_xy(10, 85)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 8, " INFORMACIÓN ADICIONAL DEL CONTRIBUYENTE", ln=True, fill=True)
    
    pdf.set_font("Helvetica", "", 9)
    # Filtramos para no repetir datos ya puestos arriba
    excluir = ['Nombre', 'Apellido Paterno', 'Apellido Materno', 'CURP', 'RFC']
    for k, v in datos.items():
        if k not in excluir:
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(60, 6, f"{k}:", border='B')
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 6, f" {v}", border='B', ln=True)

    # Bloque de Validación Final (Cadena y Sello)
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(0, 5, "Cadena Original:", ln=True)
    pdf.set_font("Helvetica", "", 7)
    pdf.multi_cell(0, 4, cadena)
    
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(0, 5, "Sello Digital:", ln=True)
    pdf.set_font("Helvetica", "", 7)
    pdf.multi_cell(0, 4, sello)

    # Pie de página
    pdf.set_y(-20)
    pdf.set_font("Helvetica", "I", 7)
    pdf.cell(0, 10, f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - Validación oficial vía SIAT", align='C')

    # Retornar como objeto binario
    output = io.BytesIO()
    output.write(pdf.output())
    output.seek(0)
    return output
        
