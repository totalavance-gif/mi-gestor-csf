from fpdf import FPDF
import qrcode
from io import BytesIO

def generar_constancia_pdf(datos, rfc_usuario, idcif_usuario, url_sat):
    # 1. Configuración inicial del PDF
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # IMPORTANTE: Debes tener el archivo 'plantilla.jpg' en la misma carpeta
    try:
        pdf.image('plantilla.jpg', x=0, y=0, w=210, h=297)
    except:
        print("Error: No se encontró plantilla.jpg")

    # 2. Configuración de fuente (Helvetica es la más parecida a la del SAT)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(0, 0, 0)

    # --- BLOQUE 1: IDENTIFICACIÓN (Coordenadas bajadas para centrar) ---
    pdf.set_font("Helvetica", "", 8.5)
    
    # RFC
    pdf.set_xy(82, 108.5) 
    pdf.cell(0, 5, str(rfc_usuario).upper())
    
    # CURP
    pdf.set_xy(82, 117.2)
    pdf.cell(0, 5, str(datos.get('CURP', '')).upper())
    
    # Nombre Completo (Unificado)
    nombre_completo = f"{datos.get('Nombre (s)', '')} {datos.get('Primer Apellido', '')} {datos.get('Segundo Apellido', '')}"
    pdf.set_xy(82, 125.5)
    pdf.cell(0, 5, nombre_completo.strip().upper())

    # Fecha de Inicio de Operaciones
    pdf.set_xy(82, 134.5)
    pdf.cell(0, 5, str(datos.get('Fecha inicio de operaciones', '01 DE ENERO DE 2015')))

    # Estatus
    pdf.set_xy(82, 143)
    pdf.cell(0, 5, str(datos.get('Estatus en el padrón', 'ACTIVO')))

    # --- BLOQUE 2: DOMICILIO FISCAL (Ajuste de impacto para que no flote) ---
    # Bajamos la coordenada Y para que el texto caiga DENTRO de los cuadros blancos
    
    pdf.set_xy(43, 191.5) # Código Postal
    pdf.cell(40, 5, str(datos.get('Código Postal', '06300')))
    
    pdf.set_xy(135, 191.5) # Tipo de Vialidad
    pdf.cell(0, 5, str(datos.get('Tipo de Vialidad', 'CALLE')))
    
    pdf.set_xy(43, 198.5) # Nombre de Vialidad (Calle)
    pdf.cell(0, 5, str(datos.get('Nombre de Vialidad', 'AV. HIDALGO')))
    
    pdf.set_xy(135, 198.5) # Número Exterior
    pdf.cell(0, 5, str(datos.get('Número Exterior', '77')))
    
    pdf.set_xy(43, 206.5) # Colonia
    pdf.cell(0, 5, str(datos.get('Nombre de la Colonia', 'GUERRERO')))
    
    pdf.set_xy(135, 214) # Municipio / Alcaldía
    pdf.cell(0, 5, str(datos.get('Nombre del Municipio o Demarcación Territorial', 'CUAUHTEMOC')))
    
    pdf.set_xy(43, 221.5) # Estado
    pdf.cell(0, 5, str(datos.get('Nombre de la Entidad Federativa', 'CIUDAD DE MEXICO')))

    # --- BLOQUE 3: GENERACIÓN DE QR OFICIAL ---
    # Este es el QR que valida la constancia al escanearla
    qr = qrcode.QRCode(version=1, box_size=10, border=0)
    qr.add_data(url_sat)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    # Guardar QR en memoria
    qr_buffer = BytesIO()
    img_qr.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    # Insertar QR en la posición oficial (esquina inferior izquierda)
    pdf.image(qr_buffer, x=15, y=245, w=35, h=35)

    # 4. Retornar el PDF como un stream de bytes para Flask
    pdf_output = BytesIO()
    pdf_output.write(pdf.output(dest='S').encode('latin-1'))
    pdf_output.seek(0)
    
    return pdf_output
    
