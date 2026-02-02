from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
import requests
import io

app = Flask(__name__)
CORS(app)

@app.route('/generar', methods=['POST'])
def generar():
    try:
        rfc = request.form.get('rfc', '').upper().strip()
        idcif = request.form.get('idcif', '').strip()

        # URL del Validador Móvil (La que usa el paquete sat_scraping)
        # Este endpoint es más permisivo que el de escritorio
        validador_url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Referer': 'https://siat.sat.gob.mx/'
        }

        # Intentamos obtener la información fiscal
        response = requests.get(validador_url, headers=headers, timeout=20, verify=False)

        # Si el validador responde, aquí tendrías los datos en HTML.
        # Para bajar el PDF real, a veces el validador ofrece un botón de 'Imprimir'
        if response.status_code == 200:
            # Si el objetivo es solo los DATOS, ya ganamos. 
            # Si el objetivo es el PDF, usamos esta sesión para pedir el archivo.
            return jsonify({
                "status": "success",
                "message": "Enlace de validación activo",
                "url_qr": validador_url
            })
        
        return jsonify({"message": "El validador del SAT no reconoce estos datos."}), 404

    except Exception as e:
        return jsonify({"message": "Error en el bypass de scraping móvil."}), 500
        
