#!/usr/bin/python3
# -*- encoding:utf-8 -*-
import json
import re
from dataclasses import asdict
from enum import Enum
from typing import Dict, List, Any, ClassVar, Union

from pydantic import StrictInt, StrictStr
from pydantic.dataclasses import dataclass
from pydantic.validators import str_validator, constr_strip_whitespace

RUNTIME: List[str] = 'python3.6 | python3.7 | python3.8'.split(' | ')


class ErrorMixin:
    code: str
    msg_template: str

    def __init__(self, **ctx: Any) -> None:
        self.__dict__ = ctx

    def __str__(self) -> str:
        return self.msg_template.format(**self.__dict__)


class ListMaxLengthError(ErrorMixin, ValueError):
    msg_template = 'ensure that the value for {variable} has at most {limit_value} items'

    def __init__(self, *, limit_value: int, variable: str) -> None:
        super().__init__(limit_value=limit_value, variable=variable)


class Properties:
    def to_dict(self):
        d = {}
        for key, value in asdict(self).items():
            if isinstance(value, Enum):
                value = value.value
            if key not in ['name_resource', 'output']:
                d[key] = value
        d = self.drop_nulls(d)
        return d

    def drop_nulls(self, dictionary: Dict[str, Any]) -> Dict[str, Any]:
        new_dict = {}
        for k, v in dictionary.items():
            if isinstance(v, dict):
                v = self.drop_nulls(v)
            if v:
                new_dict[k] = v
        return new_dict

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4)


class Arn(StrictStr):
    min_length = 10
    max_length = 100
    regex = re.compile(r"(arn:(aws[a-zA-Z-]*)?:[a-z0-9-.]+:.*)|()")


class S3BucketType(StrictStr):
    min_length = 3
    max_length = 62
    regex = re.compile(r'^[0-9A-Za-z\.\-_]*(?<!\.)$')


class S3KeyType(StrictStr):
    min_length = 1
    max_length = 1023


class S3ObjectVersionType(StrictStr):
    min_length = 1
    max_length = 1023


class RoleArn(StrictStr):
    regex = re.compile(r'arn:(aws[a-zA-Z-]*)?:iam::\d{12}:role/?[a-zA-Z_0-9+=,.@\-_/]+')


class Role(StrictStr):
    regex = re.compile(r'[a-zA-Z_0-9+=,.@\-_/]+')


class Description(StrictStr):
    max_length = 255


class Handler(StrictStr):
    max_length = 127
    regex = re.compile(r'[^\s]+')


class KmsKeyArn(StrictStr):
    regex = re.compile(r'(arn:(aws[a-zA-Z-]*)?:[a-z0-9-.]+:.*)|()')


class MemorySize(StrictInt):
    ge = 128
    le = 3008


class ReservedConcurrentExecutions(StrictInt):
    ge = 0


class Runtime(str):
    strip_whitespace: ClassVar[bool] = True
    min_length: ClassVar[int] = 1
    max_length: ClassVar[int] = 30

    def __init__(self, runtime: str):
        self.runtime = runtime

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield str_validator
        yield constr_strip_whitespace
        yield cls.validate_runtime
        yield cls

    @classmethod
    def validate_runtime(cls, runtime: str) -> str:
        if runtime not in RUNTIME:
            raise ValueError('Runtime not valid')
        return runtime


class Timeout(StrictInt):
    ge = 1


class ModeType(str, Enum):
    Active = 'Active'
    PassThrough = 'PassThrough'


@dataclass
class DeadLetterConfig(Properties):
    TargetArn: Arn


@dataclass()
class Code(Properties):
    S3Bucket: S3BucketType
    S3Key: S3KeyType
    S3ObjectVersion: S3ObjectVersionType
    ZipFile: str


@dataclass()
class Environment(Properties):
    Variables: Dict[str, Any]


@dataclass
class Tag(Properties):
    Key: str
    Value: str


@dataclass
class TracingConfig(Properties):
    Mode: ModeType


@dataclass
class VpcConfig(Properties):
    SecurityGroupIds: List[Union[Dict, str]]
    SubnetIds: List[Union[Dict, str]]

    def __post_init__(self):
        if len(self.SecurityGroupIds) > 5 and isinstance(self.SecurityGroupIds, list):
            raise ListMaxLengthError(limit_value=5, variable='SecurityGroupIds')
        if len(self.SubnetIds) > 16 and isinstance(self.SubnetIds, list):
            raise ListMaxLengthError(limit_value=16, variable='SubnetIds')
