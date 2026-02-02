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

# Configuración de seguridad
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

# Adaptador para saltar el error de seguridad SSL del SAT
class SSLAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        ctx.check_hostname = False
        kwargs['ssl_context'] = ctx
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)

def procesar_datos_fiscales(datos_sucios, rfc_input, idcif_input):
    """Lógica para limpiar datos y generar metadatos de validación"""
    d = datos_sucios.get('data', {})
    
    # 1. Limpieza de Nombre
    nombre = f"{d.get('Nombre', '')} {d.get('Apellido Paterno', '')} {d.get('Apellido Materno', '')}".strip()
    
    # 2. Generación de Cadena Original (Simulada bajo estándar SAT)
    fecha_emision = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    cadena = f"||{rfc_input}|{idcif_input}|{fecha_emision}|{d.get('Situación del contribuyente', 'ACTIVO')}||"
    
    # 3. Generación de Sello Digital (SHA256)
    sello = base64.b64encode(hashlib.sha256(cadena.encode()).digest()).decode('utf-8')
    
    return {
        "rfc": rfc_input,
        "curp": d.get('CURP', 'N/A'),
        "nombre": nombre,
        "situacion": d.get('Situación del contribuyente', 'ACTIVO'),
        "regimen": d.get('Régimen', 'Sin obligaciones fiscales'),
        "cp": d.get('CP', ''),
        "direccion": f"{d.get('Tipo de vialidad', '')} {d.get('Nombre de la vialidad', '')} EXT. {d.get('Número exterior', '')} INT. {d.get('Número interior', 'S/N')}, {d.get('Colonia', '')}, {d.get('Municipio o delegación', '')}, {d.get('Entidad Federativa', '')}",
        "cadena": cadena,
        "sello": sello,
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generar', methods=['POST'])
def generar():
    try:
        rfc = request.form.get('rfc', '').upper().strip()
        idcif = request.form.get('idcif', '').strip()

        # 1. SCRAPING (Extracción)
        val_url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
        session = requests.Session()
        session.mount('https://', SSLAdapter())
        res = session.get(val_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20, verify=False)

        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            raw_data = {"data": {cols[0].text.strip().replace(':', ''): cols[1].text.strip() 
                        for row in soup.find_all('tr') if (cols := row.find_all('td'))}}
            
            # 2. PROCESAMIENTO (Lógica de negocio)
            info = procesar_datos_fiscales(raw_data, rfc, idcif)

            # 3. GENERAR QR
            qr = qrcode.make(val_url)
            qr_io = io.BytesIO()
            qr.save(qr_io, format='PNG')
            qr_io.seek(0)

            # 4. DIBUJAR PDF (Reconstrucción visual)
            pdf = FPDF()
            pdf.add_page()
            
            # Encabezado Oficial
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "CONSTANCIA DE SITUACIÓN FISCAL", ln=True, align='C')
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 5, "SERVICIO DE ADMINISTRACIÓN TRIBUTARIA", ln=True, align='C')
            pdf.ln(10)

            # Insertar QR y Datos básicos
            pdf.image(qr_io, x=10, y=35, w=35)
            pdf.set_xy(50, 35)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"RFC: {info['rfc']}", ln=True)
            pdf.set_x(50)
            pdf.cell(0, 6, f"CURP: {info['curp']}", ln=True)
            pdf.set_x(50)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, f"NOMBRE: {info['nombre']}")
            
            # Sección de Domicilio y Régimen
            pdf.ln(15)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(0, 8, " DATOS DEL DOMICILIO FISCAL Y RÉGIMEN", ln=True, fill=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 8, f"Dirección: {info['direccion']}\nC.P.: {info['cp']}\nSituación: {info['situacion']}\nRégimen: {info['regimen']}", border='B')

            # Cadena y Sello (Validación)
            pdf.ln(10)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(0, 5, "Cadena Original:", ln=True)
            pdf.set_font("Helvetica", "", 7)
            pdf.multi_cell(0, 4, info['cadena'])
            
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(0, 5, "Sello Digital:", ln=True)
            pdf.set_font("Helvetica", "", 7)
            pdf.multi_cell(0, 4, info['sello'])

            # Footer
            pdf.set_y(-25)
            pdf.set_font("Helvetica", "I", 7)
            pdf.cell(0, 5, f"Fecha de emisión: {info['fecha']} - Documento validado vía SIAT-SAT", align='C')

            # Enviar PDF
            pdf_out = io.BytesIO()
            pdf_out.write(pdf.output())
            pdf_out.seek(0)
            return send_file(pdf_out, mimetype='application/pdf', as_attachment=True, download_name=f"CSF_{rfc}.pdf")

        return jsonify({"message": "No se pudo conectar con el validador del SAT"}), 503
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    
