#!/usr/bin/python3
# -*- encoding:utf-8 -*-
import json
import re
from dataclasses import field
from typing import List, Optional, Union, Dict, Any

import boto3
from . import meta_types as mt
from pydantic.dataclasses import dataclass


@dataclass
class LambdaProperties(mt.Properties):
    Code: Union[str, mt.Code]
    Handler: mt.Handler
    Role: Union[mt.RoleArn, Dict[str, Any], mt.Role]
    Runtime: mt.Runtime

    FunctionName: str = ''

    Environment: Optional[mt.Environment] = None
    Layers: Union[List[Union[str, Dict]], Dict] = None
    MemorySize: Optional[mt.MemorySize] = None
    Tags: List[Optional[mt.Tag]] = None
    Timeout: Optional[mt.Timeout] = None
    VpcConfig: Optional[mt.VpcConfig] = None
    Description: Optional[mt.Description] = None

    DeadLetterConfig: Optional[mt.DeadLetterConfig] = None
    ReservedConcurrentExecutions: Optional[mt.ReservedConcurrentExecutions] = None
    TracingConfig: Optional[mt.TracingConfig] = None
    KmsKeyArn: Optional[mt.KmsKeyArn] = None

    def __post_init__(self):
        self.__client_iam = boto3.resource('iam')
        try:
            if isinstance(self.Role, str):
                self.Role = self.__client_iam.Role(self.Role).arn
        except AttributeError:
            raise ValueError('Role not exist in this account')

        if isinstance(self.Role, dict) and list(self.Role.keys())[0] != 'Ref':
            raise ValueError('You can\'t use a dict like a role if not is a reference to resource template')


@dataclass
class Lambda(mt.Properties):
    Type: str = "AWS::Lambda::Function"
    Properties: LambdaProperties = None

    def __post_init__(self):
        if not self.Properties:
            raise ValueError('Properties is empty')
        if not self.Properties.FunctionName and isinstance(self.Properties.Code, str):
            self.Properties.FunctionName = self.Properties.Code[2:]
        elif not self.Properties.FunctionName and not isinstance(self.Properties.Code, str):
            raise ValueError('Error in name lambda')

    @property
    def name_resource(self):
        regex = r"[A-Za-z0-9]*"
        matches = re.finditer(regex, self.Properties.FunctionName, re.MULTILINE)
        name_resource = ''
        for matchNum, match in enumerate(matches, start=1):
            gg = match.group()
            if gg:
                name_resource += gg

        return name_resource

    @property
    def output_resource(self):
        regex = r"[A-Za-z0-9]*"
        matches = re.finditer(regex, self.Properties.FunctionName, re.MULTILINE)
        name_resource = ''
        for matchNum, match in enumerate(matches, start=1):
            gg = match.group()
            if gg:
                name_resource += gg

        return f'{name_resource}Arn'


@dataclass
class Template(mt.Properties):
    AWSTemplateFormatVersion: str = "2010-09-09"
    Description: mt.Description = "Template Created by tool"
    Metadata: Dict[str, Any] = field(default_factory=dict)
    Parameters: Dict[str, Any] = field(default_factory=dict)
    Mappings: Dict[str, Any] = field(default_factory=dict)
    Conditions: Dict[str, Any] = field(default_factory=dict)
    Transform: Dict[str, Any] = field(default_factory=dict)
    Resources: Dict[str, Any] = field(default_factory=dict)
    Outputs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApiBaseMethod:
    verb: str = None
    consumes: List[str] = field(default_factory=lambda: ["application/json"])
    produces: List[str] = field(default_factory=lambda: ["application/json"])
    responses: Dict[str, Any] = field(default_factory=lambda: {
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
    })

    security: List[Dict] = None
    x_amazon_apigateway_integration: Dict[str, Any] = None

    @classmethod
    def get_method_instance(cls, region,
                            template_name,
                            resource_name,
                            role_api_invoke,
                            allow_methods,
                            allow_headers,
                            security: List[str] = None):
        x_amazon_apigateway_integration = {
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
                        "method.response.header.Access-Control-Allow-Methods": f"{allow_methods}",
                        "method.response.header.Access-Control-Allow-Headers": f"{allow_headers}",
                        "method.response.header.Access-Control-Allow-Origin": "'*'"
                    }
                }
            },
            "passthroughBehavior": "when_no_templates",
            "httpMethod": "POST",
            "contentHandling": "CONVERT_TO_TEXT",
            "type": "aws_proxy"
        }
        security = [{s: []} for s in security]
        return cls(security=security, x_amazon_apigateway_integration=x_amazon_apigateway_integration)

    def to_json(self):
        template = self.to_dict()
        try:
            template['x-amazon-apigateway-integration'] = self.x_amazon_apigateway_integration
            del template['x_amazon_apigateway_integration']
        except Exception as details:
            pass
        try:
            del template['verb']
        except Exception as details:
            pass
        return json.dumps(template, indent=4)


@dataclass
class ApiGet(ApiBaseMethod, mt.Properties):
    verb: str = 'get'


@dataclass
class ApiPost(ApiBaseMethod, mt.Properties):
    verb: str = 'post'


@dataclass
class ApiOptions(ApiBaseMethod, mt.Properties):
    verb: str = 'options'

    @classmethod
    def get_method_instance(cls, **kwargs):
        x_amazon_apigateway_integration = {
                "responses": {
                    "default": {
                        "statusCode": "200",
                        "responseParameters": {
                            "method.response.header.Access-Control-Allow-Methods": f"{kwargs.get('allow_methods')}",
                            "method.response.header.Access-Control-Allow-Headers": f"{kwargs.get('allow_headers')}",
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
        return cls(x_amazon_apigateway_integration=x_amazon_apigateway_integration)


@dataclass
class APITemplate(mt.Properties):
    swagger: str = None
    info: Dict[str, Any] = None
    host: str = None
    basePath: str = None
    schemes: List[str] = None
    paths: Dict[str, Any] = None
    securityDefinitions: Dict[str, Any] = None
    definitions: Dict[str, Any] = None
    x_amazon_apigateway_gateway_responses: Dict[str, Any] = None
    x_amazon_apigateway_binary_media_types: List[str] = None
    x_amazon_apigateway_documentation: Dict[str, Any] = None

    @classmethod
    def special_instance(cls, template):
        template['x_amazon_apigateway_gateway_responses'] = template['x-amazon-apigateway-gateway-responses']
        del template['x-amazon-apigateway-gateway-responses']
        template['x_amazon_apigateway_binary_media_types'] = template['x-amazon-apigateway-binary-media-types']
        del template['x-amazon-apigateway-binary-media-types']
        template['x_amazon_apigateway_documentation'] = template['x-amazon-apigateway-documentation']
        del template['x-amazon-apigateway-documentation']
        return cls(**template)

    def to_json(self):
        template = self.to_dict()
        template['x-amazon-apigateway-gateway-responses'] = template['x_amazon_apigateway_gateway_responses']
        del template['x_amazon_apigateway_gateway_responses']
        template['x-amazon-apigateway-binary-media-types'] = template['x_amazon_apigateway_binary_media_types']
        del template['x_amazon_apigateway_binary_media_types']
        template['x-amazon-apigateway-documentation'] = template['x_amazon_apigateway_documentation']
        del template['x_amazon_apigateway_documentation']
        for p in template['paths']:
            for v in template['paths'][p]:
                try:
                        template['paths'][p][v]['x-amazon-apigateway-integration'] = template['paths'][p][v]['x_amazon_apigateway_integration']
                        del template['paths'][p][v]['x_amazon_apigateway_integration']
                except KeyError:
                    pass
                try:
                    del template['paths'][p][v]['verb']
                except KeyError:
                    pass
        return json.dumps(template, indent=4)

    def add_method(self, instance_verb: Union[ApiGet, ApiPost, ApiOptions], path):
        self.paths.setdefault(path, {})
        self.paths[path].update({instance_verb.verb: instance_verb.to_dict()})
