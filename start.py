import os
import tempfile
import subprocess
import requests

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
            if module == 'pywin32':
                __import__('win32api')
            elif module == 'Pillow':
                __import__('PIL')
            else:
                __import__(module)
        except ImportError:
            print(f"Módulo {module} não encontrado. Instalando...")
            subprocess.run(['pip', 'install', module])

    # Limpar o terminal de acordo com o sistema operacional
    os.system('cls' if os.name == 'nt' else 'clear')

def download_and_execute():
    main_py_url = 'https://raw.githubusercontent.com/OneDefauter/mupl/main/main.py'
    main_py_filename = 'main_mupl.py'
    temp_dir = tempfile.gettempdir()
    main_py_path = os.path.join(temp_dir, main_py_filename)
    folder_executed = os.getcwd()

    # Baixar o arquivo main_mupl.py
    try:
        response = requests.get(main_py_url)
        if response.status_code == 200:
            with open(main_py_path, 'wb') as f:
                f.write(response.content)

            command = ['python', main_py_path, folder_executed] if os.name == 'nt' else ['python3', main_py_path, folder_executed]

            # Executar o subprocesso corretamente
            subprocess.run(command)
            
        else:
            if os.path.exists(main_py_path):
                command = ['python', main_py_path, folder_executed] if os.name == 'nt' else ['python3', main_py_path, folder_executed]

                # Executar o subprocesso corretamente
                subprocess.run(command)

    except Exception as e:
        if os.path.exists(main_py_path):
            command = ['python', main_py_path, folder_executed] if os.name == 'nt' else ['python3', main_py_path, folder_executed]

            # Executar o subprocesso corretamente
            subprocess.run(command)
            
        else:
            print(f"Erro durante o download ou execução: {e}")


if __name__ == "__main__":
    install_modules()
    download_and_execute()
