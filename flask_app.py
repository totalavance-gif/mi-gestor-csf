from flask import Flask, request, send_file, render_template, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import urllib3
import ssl
import io
import hashlib
import base64
from datetime import datetime
from fpdf import FPDF
import qrcode

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

class SSLAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        ctx.check_hostname = False
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

        # Scraping - Usando el bypass móvil que ya funcionó
        val_url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
        session = requests.Session()
        session.mount('https://', SSLAdapter())
        res = session.get(val_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20, verify=False)

        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # Extraemos los datos de la tabla
            d = {cols[0].text.strip().replace(':', ''): cols[1].text.strip() 
                 for row in soup.find_all('tr') if (cols := row.find_all('td'))}

            # Lógica de Validación (Cadena y Sello)
            fecha_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            cadena = f"||{rfc}|{idcif}|{fecha_iso}||"
            sello = base64.b64encode(hashlib.sha256(cadena.encode()).digest()).decode('utf-8')

            # Generar QR en memoria
            qr_img = qrcode.make(val_url)
            qr_io = io.BytesIO()
            qr_img.save(qr_io, format='PNG')
            qr_io.seek(0)

            # --- DIBUJAR PDF ---
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "CONSTANCIA DE SITUACIÓN FISCAL", ln=True, align='C')
            
            # Posicionar QR y Datos principales
            pdf.image(qr_io, x=10, y=30, w=35)
            pdf.set_xy(50, 35)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"RFC: {rfc}", ln=True)
            pdf.set_x(50)
            nombre_completo = f"{d.get('Nombre', '')} {d.get('Apellido Paterno', '')} {d.get('Apellido Materno', '')}"
            pdf.multi_cell(0, 6, f"NOMBRE: {nombre_completo}")

            # Tabla de Datos
            pdf.ln(20)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(0, 8, " IDENTIFICACIÓN DEL CONTRIBUYENTE", ln=True, fill=True)
            pdf.set_font("Helvetica", "", 9)
            
            for k, v in d.items():
                if k not in ['Nombre', 'Apellido Paterno', 'Apellido Materno']:
                    pdf.set_font("Helvetica", "B", 8)
                    pdf.cell(50, 5, f"{k}:", border='B')
                    pdf.set_font("Helvetica", "", 8)
                    pdf.cell(0, 5, f" {v}", border='B', ln=True)

            # Sección de Sello
            pdf.ln(10)
            pdf.set_font("Helvetica", "B", 7)
            pdf.cell(0, 4, "Cadena Original:", ln=True)
            pdf.set_font("Helvetica", "", 6)
            pdf.multi_cell(0, 3, cadena)
            pdf.set_font("Helvetica", "B", 7)
            pdf.cell(0, 4, "Sello Digital:", ln=True)
            pdf.set_font("Helvetica", "", 6)
            pdf.multi_cell(0, 3, sello)

            pdf_out = io.BytesIO()
            pdf_out.write(pdf.output())
            pdf_out.seek(0)
            return send_file(pdf_out, mimetype='application/pdf', as_attachment=True, download_name=f"CSF_{rfc}.pdf")

        return jsonify({"message": "Error al extraer datos del SAT"}), 502
    except Exception as e:
        return jsonify({"message": f"Servidor falló: {str(e)}"}), 500
            
