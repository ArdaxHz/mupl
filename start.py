import os
import tempfile
import subprocess

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

    # Clear the terminal according to the operating system
    os.system('cls' if os.name == 'nt' else 'clear')

def download_and_execute():
    main_py_url = 'https://raw.githubusercontent.com/OneDefauter/mupl/main/main.py'
    main_py_filename = 'main_mupl.py'
    temp_dir = tempfile.gettempdir()
    main_py_path = os.path.join(temp_dir, main_py_filename)
    folder_executed = os.getcwd()

    # Download the main_mupl.py file
    try:
        response = requests.get(main_py_url)
        if response.status_code == 200:
            with open(main_py_path, 'wb') as f:
                f.write(response.content)

            command = ['python', main_py_path, folder_executed] if os.name == 'nt' else ['python3', main_py_path, folder_executed]

            # Execute the subprocess correctly
            subprocess.run(command)
            
        else:
            if os.path.exists(main_py_path):
                command = ['python', main_py_path, folder_executed] if os.name == 'nt' else ['python3', main_py_path, folder_executed]

                # Execute the subprocess correctly
                subprocess.run(command)

    except Exception as e:
        if os.path.exists(main_py_path):
            command = ['python', main_py_path, folder_executed] if os.name == 'nt' else ['python3', main_py_path, folder_executed]

            # Execute the subprocess correctly
            subprocess.run(command)
            
        else:
            print(f"Error during download or execution: {e}")


if __name__ == "__main__":
    install_modules()
    import requests
    download_and_execute()
