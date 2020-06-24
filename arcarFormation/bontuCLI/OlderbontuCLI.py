#!/usr/bin/python3
# -*- encoding:utf-8 -*-

import argparse
import configparser
import logging
import os

from make_template import new_lambda
from make_template import deploy

__author__ = 'Carlos Añorve'
__version__ = '1.2'

LOGGER = logging.getLogger('BontuCLI')
LOGGER.setLevel(logging.INFO)

CONFIG = configparser.ConfigParser()
PARSER = argparse.ArgumentParser()

BASE_PATH = os.path.expanduser('~')
NAME_CONFIG = 'bontuConfig.ini'
BONTU_PATH = os.path.join(BASE_PATH, '.bontu')
PATH_CONFIG = os.path.join(BONTU_PATH, NAME_CONFIG)

if not os.path.exists(BONTU_PATH):
    os.mkdir(BONTU_PATH)

# Make lambdas commands
PARSER.add_argument("-n", "--name", type=str,
                    help="Nombre que recibe la lambda")
PARSER.add_argument("-t", "--template", type=str,
                    help="Nombre del template al que pertenece la lambda")
PARSER.add_argument("-p", "--path", type=str,
                    help="Ubicacion en donde se guardara la lambda, por defecto se usara la ruta establecida por el comando -w o --work_path")

# Configuration
PARSER.add_argument("-w", "--work_path", type=str,
                    help="Defina la ubicacion de su proyecto de lambbdas")
PARSER.add_argument("--config", action="store_true",
                    help="Imprime la informacion de configuracion")
PARSER.add_argument("--valid-templates", type=str,
                    help="Imprime los nombres de los templates validos para añadir lambdas")
PARSER.add_argument("--add-templates", type=str,
                    help="Añade un nombre de template valido")

PARSER.add_argument("--deploy", action='store_true',
                    help="Crea los templates respectivos con la configuracion establecida")

# Use profiles
PARSER.add_argument("--profile", default='DEFAULT', help="Nombre del perfil de configuracion")
PARSER.add_argument("--list-profiles", action='store_true', help="Lista de perdiles configurados")

args = PARSER.parse_args()


def save_config(data):
    if os.path.exists(PATH_CONFIG):
        data_config_profile = read_config(args.profile, True)
        data_config_profile.update({'TemplateDefault': "ModTEMPLATEOUTAPI.json"})
        data_config_profile.update(data)
    else:
        data_config_profile = data
    CONFIG[args.profile] = data_config_profile

    with open(PATH_CONFIG, 'w') as configfile:
        CONFIG.write(configfile)


def read_config(profile, save=False):
    CONFIG.read(PATH_CONFIG)
    try:
        data_config_profile = dict(CONFIG[profile])
    except KeyError as details:
        if save:
            return {}
        else:
            LOGGER.error(f'No existe informacion para el perfil: {details}')
            exit(1)
    except Exception as details:
        LOGGER.error(f'Error desconosido: {details}')
        exit(1)
    else:
        return data_config_profile


def read_profiles():
    pass


if not os.path.exists(PATH_CONFIG) and not args.path and not args.work_path:
    print(
        'Please use the command --work_path or -w and define your work path\nEg. python -m bontu.new_lambda --work_path C:\\user\\my_project')
    exit(1)

if args.config:
    print(read_config(args.profile))
    exit(0)

if args.work_path:
    if not os.path.exists(args.work_path):
        print(f'El path "{args.work_path}" no existe en el sistema')
        exit(1)
    else:
        save_config({"path": args.work_path})
        print(f'work path: "{args.work_path}" saved')
        exit(0)

if args.name:
    config = dict(read_config(args.profile))
    result = new_lambda(args.name, args.template, args.path if args.path else config.get('path'))
    if result:
        print(f'Se creo correctamente la lambda {args.name}')
    else:
        print(f'No se creo la lambda con el nomrbe {args.name}')
    exit(0)

if args.deploy:
    config = dict(read_config(args.profile))
    if not config.get('path'):
        print('No hay un directorio de trabajo definido en este perfil')
        exit(0)
    deploy(config.get('path'))
    exit(0)

if args.list_profiles:
    CONFIG.read(PATH_CONFIG)
    print(list(CONFIG.keys()))
    exit(0)

if args.add_template:
    print(args.add_template)
    exit(0)