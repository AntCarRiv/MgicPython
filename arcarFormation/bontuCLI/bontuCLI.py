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
from pydantic.typing import List, Any

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


def beauty_print(head: List[str], values: List[List[Any]], sep: int = 13):
    formato = ('|{:^' + f'{sep}' + '}') * len(head)
    headers = formato.format(*head)
    arround = '{}|'
    print(arround.format(headers))
    print('=' * (len(headers) + 1))
    for e in values:
        row = formato.format(*e)
        print(arround.format(row))
        print('-' * (len(row) + 1))


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
        self.__security_default = 'api_security'
        self.__api_template_default = 'api_template_default'
        self.__profile_default = 'DEFAULT'
        self.__configuration_initial = {
            # self.__template_default: {'method': self.set_template_default, 'message': 'template default: '},
            self.__project_path: {'method': self.set_path, 'message': 'Work path: '},
            self.__security_default: {'method': self.add_security, 'message': 'Api Security: '},
            self.__api_template_default: {'method': self.add_api_template, 'message': "Api template"}}
        if not os.path.exists(self.__path_config):
            print('Debe configurar los siguientes parametros para poder iniciar.')
            self.initial_configuration()
        self.initial_files()

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

    def initial_files(self):
        path = self.get_work_path(self.__profile_default)
        path_file = os.path.join(path, 'template_properties_default.json')
        if not os.path.exists(path_file):
            with open(path_file, 'w') as ff:
                ff.write(json.dumps({'lambda': {}, 'api': {}}, indent=4))

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
        templates = self.config[profile]['templates']
        templates = templates.split(',')
        # templates = os.listdir(os.path.join(self.get_work_path(profile), 'templates'))
        return templates if templates else 'No hay templates definidos.'

    def get_template_default(self, profile):
        try:
            template_default = self.config.get(profile, self.__template_default)
        except configparser.NoOptionError:
            return None
        return template_default

    def get_api_template(self, profile):
        try:
            api_template = self.config.get(profile, self.__api_template_default)
        except configparser.NoOptionError:
            return None
        return api_template

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
            if not self.config.has_section(profile) and profile != 'DEFAULT':
                return f'El perfil {profile} aun no esta definido, primero intente config --add-profile {profile}'
            self.config.set(profile, self.__project_path, path)
            try:
                self.save_config()
            except Exception as details:
                self.logger.error(details)
                self.logger.error(traceback.format_exc())
                return None
            else:
                return f'work path: "{path}" saved'

    def get_security(self, profile):
        try:
            security = self.config.get(profile, self.__security_default)
            security = security.split(',')
        except Exception as details:
            LOGGER.error(f'Error to try get the security information\nDetails: {details}')
            return None
        else:
            return security

    def add_security(self, profile, security_name):
        if not self.config.has_section(profile) and profile != 'DEFAULT':
            return f'El perfil {profile} aun no esta definido, primero intente config --add-profile {profile}'
        else:
            try:
                if self.config.has_option(profile, self.__security_default):
                    data = self.config.get(profile, self.__security_default)
                    data = data.split(',')
                    data.append(security_name)
                else:
                    data = [security_name]

                data = ','.join(data)
                self.config.set(profile, self.__security_default, data)
                self.save_config()
            except Exception as details:
                print(details)
                LOGGER.error(details)
                LOGGER.error(traceback.format_exc())
                return None
            else:
                return f'Nombre {security_name} como elemento de seguridad guardado '

    def add_new_profile(self, name):
        try:
            self.config.add_section(name)
            self.save_config()
        except Exception as details:
            LOGGER.error(details)
            LOGGER.error(traceback.format_exc())
            return None
        else:
            return f'El perfil {name} se guardo correctamente'

    def add_api_template(self, profile, name_template):
        file_split = os.path.splitext(name_template)
        if file_split[-1] in self.valid_extention_template and len(file_split) == 2:
            self.config.set(profile, self.__api_template_default, name_template)
            if self.save_config():
                return f'template {name_template} guardado como api_template'
            else:
                return 'Error al guardar el api template'
        else:
            return f'La extencion del arhivo deberia ser alguna de las siguientes: {self.valid_extention_template}'

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
        # if self.config.has_section(profile):
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
        # TODO testear creacion de lambdas con api
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
        parser.add_argument("-s", "--security-type", type=str,
                            help="Nombre del autorizador que utilizara la lambda")
        parser.add_argument("-a", "--alias-template", type=str,
                            help="Nombre del id logico donde se contrulle el recurso.")

        args = get_args(parser)

        # Validation for fields
        if not args.name:
            print('Debe definir almenos el nombre de la lambda')
            exit(1)
        if args.template and args.template not in self.config_data.get_valid_templates(args.profile):
            print(
                f'El template no es valido, templates validos son: '
                f'{self.config_data.get_valid_templates(args.profile)}')
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
                f"Asegurate de solo agregar caracteres alfabeticos")
            exit(1)
        if args.api_path and not next(
                re.finditer(regex_endpoint, args.api_path, re.MULTILINE)).group() == args.api_path:
            print(
                f"El nombre {args.api_path} no es un valor valido para el endpoint de la lambda. Los valores deben "
                f"tener la forma /endpoint or /enpoint/example")
            exit(1)
        if args.api_path and not args.alias_template:
            print('El alias template es obligatorio si se pasa un enpoint')
            exit(1)
        # Get all values from args
        alias_template = args.alias_template
        template = args.template if args.template else self.config_data.get_template_default(args.profile)
        path = args.path if args.path else self.config_data.get_work_path(args.profile)
        name = args.name
        endpoint = args.api_path
        verb = args.metodo if endpoint else print(
            'No se guardara el metodo en la configuracion pues no se definio un endpoint')
        security_type = args.security_type if endpoint else print(
            'No se guardara el security_type en la configuracion pues no se definio un endpoint')
        if security_type:
            if security_type not in self.config_data.get_security(args.profile):
                print(
                    f'El tipo de seguridad no esta definido con un tipo de seguridad valido, valoeres permitidos '
                    f'son: {self.config_data.get_security(args.profile)}')
                exit(1)

        # Las validation for make resource
        if not template:
            print('No se definio un template para este recurso')
            exit(1)

        if new_lambda(name, template, path, verb, endpoint, security_type, alias_template):
            print(f'Se creo correrctamente la lambda con el nombre: {name}')
        exit(0)

    def deploy(self):
        def read_config(path_file, file_name):
            with open(os.path.join(path_file, file_name), 'r') as config_object:
                try:
                    data = json.loads(config_object.read())
                except Exception as details:
                    LOGGER.error(details)
                else:
                    return data

        parser = default_parser()
        args = get_args(parser)
        path = self.config_data.get_work_path(args.profile)
        if not path:
            print(f'Debe definir un path de trabajo para el perfil: {args.profile}')
            exit(1)
        lambda_basic_config = read_config(path, 'template_properties_default.json')
        if not lambda_basic_config:
            LOGGER.warning('No se encontro una configuracion default para la lambda.')
        api_template = read_config(path, self.config_data.get_api_template(args.profile))
        if not api_template:
            LOGGER.warning('Not found api-template')
        deploy(path, lambda_basic_config, api_template,
               os.path.join(path, self.config_data.get_api_template(args.profile)))
        exit(0)

    def config(self):
        parser = default_parser()
        parser.add_argument("--show", action="store_true",
                            help="Imprime la informacion de configuracion para un perfil especificado")
        parser.add_argument("--show-all", action="store_true",
                            help="Imprime la informacion de configuracion")
        parser.add_argument("--show-profiles", action="store_true",
                            help="Imprime el nombre de todos los perfiles disponibles")
        parser.add_argument('--show-security', action='store_true',
                            help='Imprime los nombres del tipo de seguridad para api gateway')

        parser.add_argument("--valid-templates", action="store_true",
                            help="Imprime los nombres de los templates validos para añadir lambdas")
        parser.add_argument("--add-template", type=str,
                            help="Añade un nombre de template valido")
        parser.add_argument("--add-path", type=str,
                            help="Añade o actualiza la ruta del directorio del projecto")
        parser.add_argument("--add-profile", type=str,
                            help="Añade un nuevo perfi de configuraciones")
        parser.add_argument('--add-security', type=str,
                            help='Añade el nombre de un elemento de seguridad para api gaateway')

        args = get_args(parser)
        if args.show:
            print(self.config_data.get_config(args.profile))
            exit(0)
        if args.show_all:
            print(self.config_data.get_all_config())
            exit(0)
        if args.add_path:
            print(self.config_data.set_path(args.profile, args.add_path))
            exit(0)
        if args.valid_templates:
            print(self.config_data.get_valid_templates(args.profile))
            exit(0)
        if args.add_template:
            print(self.config_data.add_valid_template(args.profile, args.add_template))
            exit(0)
        if args.show_profiles:
            print(self.config_data.get_profiles())
            exit(0)
        if args.add_profile:
            print(self.config_data.add_new_profile(args.add_profile))
            exit(0)
        if args.show_security:
            print(self.config_data.get_security(args.profile))
            exit(0)
        if args.add_security:
            self.config_data.add_security(args.profile, args.add_security)
            exit(0)


if __name__ == '__main__':
    BontuCLI()
