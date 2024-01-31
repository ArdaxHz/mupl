import os
import sys
import json
import webbrowser
import subprocess
from flask import Flask, render_template, request, jsonify

folder_executed = sys.argv[1]

app = Flask(__name__)

temp_folder = os.environ['TEMP']
app_folder = os.path.join(temp_folder, "MangaDex Uploader (APP)")
mupl_app = os.path.join(app_folder, "mupl.py")
caminho_arquivo = os.path.join(app_folder, 'name_id_map.json')

default_url = 'http://127.0.0.1:5000'


def load_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {
            "options": {
                "number_of_images_upload": 10,
                "upload_retry": 3,
                "ratelimit_time": 2,
                "max_log_days": 30,
                "group_fallback_id": None,
                "number_threads": 3,
                "language_default": "en"
            },
            "credentials": {
                "mangadex_username": None,
                "mangadex_password": None,
                "client_id": None,
                "client_secret": None
            },
            "paths": {
                "name_id_map_file": "name_id_map.json",
                "uploads_folder": "to_upload",
                "uploaded_files": "uploaded",
                "mangadex_api_url": "https://api.mangadex.org",
                "mangadex_auth_url": "https://auth.mangadex.org/realms/mangadex/protocol/openid-connect",
                "mdauth_path": ".mdauth"
            }
        }

def save_config(config):
    with open('config.json', 'w', encoding='utf-8') as file:
        json.dump(config, file, indent=4, ensure_ascii=False)@app.route("/")


@app.route('/')
def index():
    # Verifique se o arquivo config.json existe
    try:
        with open('config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)

            # Verifique se o arquivo tem credenciais
            if 'credentials' in config and all(config['credentials'].values()):
                # Se tiver credenciais, redirecione para a página principal
                return main_setup()
    except FileNotFoundError:
        pass  # O arquivo config.json ainda não existe

    # Se não houver credenciais, renderize a página de login
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login_credential', methods=['POST'])
def login_credential():
    try:
        # Receba as credenciais do corpo da solicitação
        credentials = request.get_json()

        # Verifique se todas as credenciais estão presentes
        required_fields = ['mangadex_username', 'mangadex_password', 'client_id', 'client_secret', 'languageCode']
        if not all(field in credentials for field in required_fields):
            return jsonify({'error': 'Por favor, forneça todas as credenciais necessárias.'}), 400

        # Carregue a configuração atual
        config = load_config()

        # Atualize as credenciais e o languageCode na configuração
        config['credentials'] = {key: value for key, value in credentials.items() if key != 'languageCode'}
        config['options']['language_default'] = credentials['languageCode']

        # Salve a configuração atualizada
        save_config(config)

        return jsonify({'success': 'Credenciais salvas com sucesso.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/new_login')
def new_login():
    return render_template('index.html')

@app.route('/main_setup')
def main_setup():
    return render_template('main.html')

@app.route('/open_folder1', methods=['POST'])
def open_folder1():
    uploads_folder = os.path.join(app_folder, 'to_upload')
    print(uploads_folder)
    os.startfile(uploads_folder)
    return jsonify({'message': 'Pasta aberta com sucesso!'})

@app.route('/open_folder2', methods=['POST'])
def open_folder2():
    uploaded_files = os.path.join(app_folder, 'uploaded')
    print(uploaded_files)
    os.startfile(uploaded_files)
    return jsonify({'message': 'Pasta aberta com sucesso!'})

@app.route('/open_file', methods=['POST'])
def open_file():
    try:
        subprocess.run(['notepad.exe', caminho_arquivo])
        return jsonify({'message': 'Arquivo aberto com sucesso!'})
    except:
        return

@app.route('/clear_folder1', methods=['POST'])
def clear_folder1():
    uploaded_files = os.path.join(app_folder, 'uploaded')
    
    def limpar_pasta(pasta):
        # Listar todos os itens na pasta
        itens_na_pasta = os.listdir(pasta)
        
        for item in itens_na_pasta:
            caminho_item = os.path.join(pasta, item)
            
            # Verificar se é um diretório
            if os.path.isdir(caminho_item):
                # Verificar se não é a pasta 'uploaded'
                if item != 'uploaded':
                    # Chamar a função recursivamente para limpar o diretório
                    limpar_pasta(caminho_item)
            else:
                # Remover o arquivo
                os.remove(caminho_item)

        # Remover a pasta se não for a pasta principal ('uploaded')
        if pasta != uploaded_files:
            os.rmdir(pasta)

    # Chamar a função para limpar a pasta desejada
    limpar_pasta(uploaded_files)

    return jsonify({'message': 'Pasta limpa com sucesso!'})

@app.route('/start_process', methods=['POST'])
def start_process():
    uploads_folder = os.path.join(folder_executed, 'to_upload')
    uploaded_files = os.path.join(folder_executed, 'uploaded')
    
    try:
        # Verifique a plataforma para usar o comando apropriado
        if sys.platform.startswith('win'):
            command = ['cmd', '/c', 'python', mupl_app]
        else:
            command = ['python3', mupl_app]

        # Execute o subprocesso e aguarde a conclusão
        subprocess.run(command)
        
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar mupl.py: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")
        
    return jsonify({'message': 'Executado!'})



webbrowser.open(default_url)
app.run(debug=False)
