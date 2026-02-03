from flask import Flask, render_template, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
import ssl
import urllib3
from reconstructor import generar_constancia_pdf

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
app = Flask(__name__)

# Adaptador SSL simplificado para evitar el error de cifrado
class SimpleSSL(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extraer', methods=['POST'])
def extraer():
    try:
        rfc = request.form.get('rfc', '').upper().strip()
        idcif = request.form.get('idcif', '').strip()
        url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
        
        session = requests.Session()
        session.mount('https://', SimpleSSL())
        
        # Petición directa y rápida
        r = session.get(url, timeout=10, verify=False)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Algoritmo de raspado por encima: toma pares de celdas
        datos = {}
        for fila in soup.find_all('tr'):
            celdas = fila.find_all('td')
            if len(celdas) >= 2:
                # Limpiamos puntos y espacios de las etiquetas
                label = celdas[0].get_text(strip=True).replace(':', '')
                valor = celdas[1].get_text(strip=True)
                datos[label] = valor

        if not datos:
            return jsonify({"status": "vacio", "msg": "No se leyeron datos. Revisa RFC/idCIF."})

        return jsonify({
            "status": "success",
            "datos": datos,
            "rfc": rfc,
            "idcif": idcif
        })
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

@app.route('/descargar', methods=['POST'])
def descargar():
    # Esta ruta recibe los datos finales para el PDF
    info = request.form.to_dict()
    pdf = generar_constancia_pdf(info, info.get('rfc'), info.get('idcif'), "URL_VAL")
    return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name="CSF.pdf")
    
