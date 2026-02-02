from flask import Flask, request, send_file, render_template
from fpdf import FPDF
import io
from bs4 import BeautifulSoup
import requests
import ssl

app = Flask(__name__)

# Reutilizamos el adaptador SSL que ya sabemos que funciona para entrar al SAT
class SSLAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = ctx
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generar', methods=['POST'])
def generar():
    try:
        rfc = request.form.get('rfc', '').upper().strip()
        idcif = request.form.get('idcif', '').strip()

        # 1. Extracción de datos (Lo que ya lograste hacer)
        validador_url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
        session = requests.Session()
        session.mount('https://', SSLAdapter())
        res = session.get(validador_url, timeout=20, verify=False)
        
        soup = BeautifulSoup(res.text, 'html.parser')
        datos = {cols[0].text.strip(): cols[1].text.strip() for row in soup.find_all('tr') if (cols := row.find_all('td'))}

        if not datos:
            return "No se encontraron datos", 404

        # 2. Creación del PDF con los datos obtenidos
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Constancia de Situación Fiscal (Resumen)", ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", "", 12)
        for clave, valor in datos.items():
            pdf.set_font("Arial", "B", 11)
            pdf.cell(50, 8, f"{clave}", border=0)
            pdf.set_font("Arial", "", 11)
            pdf.cell(0, 8, f": {valor}", border=0, ln=True)
        
        pdf.ln(20)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 10, "Documento generado mediante validación de código QR oficial del SAT.", align='C')

        # 3. Enviar el PDF al usuario
        pdf_output = io.BytesIO()
        pdf_output.write(pdf.output())
        pdf_output.seek(0)

        return send_file(
            pdf_output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"CSF_{rfc}.pdf"
        )

    except Exception as e:
        return str(e), 500
        
