from flask import Flask, request, send_file, render_template
from fpdf import FPDF
import io
from bs4 import BeautifulSoup
import requests
import ssl

app = Flask(__name__)

class SSLAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = ctx
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)

@app.route('/generar', methods=['POST'])
def generar():
    try:
        rfc_user = request.form.get('rfc', '').upper().strip()
        idcif = request.form.get('idcif', '').strip()

        # 1. Extracción de datos (El Bypass que ya funciona)
        validador_url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc_user}"
        session = requests.Session()
        session.mount('https://', SSLAdapter())
        res = session.get(validador_url, timeout=20, verify=False)
        
        soup = BeautifulSoup(res.text, 'html.parser')
        datos = {cols[0].text.strip().replace(':', ''): cols[1].text.strip() for row in soup.find_all('tr') if (cols := row.find_all('td'))}

        if not datos:
            return "No se pudieron obtener los datos para generar el PDF", 404

        # 2. Reconstrucción del PDF (Diseño Constancia)
        pdf = FPDF()
        pdf.add_page()
        
        # Encabezado (Simulando el logo del SAT/Hacienda con texto o podrías subir una imagen a tu repo)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "SECRETARÍA DE HACIENDA Y CRÉDITO PÚBLICO", ln=True, align='L')
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 7, "SERVICIO DE ADMINISTRACIÓN TRIBUTARIA", ln=True, align='L')
        pdf.cell(0, 7, "CONSTANCIA DE SITUACIÓN FISCAL", ln=True, align='C')
        pdf.ln(10)

        # Cuerpo de la Constancia (Formato de tabla de 2 columnas)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 8, "DATOS DE IDENTIFICACIÓN DEL CONTRIBUYENTE", ln=True, fill=True)
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 9)
        for clave, valor in datos.items():
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(60, 7, f"{clave}:", border='B')
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 7, f" {valor}", border='B', ln=True)
        
        pdf.ln(10)
        pdf.set_font("Helvetica", "I", 8)
        pdf.multi_cell(0, 5, "La información contenida en este documento ha sido validada en tiempo real a través del portal oficial del SAT (SIAT) mediante la consulta del ID CIF proporcionado.")

        # 3. Entrega del archivo
        pdf_output = io.BytesIO()
        pdf_output.write(pdf.output())
        pdf_output.seek(0)

        return send_file(
            pdf_output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"Constancia_{rfc_user}.pdf"
        )

    except Exception as e:
        return f"Error al reconstruir la constancia: {str(e)}", 500
        
