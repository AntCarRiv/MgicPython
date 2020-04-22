#!/usr/bin/env python

import argparse
import configparser
import logging
import os
import sys

from make_template import deploy
from make_template import new_lambda

LOGGER = logging.getLogger('BontuCLI')
LOGGER.setLevel(logging.INFO)
CONFIG = configparser.ConfigParser()

BASE_PATH = os.path.expanduser('~')
NAME_CONFIG = 'bontuConfig.ini'
BONTU_PATH = os.path.join(BASE_PATH, '.bontu')
PATH_CONFIG = os.path.join(BONTU_PATH, NAME_CONFIG)

if not os.path.exists(BONTU_PATH):
    os.mkdir(BONTU_PATH)


class BontuCLI(object):

    def __init__(self):
        functions = {"new-lambda": "new_lambda"}
        parser = argparse.ArgumentParser(
            description='Pretends to BontuCLI',
            usage='''BontuCLI <command> [<args>]

The most commonly used BontuCLI commands are:
   new-lambda     Create a new lambda in the project
   deploy         Make all templates for the deploy
''')
        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, functions.get(args.command, args.command)):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        getattr(self, functions.get(args.command, args.command))()

    @staticmethod
    def prepare_command(self, function):
        def decorator(*args, **kwargs):
            parser = argparse.ArgumentParser(description='Record changes to the repository')
            parser.add_argument("--profile", default='DEFAULT', help="Nombre del perfil de configuracion")
            args = self.__get_args(parser)
            config = dict(self.read_config(args.profile))
            return function(parser, args, config)

        return decorator

    @staticmethod
    def __get_args(parser):
        return parser.parse_args(sys.argv[2:])

    @staticmethod
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

    def new_lambda(self):
        parser = argparse.ArgumentParser(description='Record changes to the repository')
        parser.add_argument("-n", "--name", type=str,
                            help="Nombre que recibe la lambda")
        parser.add_argument("-t", "--template", type=str,
                            help="Nombre del template al que pertenece la lambda")
        parser.add_argument("-p", "--path", type=str,
                            help="Ubicacion en donde se guardara la lambda, por defecto se usara la ruta establecida por el comando -w o --work_path")
        parser.add_argument("--profile", default='DEFAULT', help="Nombre del perfil de configuracion")
        args = self.__get_args(parser)
        if args.name:
            config = dict(self.read_config(args.profile))
            result = new_lambda(args.name, args.template, args.path if args.path else config.get('path'))
            if result:
                print(f'Se creo correctamente la lambda {args.name}')
            else:
                print(f'No se creo la lambda con el nomrbe {args.name}')
            exit(0)
        exit(0)

    def deploy(self):
        parser = argparse.ArgumentParser(
            description='Record changes to the repository')
        parser.add_argument("--deploy", action='store_true',
                            help="Crea los templates respectivos con la configuracion establecida")
        parser.add_argument("--profile", default='DEFAULT', help="Nombre del perfil de configuracion")
        args = self.__get_args(parser)
        if args.deploy:
            config = dict(self.read_config(args.profile))
            if not config.get('path'):
                print('No hay un directorio de trabajo definido en este perfil')
                exit(0)
            deploy(config.get('path'))
            exit(0)

        exit(0)

    @prepare_command
    def config(self, parser, args, config):
        parser.add_argument("--config", action='store_true',
                            help="Crea los templates respectivos con la configuracion establecida")

    #
    # def fetch(self):
    #     parser = argparse.ArgumentParser(
    #         description='Download objects and refs from another repository')
    #     # NOT prefixing the argument with -- means it's not optional
    #     parser.add_argument('repository')
    #     args = parser.parse_args(sys.argv[2:])
    #     print('Running git fetch, repository=%s' % args.repository)
    #


if __name__ == '__main__':
    BontuCLI()
