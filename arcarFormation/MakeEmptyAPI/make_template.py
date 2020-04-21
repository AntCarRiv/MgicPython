import json
import logging
import os
from copy import deepcopy
from typing import List, Dict, Any, Optional

from aws_types import aws_resources
from meta import templates as t

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger('makeTemplates')


def get_all_lambdas(path) -> Dict[str, Any]:
    return {e[0].replace(path, ''): read_json_config(os.path.join(e[0], i), path) for e in os.walk(path) for i in e[2]
            if
            os.path.splitext(i)[-1].lower() == '.json' and os.path.splitext(i)[0].lower() == 'configuration'}


def read_json_config(json_path: str, path: str) -> Dict[str, Any]:
    with open(json_path, 'r') as jf:
        try:
            data = json.loads(jf.read())
        except Exception as details:
            LOGGER.warning(details)
            data = {}
    if data:
        data.update({'nft': not check_father_template(data, path)})
    return data


def check_father_template(dict_configuration, path):
    template = dict_configuration.get('template')
    if template and os.path.exists(os.path.join(path, template)):
        return True
    else:
        return False


def group_by_template(all_lambdas: Dict[str, Any]) -> Dict[str, List[Any]]:
    groups = {}
    for lmd in all_lambdas:
        template_name = all_lambdas[lmd].get('template')
        if not template_name:
            LOGGER.warning('No template in lambda config will be created one')
            template_name = 'OutLambdas.json'
        else:
            del all_lambdas[lmd]['template']
        if template_name not in groups:
            groups.setdefault(template_name, [])
        groups[template_name].append(all_lambdas[lmd])
    return groups


def make_dir_lambda(path):
    try:
        LOGGER.info(f'Try make dir {path}')
        os.mkdir(path)
    except FileNotFoundError:
        os.makedirs(path)


def validation_name(name: str) -> Optional[str]:
    LOGGER.info("Name validation")
    if name[0] == '.':
        return None
    if name[0] == '/':
        return f'.{name}'
    if name[0] != '/':
        return f'./{name}'


def new_lambda(name: str, template: str = None, path: str = None) -> bool:
    try:
        name_system = name
        path_system = os.path.join(path.replace('/', os.sep), name.replace('/', os.sep))
        LOGGER.info(
            f'\nPath: {path.replace("/", os.sep)}\nName: {name.replace("/", os.sep)}\nTemplate: {template}\npath_system: {path_system}')
        name = validation_name(name)
        if not name:
            print('Not define relative path in the name lambda')
            return False
        LOGGER.info('Name ok')
        if not os.path.exists(path_system):
            make_dir_lambda(path_system)

            lambda_name = os.path.split(path_system)[-1]
            lambda_template = deepcopy(t.new_lambda_template)
            lambda_template['template'] = template if template else lambda_template['template']
            lambda_template['function_config']["Code"] = name
            lambda_template['function_config']["FunctionName"] = lambda_name

            with open(os.path.join(path_system, 'lambda_function.py'), 'w') as code_file:
                code_file.write(t.CODE_LAMBDA_TEMPLATE.format(name_lambda=lambda_name))
            with open(os.path.join(path_system, 'configuration.json'), 'w') as conf_file:
                conf_file.write(json.dumps(lambda_template, indent=4))
        else:
            LOGGER.warning(f'The dir {name} already exist in the work path')
            return False
    except Exception as details:
        LOGGER.warning(details)
        return False
    return True


def deploy(path):
    all_config_lambdas = get_all_lambdas(path)
    groups = group_by_template(all_config_lambdas)
    t_template = deepcopy(t.parameter_default)

    templates = {}
    LOGGER.info(f'Will be created {len(groups)} templates')
    for template in groups:
        template_length = len(groups[template])
        if template_length > 200:
            LOGGER.error(
                f'The limit for templates is 200 resource but this template contain {template_length} resources')
        for dd in groups[template]:
            print(template, dd['function_config'])
            t_lambda = deepcopy(t.template_properties_lambda_default)
            t_lambda.update(dd.get('function_config'))
            lp = aws_resources.LambdaProperties(**t_lambda)
            l = aws_resources.Lambda(Properties=lp)
            if template not in templates:
                templates[template]: aws_resources.Template = aws_resources.Template(Parameters=t_template,
                                                                                     Resources={l.name_resource: l},
                                                                                     Outputs={})
            else:
                if l.name_resource in templates[template].Resources:
                    LOGGER.warning('Resource will be replace by other with the same name')
                templates[template].Resources[l.name_resource] = l

    for template in templates:
        print('saving', template)
        with open(os.path.join(path, template), 'w') as ff:
            ff.write(templates[template].to_json())
