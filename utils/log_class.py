'''function for common tasks'''
import os
import yaml
import loguru

ENCODING = "utf-8"


class LogStyle():
    """Logger for the String-Atlas repository using loguru"""

    def __init__(self, config:str="", setting:str="default_plus"):
        """
        Initialization for the logger framework Loguru. 
        """
        self.logger = loguru.logger
        if config.endswith("yaml") is False:
            # call default configuration (in this class)
            self._default()
            self.logger.warning(f"No access possible for the configurations file {config}. "
                                f"Default settings will be used.")
        else:
            if config == "":
                filename = "configPoC.yaml"
                path = os.path.dirname(os.path.abspath(__file__))
                config = os.path.join(path, filename)
            try:
                with open(os.path.join(os.getcwd(), config), "r", encoding=ENCODING) as stream:
                    config = yaml.safe_load(stream)['logger']
                    self._custom_format(config, setting)
            except FileNotFoundError as e:
                self._default()
                self.logger.warning(f"{e}. Use default setting.")
            except Exception as e: # pylint: disable=broad-exception-caught
                self._default()
                self.logger.warning({e})

    def _default(self):
        self.logger.remove()
        self.logger.add("logs/string-atlas-default.log",
                        format="{time} {level} {message} Module: {module}")
        self.logger.add(
            "logs/string-atlas-warning.log",
            filter=lambda record: record["level"].name in ["WARNING", "ERROR"],
            format= "{time} {level} {message} Module: {module} "
                    "Filename:{file.name} Function:{function} Line: {line}"
        )

    def _custom_format(self, config, setting:str):
        """
        Args:
            loaded config file and corresponding setting in it
        To prevent stdout log messages by removing existing loggers first.
        Setttings:
        sink/destination: Location of the log file.
        rotation: String representing when new file should be created.
        retention: String representing when a cleanup should be started.
        message: String representing the log message format.
        level: String representing the log level.
        """
        module_config = config[setting]
        base = module_config['basics']
        self.logger.remove()
        self.logger.add(sink= base['log_file'],
                   rotation=base['log_max_file_size'],
                   retention=base['log_retention'],
                   format= "{time} {level} {message} {function} {file.path}\n" ,
                   level=base['log_level'])
        self.logger.add(
            "string-atlas-warning.log",
            filter=lambda record: record["level"].name in ["WARNING", "ERROR"],
            format= "{time} {level} {message} {module} {file.name} {function} {line}"
        )
