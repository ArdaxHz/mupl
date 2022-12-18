from .config import open_config_file
from .languages import languages
from .logs import setup_logs, root_path

config = open_config_file(root_path)
