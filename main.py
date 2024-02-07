import os
import sys
import json
import subprocess

folder_executed = sys.argv[1]

def install_modules():
    required_modules = [
        'requests',
        'natsort',
        'Pillow',
        'tqdm',
        'asyncio',
        'packaging',
        'flask',
    ]
    
    for module in required_modules:
        try:
            if module == 'Pillow':
                __import__('PIL')
            
            else:
                __import__(module)
                
        except ImportError:
            subprocess.run(['pip', 'install', module])
            
    os.system('cls') if os.name == 'nt' else os.system('clear')
install_modules()

import requests


temp_folder = os.environ['TEMP']
app_folder = os.path.join(temp_folder, "MangaDex Uploader (APP)")
path = os.path.join(temp_folder, "MangaDex Uploader (APP)", "run.py")
config_path = os.path.join(app_folder, 'config.json')
map_path_file = os.path.join(app_folder, 'name_id_map.json')

os.makedirs(app_folder, exist_ok=True)
os.makedirs(os.path.join(app_folder, "to_upload"), exist_ok=True)
os.makedirs(os.path.join(app_folder, "uploaded"), exist_ok=True)


folders = ['logs', 'static', 'templates', 'mupl\\http', 'mupl\\loc', 'mupl\\uploader', 'mupl\\utils']

for x in folders:
    x = os.path.join(app_folder, x)
    os.makedirs(x, exist_ok=True)

context_1 = 'https://raw.githubusercontent.com/OneDefauter/mupl/main'
context_2 = 'https://raw.githubusercontent.com/OneDefauter/mupl/main/mupl'
context_3 = 'https://raw.githubusercontent.com/OneDefauter/mupl/main/mupl/http'
context_4 = 'https://raw.githubusercontent.com/OneDefauter/mupl/main/mupl/loc'
context_5 = 'https://raw.githubusercontent.com/OneDefauter/mupl/main/mupl/uploader'
context_6 = 'https://raw.githubusercontent.com/OneDefauter/mupl/main/mupl/utils'
context_7 = 'https://raw.githubusercontent.com/OneDefauter/mupl/main/static'
context_8 = 'https://raw.githubusercontent.com/OneDefauter/mupl/main/templates'


urls_1 = {
    'mupl.py':f'{context_1}/mupl.py',
    'run.py':f'{context_1}/run.py'
}

urls_2 = {
    '__init__.py':f'{context_2}/__init__.py',
    'file_validator.py':f'{context_2}/file_validator.py',
    'image_validator.py':f'{context_2}/image_validator.py'
}

urls_3 = {
    '__init__.py':f'{context_3}/__init__.py',
    'client.py':f'{context_3}/client.py',
    'model.py':f'{context_3}/model.py',
    'oauth.py':f'{context_3}/oauth.py',
    'response.py':f'{context_3}/response.py'
}

urls_4 = {
    'en.json':f'{context_4}/en.json',
    'pt-br.json':f'{context_4}/pt-br.json'
}

urls_5 = {
    '__init__.py':f'{context_5}/__init__.py',
    'handler.py':f'{context_5}/handler.py',
    'uploader.py':f'{context_5}/uploader.py'
}

urls_6 = {
    '__init__.py':f'{context_6}/__init__.py',
    'config.py':f'{context_6}/config.py',
    'defaults.json':f'{context_6}/defaults.json',
    'logs.py':f'{context_6}/logs.py'
}

urls_7 = {
    'icon.ico':f'{context_7}/icon.ico',
    'style.css':f'{context_7}/style.css',
    'en.json':f'{context_7}/en.json',
    'pt-br.json':f'{context_7}/pt-br.json'
}

urls_8 = {
    'index.html':f'{context_8}/index.html',
    'login.html':f'{context_8}/login.html',
    'main.html':f'{context_8}/main.html'
}



def download_files(url_dict, folder_path):
    for filename, url in url_dict.items():
        file_path = os.path.join(folder_path, filename)
        response = requests.get(url)
        
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                file.write(response.content)
            print(f"Download: '{filename}'.")
        else:
            print(f"Error: '{filename}'. Code: {response.status_code}")


# Download 'mupl'
download_files(urls_1, app_folder)

# Download 'mupl/mupl'
download_files(urls_2, os.path.join(app_folder, 'mupl'))

# Download 'mupl/mupl/http'
download_files(urls_3, os.path.join(app_folder, 'mupl', 'http'))

# Download 'mupl/mupl/loc'
download_files(urls_4, os.path.join(app_folder, 'mupl', 'loc'))

# Download 'mupl/mupl/uploader'
download_files(urls_5, os.path.join(app_folder, 'mupl', 'uploader'))

# Download 'mupl/mupl/utils'
download_files(urls_6, os.path.join(app_folder, 'mupl', 'utils'))

# Download 'static'
download_files(urls_7, os.path.join(app_folder, 'static'))

# Download 'templates'
download_files(urls_8, os.path.join(app_folder, 'templates'))

if not os.path.exists(map_path_file):
    download_files({'name_id_map.json':f'{context_1}/name_id_map.json'}, app_folder)

if not os.path.exists(os.path.join(app_folder, "static", "background.mp4")):
    download_files({'background.mp4':f'{context_7}/background.mp4'}, os.path.join(app_folder, 'static'))

def create_config_file(uploads_folder, uploaded_files):
    config_structure = {
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
            "uploads_folder": uploads_folder,
            "uploaded_files": uploaded_files,
            "mangadex_api_url": "https://api.mangadex.org",
            "mangadex_auth_url": "https://auth.mangadex.org/realms/mangadex/protocol/openid-connect",
            "mdauth_path": ".mdauth"
        }
    }

    # Create the config.json file
    with open(config_path, 'w', encoding='utf-8') as file:
        json.dump(config_structure, file, indent=4)

def check_config_paths():
    uploads_folder = os.path.join(folder_executed, 'to_upload')
    uploaded_files = os.path.join(folder_executed, 'uploaded')
    
    os.makedirs(uploads_folder, exist_ok=True)
    os.makedirs(uploaded_files, exist_ok=True)
    
    if not os.path.exists(config_path):
        create_config_file(uploads_folder, uploaded_files)

    with open(config_path, 'r', encoding='utf-8') as file:
        config = json.load(file)

        if config['paths']['uploads_folder'] != uploads_folder:
            config['paths']['uploads_folder'] = uploads_folder

        if config['paths']['uploaded_files'] != uploaded_files:
            config['paths']['uploaded_files'] = uploaded_files

        config['paths']['uploads_folder'] = os.path.abspath(config['paths']['uploads_folder'])
        config['paths']['uploaded_files'] = os.path.abspath(config['paths']['uploaded_files'])

    # Update the config.json file if there are modifications
    with open(config_path, 'w', encoding='utf-8') as file:
        json.dump(config, file, indent=4)

check_config_paths()

os.chdir(app_folder)


command = ['python', path, folder_executed] if os.name == 'nt' else ['python3', path, folder_executed]
subprocess.run(command)
