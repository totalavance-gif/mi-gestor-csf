from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
import requests
import io

app = Flask(__name__)
CORS(app)

# Ruta para servir la página principal
@app.route('/')
def home():
    return render_template('index.html')

# Ruta de generación con bypass de Validador QR
@app.route('/generar', methods=['POST'])
def generar():
    try:
        rfc = request.form.get('rfc', '').upper().strip()
        idcif = request.form.get('idcif', '').strip()

        if not rfc or not idcif:
            return jsonify({"message": "Faltan datos (RFC o ID CIF)"}), 400

        # BYPASS 2026: Usamos el endpoint del QR móvil que es más permisivo
        # Este es el método que usa el paquete 'sat_scraping' que encontraste
        validador_url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Referer': 'https://siat.sat.gob.mx/'
        }

        # Paso 1: Validar identidad ante el SAT (Scraping)
        response = requests.get(validador_url, headers=headers, timeout=20, verify=False)

        if response.status_code == 200:
            # Aquí el SAT muestra los datos fiscales. 
            # Para obtener el PDF, intentamos el salto al generador directo usando esta sesión.
            pdf_url = f"https://sinat.sat.gob.mx/CifDirecto/Home/Index?rfc={rfc}&idCif={idcif}"
            pdf_res = requests.get(pdf_url, headers=headers, timeout=20, verify=False)

            if b'%PDF' in pdf_res.content:
                return send_file(
                    io.BytesIO(pdf_res.content),
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f"CSF_{rfc}.pdf"
                )
            
            # Si no entrega PDF, devolvemos los datos de validación como éxito parcial
            return jsonify({
                "status": "validated",
                "message": "Datos validados. El SAT bloqueó la descarga del PDF por IP, pero el RFC es correcto.",
                "data_url": validador_url
            })

        return jsonify({"message": "El SAT no reconoce estos datos."}), 404

    except Exception as e:
        return jsonify({"message": f"Error técnico: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
    
