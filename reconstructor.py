from fpdf import FPDF
import qrcode
import io
import hashlib
import base64
from datetime import datetime

def generar_constancia_pdf(datos, rfc_usuario, idcif_usuario, url_sat):
    # Lógica de Sello (SAT oficial usa Pipe ||)
    fecha_iso = datetime.now().strftime("%Y/%m/%d")
    cadena = f"||{fecha_iso}|{rfc_usuario}|CONSTANCIA DE SITUACIÓN FISCAL|{idcif_usuario}||"
    sello = base64.b64encode(hashlib.sha256(cadena.encode()).digest()).decode('utf-8')

    # QR - Ajustado para que quepa en el recuadro blanco de la Cédula
    qr_img = qrcode.make(url_sat)
    qr_io = io.BytesIO()
    qr_img.save(qr_io, format='PNG')
    qr_io.seek(0)

    pdf = FPDF()
    pdf.add_page()
    
    # 1. CARGAMOS TU PLANTILLA (Debe llamarse plantilla.jpg en tu carpeta)
    try:
        pdf.image('plantilla.jpg', x=0, y=0, w=210, h=297)
    except:
        pass # Si no existe, al menos escribirá los datos

    # 2. SECCIÓN: CÉDULA DE IDENTIFICACIÓN FISCAL (Superior Izquierda)
    pdf.image(qr_io, x=11, y=28, w=35) # QR en su lugar
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(48, 31)
    pdf.cell(0, 5, rfc_usuario) # RFC en Cédula
    
    pdf.set_xy(48, 41)
    nombre_full = f"{datos.get('Nombre', '')} {datos.get('Apellido Paterno', '')} {datos.get('Apellido Materno', '')}"
    pdf.set_font("Helvetica", "B", 8)
    pdf.multi_cell(55, 3.5, nombre_full.upper()) # Nombre en Cédula
    
    pdf.set_xy(48, 55)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, f"idCIF: {idcif_usuario}") # idCIF en Cédula

    # 3. LUGAR Y FECHA DE EMISIÓN (Derecha)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_xy(105, 41)
    fecha_txt = f"CUAUHTEMOC, CIUDAD DE MEXICO, A {datetime.now().strftime('%d DE %B DE %Y').upper()}"
    pdf.cell(95, 4, fecha_txt, align='C')

    # 4. TABLA: DATOS DE IDENTIFICACIÓN
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(40, 71)
    pdf.cell(0, 5, rfc_usuario) # RFC Tabla
    pdf.set_xy(40, 76.5)
    pdf.cell(0, 5, datos.get('CURP', '')) # CURP Tabla
    pdf.set_xy(40, 82)
    pdf.cell(0, 5, datos.get('Nombre', '')) # Nombre Tabla
    pdf.set_xy(40, 93)
    pdf.cell(0, 5, datos.get('Situación del contribuyente', 'ACTIVO')) # Estatus

    # 5. TABLA: DOMICILIO (Mapeado a los campos de la captura)
    pdf.set_xy(40, 115)
    pdf.cell(40, 5, datos.get('CP', '')) # CP
    pdf.set_xy(135, 115)
    pdf.cell(0, 5, datos.get('Tipo de vialidad', '')) # Vialidad
    
    pdf.set_xy(40, 120.5)
    pdf.cell(0, 5, datos.get('Nombre de la vialidad', '')) # Nombre Vialidad
    
    pdf.set_xy(40, 131)
    pdf.cell(50, 5, datos.get('Colonia', '')) # Colonia
    pdf.set_xy(135, 131)
    pdf.cell(0, 5, datos.get('Municipio o delegación', '')) # Municipio

    # 6. SELLOS FINALES
    pdf.set_font("Helvetica", "", 5)
    pdf.set_xy(65, 258) # Posición de la cadena original
    pdf.multi_cell(130, 2.5, cadena)
    
    pdf.set_xy(65, 265) # Posición del sello digital
    pdf.multi_cell(130, 2, sello + sello)

    output = io.BytesIO()
    output.write(pdf.output())
    output.seek(0)
    return output
    
