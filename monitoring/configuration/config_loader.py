import configparser
import os

def load_config(script_path) -> configparser.ConfigParser:
    script_directory = os.path.dirname(script_path)
    config_file_path = os.path.join(script_directory, 'config.ini')
    config = configparser.ConfigParser()
    config.read(config_file_path)
    return config
