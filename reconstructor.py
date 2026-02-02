from fpdf import FPDF
import qrcode
import io
import hashlib
import base64
from datetime import datetime

def generar_constancia_pdf(datos, rfc_usuario, idcif_usuario, url_sat):
    # Generación de la Cadena Original según el estándar del SAT
    fecha_consulta = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    [span_11](start_span)cadena = f"||{fecha_consulta}|{rfc_usuario}|CONSTANCIA DE SITUACIÓN FISCAL|{idcif_usuario}||"[span_11](end_span)
    sello = base64.b64encode(hashlib.sha256(cadena.encode()).digest()).decode('utf-8')

    # Crear el nuevo QR dinámico
    qr = qrcode.QRCode(box_size=10, border=0)
    qr.add_data(url_sat)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    qr_io = io.BytesIO()
    img_qr.save(qr_io, format='PNG')
    qr_io.seek(0)

    pdf = FPDF()
    pdf.add_page()
    
    # 1. Fondo: Tu plantilla limpia (debe llamarse plantilla.png)
    pdf.image('plantilla.png', x=0, y=0, w=210, h=297)

    # 2. Encimar el QR Nuevo (Coordenada exacta del recuadro de tu imagen)
    [span_12](start_span)pdf.image(qr_io, x=12, y=26, w=35)[span_12](end_span)

    # 3. Datos de la Cédula (Lado derecho del QR)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(48, 32)
    [span_13](start_span)pdf.cell(0, 5, rfc_usuario)[span_13](end_span)
    
    pdf.set_xy(48, 42)
    nombre_completo = f"{datos.get('Nombre (s)', '')} {datos.get('Primer Apellido', '')} {datos.get('Segundo Apellido', '')}".strip()
    pdf.set_font("Helvetica", "B", 8)
    [span_14](start_span)pdf.multi_cell(50, 4, nombre_completo.upper())[span_14](end_span)
    
    pdf.set_xy(48, 55)
    [span_15](start_span)pdf.cell(0, 5, f"idCIF: {idcif_usuario}")[span_15](end_span)

    # 4. Lugar y Fecha de Emisión
    pdf.set_font("Helvetica", "", 7)
    pdf.set_xy(110, 42)
    lugar_fecha = f"CUAUHTEMOC, CIUDAD DE MEXICO, A {datetime.now().strftime('%d DE %B DE %Y').upper()}"
    [span_16](start_span)pdf.cell(90, 4, lugar_fecha, align='C')[span_16](end_span)

    # 5. Llenado de Tabla: Identificación (Ajuste a tus renglones)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(42, 71)
    [span_17](start_span)pdf.cell(0, 5, rfc_usuario)[span_17](end_span)
    pdf.set_xy(42, 76.5)
    [span_18](start_span)pdf.cell(0, 5, datos.get('CURP', ''))[span_18](end_span)
    pdf.set_xy(42, 82)
    [span_19](start_span)pdf.cell(0, 5, datos.get('Nombre (s)', ''))[span_19](end_span)
    pdf.set_xy(42, 101)
    [span_20](start_span)pdf.cell(0, 5, datos.get('Estatus en el padrón', 'ACTIVO'))[span_20](end_span)

    # 6. Llenado de Tabla: Domicilio
    pdf.set_xy(42, 126)
    [span_21](start_span)pdf.cell(0, 5, datos.get('CP', ''))[span_21](end_span)
    pdf.set_xy(140, 126)
    [span_22](start_span)pdf.cell(0, 5, datos.get('Tipo de Vialidad', ''))[span_22](end_span)
    
    # 7. Sellos de Validación (Parte inferior)
    pdf.set_font("Helvetica", "", 5)
    pdf.set_xy(65, 258)
    [span_23](start_span)pdf.multi_cell(130, 2.5, cadena)[span_23](end_span)
    pdf.set_xy(65, 266)
    [span_24](start_span)pdf.multi_cell(130, 2, sello)[span_24](end_span)

    output = io.BytesIO()
    output.write(pdf.output())
    output.seek(0)
    return output
    
