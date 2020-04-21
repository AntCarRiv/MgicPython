#!/usr/bin/python3
# -*- encoding:utf-8 -*-
from typing import List, Optional, Union, Dict, Any

from . import meta_types as mt
from dataclasses import dataclass


@dataclass
class LambdaProperties(mt.Properties):
    Code: Union[str, mt.Code]
    Handler: mt.Handler
    Role: Union[mt.Role, Dict]
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
        self.name_resource = self.Properties.FunctionName
        self.output = f'{self.Properties.FunctionName}Arn'


@dataclass
class Template(mt.Properties):
    AWSTemplateFormatVersion: str = "2010-09-09"
    Description: mt.Description = "template lambdas"
    Parameters: Dict[str, Any] = None
    Resources: Dict[str, Any] = None
    Outputs: Dict[str, Any] = None
