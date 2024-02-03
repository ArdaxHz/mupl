import os
import re
import sys
import platform
import requests
import subprocess
from tkinter import messagebox
from mupl.utils.config import translate_message

# URL do instalador do ImageMagick
url = 'https://github.com/OneDefauter/Menu_/releases/download/Req/ImageMagick-7.1.1-26-Q16-HDRI-x64-dll.exe'

# Versão
required_version = '7.1.1-26'


def verify():
    # Diretório onde procuraremos por pastas relacionadas ao ImageMagick
    program_files_path = r'C:\\Program Files'

    # Prefixo usado para identificar pastas do ImageMagick
    imagick_folder_prefix = 'ImageMagick'

    # Obtém uma lista de todas as pastas em C:\Program Files
    program_files_folders = [folder for folder in os.listdir(program_files_path)
                             if os.path.isdir(os.path.join(program_files_path, folder))]

    # Filtra as pastas que começam com o prefixo 'ImageMagick'
    imagick_folders = [folder for folder in program_files_folders if folder.startswith(imagick_folder_prefix)]

    # Verifica se cada pasta do ImageMagick contém o executável magick.exe
    for imagick_folder in imagick_folders:
        imagick_path = os.path.join(program_files_path, imagick_folder)
        magick_exe_path = os.path.join(imagick_path, 'magick.exe')
        
        # Se o executável magick.exe existir, consideramos o ImageMagick como instalado
        if os.path.isfile(magick_exe_path):
            return True

    # Se nenhum diretório do ImageMagick for encontrado, consideramos o ImageMagick não instalado
    return False


def download():
    messagebox.showinfo(translate_message['img_text_1'], translate_message['img_text_2'])
    
    temp_folder = os.environ['TEMP']
    installer_path = os.path.join(temp_folder, 'ImageMagick-Installer.exe')

    response = requests.get(url)
    with open(installer_path, 'wb') as f:
        f.write(response.content)

    # Instalar o ImageMagick usando subprocess
    subprocess.run([installer_path, '/VERYSILENT', '/SUPPRESSMSGBOXES'])
        
    os.remove(installer_path)
    messagebox.showinfo(translate_message['img_text_3'], translate_message['img_text_4'])
    
    sys.exit()


def get_installed_version():
    # Comando para obter a versão instalada do ImageMagick
    command = 'magick --version'

    try:
        # Executar o comando e capturar a saída
        output = subprocess.check_output(command, shell=True, text=True)

        # Extrair a parte relevante da saída usando expressões regulares
        version_match = re.search(r'Version: ImageMagick (\S+)', output)
        if version_match:
            installed_version_str = version_match.group(1)
            return installed_version_str
        else:
            return None
        
    except subprocess.CalledProcessError:
        # Se o comando falhar, assumimos que o ImageMagick não está instalado
        return None


def version_to_tuple(version_str):
    # Função para converter a versão em uma tupla de números inteiros
    return tuple(map(int, re.findall(r'\d+', version_str)))


def compare_versions(installed_version, required_version):
    # Converter as versões para tuplas de números inteiros
    installed_version_tuple = version_to_tuple(installed_version)
    required_version_tuple = version_to_tuple(required_version)

    # Comparar as versões
    return installed_version_tuple >= required_version_tuple


def setup():
    system = platform.system()
    if system != 'Windows':
        return False
    
    if not verify():
        download()
    
    installed_version = get_installed_version()
    
    if installed_version:
        print(f"{translate_message['img_text_5']} {installed_version}")

        if not compare_versions(installed_version, required_version):
            print(translate_message['img_text_6'])
            download()
    
    return True