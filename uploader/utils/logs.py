import logging
from datetime import date, datetime, timedelta
from pathlib import Path

from uploader.utils.config import MAX_LOG_DAYS, root_path


def format_log_dir_path():
    log_folder_path = root_path.joinpath("logs")
    log_folder_path.mkdir(parents=True, exist_ok=True)
    return log_folder_path


log_folder_path = format_log_dir_path()


def setup_logs(
    logger_name: "str",
    path: Path = log_folder_path,
    logger_filename: "str" = None,
):
    path.mkdir(exist_ok=True, parents=True)
    if logger_filename is None:
        logger_filename = logger_name

    filename = f"{logger_filename}_{str(current_date)}.log"

    logs_path = path.joinpath(filename)
    fileh = logging.FileHandler(logs_path, "a")
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s"
    )
    fileh.setFormatter(formatter)

    log = logging.getLogger(logger_name)  # root logger
    # for hdlr in log.handlers[:]:  # remove all old handlers
    #     if isinstance(hdlr, logging.FileHandler):
    #         log.removeHandler(hdlr)
    log.addHandler(fileh)
    log.setLevel(logging.DEBUG)


current_date = date.today()
last_date_keep_logs = current_date - timedelta(days=MAX_LOG_DAYS)


setup_logs(
    logger_name="md_uploader",
    path=log_folder_path,
    logger_filename="md_uploader",
)

_logger = logging.getLogger("md_uploader")


def clear_old_logs(folder_path: "Path"):
    for log_file in folder_path.rglob("*.log"):
        file_date = datetime.fromtimestamp(log_file.stat().st_mtime).date()
        if file_date < last_date_keep_logs:
            _logger.debug(f"{log_file.name} is over {MAX_LOG_DAYS} days old, deleting.")
            log_file.unlink()


clear_old_logs(log_folder_path)
