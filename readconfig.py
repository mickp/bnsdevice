import configparser
import os

path = os.path.dirname(os.path.abspath(__file__))
files = [os.path.sep.join([path, file])
    for file in os.listdir(path) if file.endswith('.conf')]
config = configparser.ConfigParser()
config.read(files)
