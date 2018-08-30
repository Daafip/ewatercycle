# -*- coding: utf-8 -*-
import configparser
from abc import ABC, abstractmethod
from urllib.request import urlopen

from ruamel.yaml import YAML


class CaseConfigParser(configparser.ConfigParser):
    """Case sensitive config parser
    See https://stackoverflow.com/questions/1611799/preserve-case-in-configparser
    """
    def optionxform(self, optionstr):
        return optionstr


def fetch(url):
    """Fetches text of url"""
    with urlopen(url) as response:
        return response.read().decode()


class AbstractConfig(ABC):
    @abstractmethod
    def __init__(self, source: str):
        """

        Args:
            source:  Source url of config file
        """
        self.config = None

    @abstractmethod
    def save(self, target: str):
        """

        Args:
            target: File path to save config to

        Returns:

        """
        pass


class IniConfig(AbstractConfig):
    """Config container where config is read/saved in ini format.
    """
    config = CaseConfigParser(strict=False)

    def __init__(self, source):
        super().__init__(source)
        body = fetch(source)
        self.config.read_string(body)

    def save(self, target):
        with open(target, 'w') as f:
            self.config.write(f)


class YamlConfig(AbstractConfig):
    """Config container where config is read/saved in yaml format"""
    yaml = YAML()

    def __init__(self, source):
        super().__init__(source)
        body = fetch(source)
        self.config = self.yaml.load(body)

    def save(self, target):
        with open(target, 'w') as f:
            self.yaml.dump(self.config, f)
