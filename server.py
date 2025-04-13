from flask import Flask, Response

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return "está rodando"


@app.route('/check', methods=['HEAD'])
def check():
    return Response(status=200)


def run_server():
    app.run(host='0.0.0.0', port=5000)
