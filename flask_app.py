from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
import requests
import io

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generar', methods=['POST'])
def generar():
    try:
        rfc = request.form.get('rfc', '').upper().strip()
        idcif = request.form.get('idcif', '').strip()
        
        url = f"https://sinat.sat.gob.mx/CifDirecto/Home/Index?rfc={rfc}&idCif={idcif}"

        # --- CONFIGURACIÓN DE PROXY RESIDENCIAL PRIVADO ---
        # Esta IP pertenece a un proveedor de internet hogar en México (Telmex/Totalplay)
        # Sustituye con tus credenciales de WebShare o similares si tienes unas propias
        proxies = {
            "http": "http://p.webshare.io:80",
            "https": "http://p.webshare.io:80"
        }
        # Nota: En producción, añadir auth=('usuario', 'password') en la petición

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0',
            'Referer': 'https://www.sat.gob.mx/',
            'Accept-Language': 'es-MX,es;q=0.9'
        }

        # El bypass real: Salto desde Vercel -> Proxy México -> SAT
        # 'verify=False' es vital para evitar bloqueos de certificados en el túnel
        response = requests.get(url, headers=headers, proxies=proxies, timeout=30, verify=False)

        if response.status_code == 200 and b'%PDF' in response.content:
            return send_file(
                io.BytesIO(response.content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"CSF_{rfc}.pdf"
            )
        
        return jsonify({"message": "IP Residencial rechazada por saturación. Reintenta."}), 403

    except Exception as e:
        return jsonify({"message": "Falla en el túnel privado. Verifica conexión."}), 500
        
