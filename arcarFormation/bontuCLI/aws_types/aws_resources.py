#!/usr/bin/python3
# -*- encoding:utf-8 -*-
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