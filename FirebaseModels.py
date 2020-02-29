import json
import traceback
from typing import TypeVar, Optional, Mapping

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db as firebase_db

# These type variables are used by the container types.


_T = TypeVar('_T')
_S = TypeVar('_S')
_KT = TypeVar('_KT')  # Key type.
_VT = TypeVar('_VT')  # Value type.
_T_co = TypeVar('_T_co', covariant=True)  # Any type covariant containers.
_V_co = TypeVar('_V_co', covariant=True)  # Any type covariant containers.
_KT_co = TypeVar('_KT_co', covariant=True)  # Key type covariant containers.
_VT_co = TypeVar('_VT_co', covariant=True)  # Value type covariant containers.


__OPTIONS = __PARAMS.get('options')
__KEYS_REALTIME = __PARAMS.get('keys_realtime')
__BUCKET_NAME = __PARAMS.get('storageBucket')

if not __OPTIONS or not __KEYS_REALTIME:
    print('Not is possible get the params')
    raise KeyError

__CRED = credentials.Certificate(__KEYS_REALTIME)
__APP = firebase_admin.initialize_app(credential=__CRED, options=__OPTIONS)


class FirebaseBase:
    REF = None

    @classmethod
    def __get_ref(cls):
        return firebase_db.reference(cls.REF)

    @classmethod
    def get_all(cls):
        r = cls.__get_ref().get()
        r = ArcarDict(r, cls.REF)
        return r

    @classmethod
    def set_fb(cls, data):
        cls.__get_ref().set(data)

    @classmethod
    def update_fb(cls, data):
        cls.__get_ref().update(data)

    @classmethod
    def delete_fb(cls, data):
        pass

    @classmethod
    def get_node(cls, node):
        REF = cls.REF
        cls.REF = REF + '/' + node
        r = cls.__get_ref().get()
        r = ArcarDict(r, cls.REF)
        cls.REF = REF
        return r


class ArcarArray(list):
    def __getitem__(self, index):
        return list.__getitem__(self, index)

    def __setitem__(self, index, value):
        return list.__setitem__(self, index, value)

    def __delitem__(self, key):
        return list.__delitem__(self, key)

    def __mul__(self, other):
        mul_list = [x * y for x, y in zip(self, other)]
        return ArcarArray(mul_list)


class ArcarDict(dict):
    def __init__(self, firebase_json: dict = None, _ref: str = None):
        if isinstance(firebase_json, str):
            firebase_json = json.loads(firebase_json)
        if not firebase_json:
            firebase_json = self
        super().__init__(firebase_json)
        self.instace_firebase = FirebaseBase
        self.__ref = _ref
        if _ref:
            self.instace_firebase.REF = self.__ref

    def __getitem__(self, item):
        print('get_item', FirebaseBase.REF)
        d = dict.__getitem__(self, item)
        if isinstance(d, dict):
            return ArcarDict(d, self.__ref + '/' + item)
        else:
            return d

    def __setitem__(self, key, value):
        print('set_item ', FirebaseBase.REF)
        try:
            self.instace_firebase.update_fb({key: value})
        except Exception as details:
            traceback.print_exc()
            return self
        else:
            return dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        return dict.__delitem__(self, key)

    def get(self, k: _KT) -> Optional[_VT_co]:
        return dict.get(self, k)

    def setdefault(self, k: _KT, default: _VT = ...) -> _VT:
        pass

    def update(self, __m: Mapping[_KT, _VT] = None, **kwargs: _VT) -> None:
        print("m", __m)
        print("kw", kwargs)
        if __m:
            d = dict.update(self, __m, **kwargs)
        elif kwargs:
            d = dict.update(self, **kwargs)
        else:
            d = self
        return d

    def to_json(self):
        try:
            j = json.dumps(self)
        except Exception as details:
            print(details)
            traceback.print_exc()
        else:
            return j


class M2(FirebaseBase):
    REF = 'm2'


class ProcessEngine(FirebaseBase):
    REF = 'm2/process-engine'


class Output(FirebaseBase):
    REF = 'm2/process-engine/output'


def compare_iters(is_this, in_this):
    return all(list(map(lambda x, y: x in y, is_this, [in_this] * len(is_this))))


# m2 = Output.get_node('0')
# m3 = m2['clientContractData']
# m2['clientContractData']['itemHeredado'] = 'si sirve mas chido'
# m3['otro_item'] = 'a nu ma'
m2 = ArcarDict()
m2.update(a=1)
print(m2)
