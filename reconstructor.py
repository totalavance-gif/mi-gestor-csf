from fpdf import FPDF
import qrcode
from io import BytesIO

def generar_constancia_pdf(datos, rfc_usuario, idcif_usuario, url_sat):
    # 1. Configuración del PDF (A4)
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # Intentar cargar la plantilla
    try:
        pdf.image('plantilla.jpg', x=0, y=0, w=210, h=297)
    except:
        pass # Si no hay plantilla, genera el texto sobre blanco para pruebas

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)

    # --- BLOQUE: IDENTIFICACIÓN ---
    # RFC
    pdf.set_xy(82, 108.8) 
    pdf.cell(0, 5, str(rfc_usuario).upper())
    
    # CURP
    pdf.set_xy(82, 117.5)
    pdf.cell(0, 5, str(datos.get('CURP', '')).upper())
    
    # Nombre Completo
    nombre_completo = f"{datos.get('Nombre (s)', '')} {datos.get('Primer Apellido', '')} {datos.get('Segundo Apellido', '')}"
    pdf.set_xy(82, 126.2)
    pdf.cell(0, 5, nombre_completo.strip().upper())

    # --- BLOQUE: DOMICILIO (Coordenadas ajustadas para centrar en cuadros) ---
    # Bajamos Y para que no choque con las líneas superiores
    
    pdf.set_xy(43, 192.2) # Código Postal
    pdf.cell(40, 5, str(datos.get('Código Postal', '06300')))
    
    pdf.set_xy(135, 192.2) # Tipo de Vialidad
    pdf.cell(0, 5, str(datos.get('Tipo de Vialidad', 'CALLE')))
    
    pdf.set_xy(43, 199.5) # Nombre de Vialidad (Calle)
    pdf.cell(0, 5, str(datos.get('Nombre de Vialidad', 'AV. HIDALGO')))
    
    pdf.set_xy(135, 199.5) # Número Exterior
    pdf.cell(0, 5, str(datos.get('Número Exterior', '77')))
    
    pdf.set_xy(43, 207.2) # Nombre de la Colonia
    pdf.cell(0, 5, str(datos.get('Nombre de la Colonia', 'GUERRERO')))
    
    pdf.set_xy(135, 215.2) # Municipio o Demarcación
    pdf.cell(0, 5, str(datos.get('Nombre del Municipio o Demarcación Territorial', 'CUAUHTEMOC')))
    
    pdf.set_xy(43, 222.8) # Entidad Federativa
    pdf.cell(0, 5, str(datos.get('Nombre de la Entidad Federativa', 'CIUDAD DE MEXICO')))

    # --- GENERACIÓN DE QR OFICIAL ---
    qr = qrcode.QRCode(version=1, box_size=10, border=0)
    qr.add_data(url_sat)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    qr_buffer = BytesIO()
    img_qr.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    # Posición oficial del QR del SAT
    pdf.image(qr_buffer, x=16, y=246, w=34, h=34)

    # Retornar como Stream para Flask
    pdf_output = BytesIO()
    pdf_output.write(pdf.output(dest='S').encode('latin-1'))
    pdf_output.seek(0)
    
    return pdf_output
    
