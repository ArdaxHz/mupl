import os
import subprocess

def setup():
    # Verificar se os módulos estão instalados
    required_modules = [
        'requests',
        'natsort',
        'Pillow',
        'tqdm',
        'asyncio',
        'packaging',
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
            
    os.system('cls')

