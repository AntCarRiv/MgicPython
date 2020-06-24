#!/usr/bin/python3
# -*- encoding:utf-8 -*-
from dataclasses import asdict
from datetime import date
from typing import Dict, Any


class Resource:
    def to_dict(self) -> Dict[str, Any]:
        base = {}
        for k, v in asdict(self).items():
            if isinstance(v, date):
                base[k] = v.strftime('%Y%m%d')
            elif v:
                base[k] = v
        return base
