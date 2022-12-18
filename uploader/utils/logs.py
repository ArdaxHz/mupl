import logging
from datetime import date
from pathlib import Path

root_path = Path(".")


def format_log_dir_path():
    log_folder_path = root_path.joinpath("logs")
    log_folder_path.mkdir(parents=True, exist_ok=True)
    return log_folder_path


log_folder_path = format_log_dir_path()


def setup_logs(
        logger_name: str = "md_uploader",
        path: Path = log_folder_path,
        logger_filename: str = "md_uploader",
):
    if logger_name == "md_uploader":
        add_to = ""
    else:
        add_to = f"{logger_name}_"
    filename = f"{logger_filename}_{add_to}{str(date.today())}.log"

    logs_path = path.joinpath(filename)
    fileh = logging.FileHandler(logs_path, "a")
    formatter = logging.Formatter(
        "%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"
    )
    fileh.setFormatter(formatter)

    log = logging.getLogger(logger_name)  # root logger
    # for hdlr in log.handlers[:]:  # remove all old handlers
    #     if isinstance(hdlr, logging.FileHandler):
    #         log.removeHandler(hdlr)
    log.addHandler(fileh)
    log.setLevel(logging.DEBUG)


setup_logs()
