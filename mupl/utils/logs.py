import logging
from datetime import date, datetime, timedelta
from pathlib import Path


def format_log_dir_path(mupl_path=Path(".")):
    """Create and return the path to the logs directory."""
    log_folder_path = mupl_path.joinpath("logs")
    log_folder_path.mkdir(parents=True, exist_ok=True)
    return log_folder_path


def setup_logs(
    logger_name: "str",
    path: Path,
    logger_filename: "str" = None,
    level: int = 0,
):
    """Set up logging for the specified logger."""
    log_level = logging.INFO if level == 0 else logging.DEBUG

    path.mkdir(exist_ok=True, parents=True)
    if logger_filename is None:
        logger_filename = logger_name

    current_date = date.today()
    filename = f"{logger_filename}_{str(current_date)}.log"

    logs_path = path.joinpath(filename)
    fileh = logging.FileHandler(logs_path, "a", encoding="utf8")
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s"
    )
    fileh.setFormatter(formatter)

    log = logging.getLogger(logger_name)
    log.addHandler(fileh)
    log.setLevel(log_level)

    return log_level <= logging.DEBUG


def clear_old_logs(folder_path: "Path", max_log_days: int = 30):
    """Delete log files older than max_log_days."""
    current_date = date.today()
    last_date_keep_logs = current_date - timedelta(days=max_log_days)

    logger = logging.getLogger("mupl")

    for log_file in folder_path.rglob("*.log"):
        file_date = datetime.fromtimestamp(log_file.stat().st_mtime).date()
        if file_date < last_date_keep_logs:
            logger.debug(f"{log_file.name} is over {max_log_days} days old, deleting.")
            log_file.unlink()
