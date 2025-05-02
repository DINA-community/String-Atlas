'''function for common tasks'''
import os
import glob
from typing import Optional
import yaml
from loguru import logger



ENCODING = "utf-8"

class LogStyle:
    """Logger for the String-Atlas repository using loguru, with readable module info."""

    def __init__(self, config: str = "not provided", setting: str = "default",
                 module_name: Optional[str] = "UNKNOWN", file_name: Optional[str] = "UNKNOWN"):
        """
        Initializes Loguru logger with optional config file and a manual module name for clarity.
        """
        self.module_name = module_name
        self.file_name = file_name
        self.logger = logger.bind(module_name=module_name,
                                  file_name=file_name)

        if config == "not provided":
            filename = "configPoC.yaml"
            path = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(path, filename)
            try:
                with open(config_path, "r", encoding=ENCODING) as stream:
                    config_data = yaml.safe_load(stream)['logger']
                    self._custom_format(config_data, setting)
            except FileNotFoundError as e:
                self._default()
                self.logger.warning(f"{e}. Using default settings.")
            except Exception as e:
                self._default()
                self.logger.warning(f"Unexpected error: {e}. Using default settings.")
        elif not config.endswith(".yaml"):
            self._default()
            self.logger.info(f"No access to config file '{config}'. Using default settings.")
        else:
            self._custom_format(config, setting)

    def _default(self):
        self.logger.remove()

        self.logger.add("logs/default.log",
                        format="{time} {level} "
                        "File_name: {extra[file_name]} "
                        "Class: {extra[module_name]} "
                        "Function: {function} Line:{line}"
                        " {message}",
                        level="INFO")

        self.logger.add("logs/warning.log",
                        filter=lambda record: record["level"].name in ["WARNING", "ERROR"],
                        format=("{time} {level} "
                                "File_name: {extra[file_name]} "
                                "Class: {extra[module_name]} "
                                "Function:{function} Line:{line}"
                                " {message}"))

    def _custom_format(self, config, setting:str):
        """
        Args:
            loaded config file and corresponding setting in it
        To prevent stdout log messages by removing existing loggers first.
        Settings:
        sink/destination: Location of the log file.
        rotation: String representing when new file should be created.
        retention: String representing when a cleanup should be started.
        message: String representing the log message format.
        level: String representing the lowest log level.
        """
        module_config = config[setting]
        base = module_config['basics']
        self.logger.remove()
        self.logger.add(sink= base['log_file'],
                        rotation=base['log_max_file_size'],
                        retention=base['log_retention'],
                        format="{time} {level} "
                               "File_name: {extra[file_name]} "
                               "Class: {extra[module_name]} "
                               "Function: {function} Line:{line}"
                               " {message}",
                               level=base['log_level'])
        self.logger.add(
                        "logs/string-atlas-warning.log",
                        filter=lambda record: record["level"].name in ["WARNING", "ERROR"],
                        rotation=base['log_max_file_size'],
                        retention=base['log_retention'],
                        format="{time} {level} "
                               "File_name: {extra[file_name]} "
                               "Class: {extra[module_name]} "
                               "Function: {function} Line:{line}"
                               " {message}",
                               level=base['log_level'])

def log_test(module:str="unknown", filename:str = "unknown", delete:bool = False):
    """Test the log function. Provide module name like __name__ abd filename as well as if the existing log files shall be removed."""
    if delete:
        path = os.path.join(os.getcwd(), "logs")
        log_files = glob.glob(os.path.join(path, '*.log'), recursive=True)
        for log_file in log_files:
            try:
                os.remove(log_file)
                print(f"Deleted: {log_file}")
            except Exception as e:
                print(f"Failed to delete {log_file}: {e}")

    testlog = LogStyle(module_name=module, file_name=filename).logger    
    testlog.info("test")
    testlog.warning("test")
