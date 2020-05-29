#!/usr/bin/env python

import argparse
import configparser
import json
import logging
import os
import re
import sys
import traceback

from make_template import deploy
from make_template import new_lambda

LOGGER = logging.getLogger('BontuCLI')
LOGGER.setLevel(logging.INFO)
CONFIG = configparser.ConfigParser()

BASE_PATH = os.path.expanduser('~')
BONTU_PATH = os.path.join(BASE_PATH, '.bontu')

if not os.path.exists(BONTU_PATH):
    os.mkdir(BONTU_PATH)


def default_parser():
    parser = argparse.ArgumentParser(description='Record changes to the repository')
    parser.add_argument("--profile", default='DEFAULT', help="Nombre del perfil de configuracion")
    return parser


def get_args(parser):
    args = sys.argv[2:]
    return parser.parse_args(args)


class Config:
    def __init__(self, name_config='bontuTest.ini'):
        self.logger = logging.getLogger('Config')
        self.name_config = name_config
        self.config = configparser.RawConfigParser()
        self.__path_config = os.path.join(BASE_PATH, BONTU_PATH, name_config)
        self.config.read(self.__path_config)
        self.valid_extention_template = ['.json', '.yaml', '.yml', 'template']
        self.__template_default = 'template_default'
        self.__project_path = 'project_path'
        self.__profile_default = 'DEFAULT'
        self.__configuration_initial = {
            self.__template_default: {'method': self.set_template_default, 'message': 'template default: '},
            self.__project_path: {'method': self.set_path, 'message': 'Work path: '}}
        if not os.path.exists(self.__path_config):
            print('Debe configurar los siguientes parametros para poder iniciar.')
            self.initial_configuration()

    def initial_configuration(self):
        try:
            for key, value in self.__configuration_initial.items():
                if key not in self.config.defaults():
                    print(value['method'](self.__profile_default, input(value['message'])))
                if not self.config.defaults():
                    break
        except KeyboardInterrupt:
            try:
                os.remove(self.__path_config)
            except Exception as details:
                pass
        else:
            for key in self.__configuration_initial:
                if key not in self.config.defaults():
                    self.initial_configuration()
                    break

    def get_profiles(self):
        return self.config.sections()

    def get_config(self, profile):
        if self.config.has_section(profile):
            return json.dumps(dict(self.config[profile]), indent=4)
        elif self.config.defaults():
            return self.config.defaults()
        else:
            return f'El perfil {profile} no existe'

    def get_all_config(self):
        return str('\n').join([f'{e[0]} {json.dumps(dict(e[1]), indent=4)}' for e in self.config.items() if dict(e[1])])

    def get_valid_templates(self, profile):
        if 'templates' in self.config[profile]:
            tplt = self.config[profile]['templates']
            tplt = tplt.split(',')
            tplt.sort()
            return tplt
        else:
            return 'No hay templates definidos para este perfil.'

    def get_template_default(self, profile):
        try:
            template_default = self.config.get(profile, self.__template_default)
        except configparser.NoOptionError:
            return None
        return template_default

    def get_work_path(self, profile):
        try:
            path = self.config.get(profile, self.__project_path)
        except configparser.NoOptionError:
            return None
        return path

    def set_path(self, profile, path):
        if not os.path.exists(path):
            return f'El path "{path}" no existe en el sistema'
        else:
            self.config.set(profile, self.__project_path, path)
            try:
                self.save_config()
            except Exception as details:
                self.logger.error(details)
                self.logger.error(traceback.format_exc())
                return None
            else:
                return f'work path: "{path}" saved'

    def set_template_default(self, profile, name_template):
        file_split = os.path.splitext(name_template)
        if file_split[-1] in self.valid_extention_template and len(file_split) == 2:
            self.config.set(profile, self.__template_default, name_template)
            if self.save_config():
                return f'template {name_template} guardado como default'
            else:
                return 'Error al guardar el template defaul'
        else:
            return f'La extencion del arhivo deberia ser alguna de las siguientes: {self.valid_extention_template}'

    def add_valid_template(self, profile, template_name):
        file_split = os.path.splitext(template_name)
        if self.config.has_section(profile):
            if 'templates' in self.config[profile]:
                tplt = self.config[profile]['templates']
                tplt = tplt.split(',')
                if template_name not in tplt and file_split[-1] in self.valid_extention_template and len(
                        file_split) == 2:
                    tplt.append(template_name)
                    self.config[profile]['templates'] = str(',').join(tplt)
                elif file_split[-1] not in self.valid_extention_template or len(file_split) != 2:
                    return "Nombre de template no valido"
                else:
                    return "Ya existe este template en la lista"
            else:
                if file_split[-1] in self.valid_extention_template and len(file_split) == 2:
                    self.config[profile]['templates'] = template_name
                else:
                    return 'Nombre del template no valido'

            if self.save_config():
                return 'Se guardo correctamente el nuevo template'
            else:
                return 'Error al intentar guardar el nuevo template'

    def save_config(self):
        try:
            with open(os.path.join(BASE_PATH, BONTU_PATH, self.name_config), 'w') as ff:
                self.config.write(ff)
        except Exception as details:
            self.logger.error(details)
            self.logger.error(traceback.format_exc())
            return False
        else:
            return True


class BontuCLI(object):

    def __init__(self):
        functions = {"new-lambda": "new_lambda"}
        self.config_data = Config()
        parser = argparse.ArgumentParser(
            description='Pretends to BontuCLI',
            usage='''BontuCLI <command> [<args>]

The most commonly used BontuCLI commands are:
   new-lambda     Create a new lambda in the project
   deploy         Make all templates for the deploy
   config         Make or add configurtion to profile
''')
        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, functions.get(args.command, args.command)):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        getattr(self, functions.get(args.command, args.command))()

    def new_lambda(self):
        parser = default_parser()
        parser.add_argument("-n", "--name", type=str,
                            help="Nombre que recibe la lambda")
        parser.add_argument("-t", "--template", type=str,
                            help="Nombre del template al que pertenece la lambda")
        parser.add_argument("-p", "--path", type=str,
                            help="Ubicacion en donde se guardara la lambda, por defecto se usara la ruta "
                                 "establecida por el comando -w o --work_path")
        parser.add_argument("-e", "--api-path", type=str,
                            help="Nombre del endpoint para api Gateway")
        parser.add_argument("-m", "--metodo", type=str, choices=['get', 'post', 'patch', 'put'],
                            help="metodo con el que se invoca la lambda a travez de api gateway")
        parser.add_argument("-s", "--security-type", type=str, choices=['auth_admin', 'auth_users', 'auth_both'],
                            help="Nombre del autorizador que utilizara la lambda")

        args = get_args(parser)

        # Validation for fields
        if not args.name:
            print('Debe definir almenos el nombre de la lambda')
            exit(1)
        if args.template and args.template not in self.config_data.get_valid_templates(args.profile):
            print(f'El template no es valido.')
            exit(0)
        if args.path and not os.path.exists(args.path):
            print('El path indicado no existe.')
            exit(0)

        # Validation with regex
        regex_name = r'^(([a-z]|[A-Z])*)'
        regex_endpoint = r'((\/)([a-zA-Z]+))+'
        if not next(re.finditer(regex_name, args.name, re.MULTILINE)).group() == args.name:
            print(
                f"El nombre {args.name} no es un valor valido para el nombre de la lambda. "
                f"Asegurate de solo agregar Caracteres")
            exit(1)
        if args.api_path and not next(
                re.finditer(regex_endpoint, args.api_path, re.MULTILINE)).group() == args.api_path:
            print(
                f"El nombre {args.api_path} no es un valor valido para el endpoint de la lambda.")
            exit(1)

        # Get all values from args
        template = args.template if args.template else self.config_data.get_template_default(args.profile)
        path = args.path if args.path else self.config_data.get_work_path(args.profile)
        name = args.name
        endpoint = args.api_path
        verb = args.metodo if endpoint else print(
            'No se guardara el metodo en la configuracion pues no se definio un endpoint')
        security_type = args.security_type if endpoint else print(
            'No se guardara el security_type en la configuracion pues no se definio un endpoint')

        # Las validation for make resource
        if not template:
            print('No se definio un template para este recurso')
            exit(1)

        new_lambda(name, template, path, verb, endpoint, security_type)
        exit(0)

    def deploy(self):
        parser = default_parser()
        args = get_args(parser)
        path = self.config_data.get_work_path(args.profile)
        if not path:
            print(f'Debe definir un path de trabajo para el perfil: {args.profile}')
            exit(1)
        deploy(path)
        exit(0)

    def config(self):
        parser = default_parser()
        parser.add_argument("--show", action="store_true",
                            help="Imprime la informacion de configuracion para un perfil especificado")
        parser.add_argument("--show-all", action="store_true",
                            help="Imprime la informacion de configuracion")
        parser.add_argument("--valid-templates", action="store_true",
                            help="Imprime los nombres de los templates validos para añadir lambdas")
        parser.add_argument("--add-template", type=str,
                            help="Añade un nombre de template valido")
        parser.add_argument("--add-path", type=str,
                            help="Añade o actualiza la ruta del directorio del projecto")

        args = get_args(parser)
        if args.show:
            print(self.config_data.get_config(args.profile))
            exit(0)
        if args.show_all:
            print(self.config_data.get_all_config())
            exit(0)
        if args.add_path:
            self.config_data.set_path(args.profile, args.add_path)
            exit(0)
        if args.valid_templates:
            print(self.config_data.get_valid_templates(args.profile))
            exit(0)
        if args.add_template:
            print(self.config_data.add_valid_template(args.profile, args.add_template))
            exit(0)


if __name__ == '__main__':
    BontuCLI()
