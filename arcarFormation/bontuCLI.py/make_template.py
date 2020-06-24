import json
import logging
import os
from copy import deepcopy
from typing import List, Dict, Any, Optional, Union

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
        LOGGER.debug(f'Try make dir {path}')
        os.mkdir(path)
    except FileNotFoundError:
        os.makedirs(path)


def validation_name(name: str) -> Optional[str]:
    LOGGER.debug("Name validation")
    if name[0] == '.':
        return None
    if name[0] == '/':
        return f'.{name}'
    if name[0] != '/':
        return f'./{name}'


def add_method(method: str, template_api: dict, api_path: str) -> Optional[Union[dict, bool]]:
    if method and not hasattr(Methods, method):
        return False
    else:
        template_api[api_path][method] = getattr(Methods, method)()
    return template_api


def add_api_config(api_path: str, api_methods: (str, list, tuple)) -> dict:
    template_api = {api_path: {}}
    if isinstance(api_methods, (list, tuple)):
        for method in api_methods:
            add_method(method, template_api, api_path)
    elif isinstance(api_methods, str):
        add_method(api_methods, template_api, api_path)
    template_api[api_path]['options'] = Methods.options()

    return template_api


def new_lambda(name: str, template: str = None, path: str = None,
               api_method: str = None, api_path: str = None, security_type: str = None) -> bool:
    try:
        name_system = name
        path_system = os.path.join(path.replace('/', os.sep), name.replace('/', os.sep))
        LOGGER.debug(
            f'\nPath: {path.replace("/", os.sep)}\nName: {name.replace("/", os.sep)}\nTemplate: {template}\npath_system: {path_system}')
        name = validation_name(name)
        if not name:
            print('Not define relative path in the name lambda')
            return False
        LOGGER.debug('Name ok')
        if not os.path.exists(path_system):
            make_dir_lambda(path_system)

            lambda_name = os.path.split(path_system)[-1]
            lambda_template = deepcopy(t.new_lambda_template)
            lambda_template['template'] = template if template else lambda_template['template']
            lambda_template['function_config']["Code"] = name
            lambda_template['function_config']["FunctionName"] = lambda_name
            if api_path:
                lambda_template.setdefault('api_configuration', {})
                lambda_template['api_configuration'].update({"path": api_path})
            if api_method and api_path:
                lambda_template['api_configuration'].update({"Method": api_method})
            if security_type and api_path:
                lambda_template['api_configuration'].update({"Security": security_type})
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


def read_template(template):
    with open(template, 'r') as ff:
        data = json.loads(ff.read())
    try:
        template = aws_resources.Template(**data)
    except Exception as details:
        LOGGER.error(details)
        raise ValueError("Template not valid")
    else:
        return template


def deploy(path, properties_default):
    all_config_lambdas = get_all_lambdas(path)
    groups = group_by_template(all_config_lambdas)
    templates = {}
    LOGGER.info(f'Will be created {len(groups)} templates')
    for template in groups:
        template_length = len(groups[template])
        if template_length > 200:
            LOGGER.error(
                f'The limit for templates is 200 resource but this template contain {template_length} resources')
        for lmd in groups[template]:
            t_lambda = deepcopy(properties_default.get('lambda'))
            t_method = deepcopy(t.template_properties_method_default)
            if t_lambda is None or t_method is None:
                raise ValueError('Not found lambda or api data')
            resources = lmd.get('Resources', [])
            if resources:
                for r in resources:
                    t_lambda.update(lmd.get('function_config'))
                    t_lambda.update(resources[r])
                    t_method.update(lmd.get('api_configuration'))
                    t_lambda['FunctionName'] = r
                    lp = aws_resources.LambdaProperties(**t_lambda)
                    lmd_instance = aws_resources.Lambda(Properties=lp)
                    templates.setdefault(template, read_template(os.path.join(path, template)))
                    if lmd_instance.name_resource in templates[template].Resources:
                        LOGGER.warning('Resource will be replace by other with the same name')
                    templates[template].Resources[lmd_instance.name_resource] = lmd_instance
                    templates[template].Outputs[lmd_instance.output_resource] = {"Description": "",
                                                                        "Value": {
                                                                            "Ref": lmd_instance.name_resource
                                                                        }
                                                                        }
            else:
                t_lambda.update(lmd.get('function_config'))
                t_method.update(lmd.get('api_configuration'))
                lp = aws_resources.LambdaProperties(**t_lambda)
                lmd_instance = aws_resources.Lambda(Properties=lp)
                templates.setdefault(template, read_template(os.path.join(path, template)))
                if lmd_instance.name_resource in templates[template].Resources:
                    LOGGER.warning('Resource will be replace by other with the same name')
                templates[template].Resources[lmd_instance.name_resource] = lmd_instance

    for template in templates:
        print('saving template ---> ', template)
        with open(os.path.join(path, template), 'w') as ff:
            ff.write(templates[template].to_json())


class Methods:

    @classmethod
    def base_method(cls, security_type: str, role_api_invoke: str,
                    region: str, template_name: str, resource_name: str) -> dict:
        return {
            "consumes": [
                "application/json"
            ],
            "produces": [
                "application/json"
            ],
            "responses": {
                "200": {
                    "description": "200 response",
                    "schema": {
                        "$ref": "#/definitions/Empty"
                    },
                    "headers": {
                        "Access-Control-Allow-Origin": {
                            "type": "string"
                        },
                        "Access-Control-Allow-Methods": {
                            "type": "string"
                        },
                        "Access-Control-Allow-Headers": {
                            "type": "string"
                        }
                    }
                }
            },
            "security": [
                {
                    security_type: []
                },
                {
                    "api_key": []
                }
            ],
            "x-amazon-apigateway-integration": {
                "uri": {
                    "Fn::Join": [
                        "",
                        [
                            f"arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/",
                            {
                                "Fn::GetAtt": [
                                    template_name,
                                    f"Outputs.{resource_name}Arn"
                                ]
                            },
                            "/invocations"
                        ]
                    ]
                },
                "credentials": {
                    "Fn::Join": [
                        "",
                        [
                            "arn:aws:iam::",
                            {
                                "Ref": "AWS::AccountId"
                            },
                            f":role/{role_api_invoke}"
                        ]
                    ]
                },
                "responses": {
                    "default": {
                        "statusCode": "200",
                        "responseParameters": {
                            "method.response.header.Access-Control-Allow-Methods": f"{t.VERBS}",
                            "method.response.header.Access-Control-Allow-Headers": f"{t.HEADERS}",
                            "method.response.header.Access-Control-Allow-Origin": "'*'"
                        }
                    }
                },
                "passthroughBehavior": "when_no_templates",
                "httpMethod": "POST",
                "contentHandling": "CONVERT_TO_TEXT",
                "type": "aws_proxy"
            }
        }

    @classmethod
    def post(cls, security_type, role_api_invoke, region, template_name, resource_name):
        base = cls.base_method(security_type, role_api_invoke, region, template_name, resource_name)
        base.update(dict(parameters=[{"in": "body",
                                      "name": "Empty",
                                      "required": False,
                                      "schema": {
                                          "$ref": "#/definitions/Empty"}
                                      }
                                     ])
                    )
        return base

    @classmethod
    def get(cls, security_type, role_api_invoke, region, template_name, resource_name):
        base = cls.base_method(security_type, role_api_invoke, region, template_name, resource_name)
        base.update(dict(parameters=[{"in": "query",
                                      "required": False,
                                      "type": "string"
                                      }
                                     ])
                    )
        return base

    @classmethod
    def options(cls):
        return {
            "consumes": [
                "application/json"
            ],
            "produces": [
                "application/json"
            ],
            "responses": {
                "200": {
                    "description": "200 response",
                    "schema": {
                        "$ref": "#/definitions/Empty"
                    },
                    "headers": {
                        "Access-Control-Allow-Origin": {
                            "type": "string"
                        },
                        "Access-Control-Allow-Methods": {
                            "type": "string"
                        },
                        "Access-Control-Allow-Headers": {
                            "type": "string"
                        }
                    }
                }
            },
            "x-amazon-apigateway-integration": {
                "responses": {
                    "default": {
                        "statusCode": "200",
                        "responseParameters": {
                            "method.response.header.Access-Control-Allow-Methods": f"{t.VERBS}",
                            "method.response.header.Access-Control-Allow-Headers": f"{t.HEADERS}",
                            "method.response.header.Access-Control-Allow-Origin": "'*'"
                        }
                    }
                },
                "passthroughBehavior": "when_no_match",
                "requestTemplates": {
                    "application/json": "{\"statusCode\": 200}"
                },
                "type": "mock"
            }
        }


if __name__ == '__main__':
    def read_config(path_file, file_name):
        with open(os.path.join(path_file, file_name), 'r') as config_object:
            try:
                data = json.loads(config_object.read())
            except Exception as details:
                LOGGER.error(details)
            else:
                return data


    lambda_basic_config = read_config('/home/carlosa/PycharmProjects/MgicPython/pruebas_deploy_carlos',
                                      'template_properties_default.json')
    deploy('/home/carlosa/PycharmProjects/MgicPython/pruebas_deploy_carlos', lambda_basic_config)
