from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import urllib3
import ssl
import io
# Importamos tu función del reconstructor.py
from reconstructor import generar_constancia_pdf

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

# Bypass de Seguridad SSL para el SAT
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

        # URL del validador móvil del SAT
        validador_url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
        
        session = requests.Session()
        session.mount('https://', SSLAdapter())
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        response = session.get(validador_url, headers=headers, timeout=20, verify=False)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            datos_raw = {}
            
            for row in soup.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) >= 2:
                    llave = cols[0].text.strip().replace(':', '').replace('.', '')
                    valor = cols[1].text.strip()
                    datos_raw[llave] = valor

            # --- LÓGICA PARA SEPARAR APELLIDOS SI VIENEN JUNTOS ---
            nombre_completo_sat = datos_raw.get('Nombre (s)', datos_raw.get('Nombre', '')).strip()
            p_apellido = datos_raw.get('Primer Apellido', '')
            s_apellido = datos_raw.get('Segundo Apellido', '')

            # Si el SAT mandó el nombre completo en un solo campo y los apellidos están vacíos:
            if nombre_completo_sat and not p_apellido:
                partes = nombre_completo_sat.split()
                if len(partes) >= 3:
                    # Ejemplo: "KAREN LOPEZ PEREZ" -> Nombre: KAREN, P: LOPEZ, S: PEREZ
                    nombre_final = " ".join(partes[:-2])
                    p_apellido = partes[-2]
                    s_apellido = partes[-1]
                elif len(partes) == 2:
                    nombre_final = partes[0]
                    p_apellido = partes[1]
                else:
                    nombre_final = nombre_completo_sat
            else:
                nombre_final = nombre_completo_sat

            # --- NORMALIZACIÓN PARA EL RECONSTRUCTOR ---
            datos_finales = {
                "Nombre (s)": nombre_final.upper(),
                "Primer Apellido": p_apellido.upper(),
                "Segundo Apellido": s_apellido.upper(),
                "CURP": datos_raw.get('CURP', ''),
                "Fecha inicio de operaciones": datos_raw.get('Fecha inicio de operaciones', '01 DE ENERO DE 2015'),
                "Estatus en el padrón": datos_raw.get('Estatus en el padrón', 'ACTIVO'),
                "Fecha de último cambio de estado": datos_raw.get('Fecha de último cambio de estado', '01 DE ENERO DE 2015'),
                
                # Domicilio Automatizado (Se llena solo si el SAT no lo da)
                "Código Postal": datos_raw.get('Código Postal', '06300'),
                "Tipo de Vialidad": datos_raw.get('Tipo de Vialidad', 'CALLE'),
                "Nombre de Vialidad": datos_raw.get('Nombre de Vialidad', 'AV. HIDALGO'),
                "Número Exterior": datos_raw.get('Número Exterior', '77'),
                "Nombre de la Colonia": datos_raw.get('Nombre de la Colonia', 'GUERRERO'),
                "Nombre del Municipio o Demarcación Territorial": datos_raw.get('Nombre del Municipio o Demarcación Territorial', 'CUAUHTEMOC'),
                "Nombre de la Entidad Federativa": datos_raw.get('Nombre de la Entidad Federativa', 'CIUDAD DE MEXICO')
            }

            # Generar el PDF usando el reconstructor
            pdf_stream = generar_constancia_pdf(datos_finales, rfc, idcif, validador_url)
            
            return send_file(
                pdf_stream,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'Constancia_{rfc}.pdf'
            )

        return "El SAT no respondió a la consulta.", 503

    except Exception as e:
        return f"Error en el sistema: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
            
