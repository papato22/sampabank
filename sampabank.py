import qrcode
from io import BytesIO
from flask import Flask, request, jsonify
import requests
import logging
import threading
import time

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

def gerar_pagamento_sampabank(valor, token, tempo):
    url = "https://api.sampabank.com/api/pix/gerar/"
    valor_centavos = int(valor * 100)
    payload = {
        "amount": valor_centavos, 
        "time": tempo 
    }

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    logging.debug(f"Enviando requisição para a URL: {url}")
    logging.debug(f"Payload: {payload}")
    logging.debug(f"Headers: {headers}")

    response = requests.post(url, json=payload, headers=headers)

    logging.debug(f"Status Code: {response.status_code}")
    logging.debug(f"Resposta: {response.text}")

    if response.status_code == 200:
        return response.json(), None
    else:
        return None, response.json()

def cancelar_pagamento_automatico(token, trxid, delay):
    time.sleep(delay * 60)
    url_cancelamento = "https://api.sampabank.com/api/pix/cancelar/"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "trxid": trxid
    }

    response = requests.post(url_cancelamento, json=payload, headers=headers)
    logging.debug(f"Cancelamento automático executado após {delay} minuto(s).")
    logging.debug(f"Status do Cancelamento: {response.status_code}")
    logging.debug(f"Resposta do Cancelamento: {response.text}")

@app.route('/gerar_pagamento', methods=['GET'])
def gerar_pagamento():
    token = request.args.get('accessToken')
    valor = request.args.get('value', type=float)
    tempo = request.args.get('time', type=int)
    if valor is None or token is None or tempo is None:
        return jsonify({"erro": "Parâmetros 'value', 'accessToken' e 'time' são obrigatórios"}), 400
    resultado, erro = gerar_pagamento_sampabank(valor, token, tempo)

    if erro:
        return jsonify({"erro": erro}), 500 
    qr_image = qrcode.make(resultado['copiaecola'])
    qr_image_file = BytesIO()
    qr_image.save(qr_image_file, format='PNG')
    qr_image_file.seek(0)

    qr_code_base64 = qr_image_file.getvalue().hex()
    threading.Thread(target=cancelar_pagamento_automatico, args=(token, resultado['id'], tempo)).start()
    return jsonify({
        "mensagem": "Pagamento gerado com sucesso",
        "qr_code_base64": qr_code_base64,  
        "id_pix": resultado.get('id'),  
        "copiaecola": resultado.get('copiaecola') 
    })
if __name__ == '__main__':
    app.run(debug=True)
