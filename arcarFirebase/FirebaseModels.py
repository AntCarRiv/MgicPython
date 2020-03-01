import json
import traceback
import warnings

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db as firebase_db

# These type variables are used by the container types.
import tools_lambda

__PARAMS = tools_lambda.get_params("firebase_realtime")
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
    def delete_fb(cls):
        try:
            cls.__get_ref().delete()
        except Exception as details:
            print(details)
            traceback.print_exc()

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
        self.__instance_firebase = FirebaseBase
        self.__ref = _ref
        if _ref:
            self.__instance_firebase.REF = self.__ref

    def __getitem__(self, item):
        _d = dict.__getitem__(self, item)
        if isinstance(_d, dict):
            return ArcarDict(_d, f'{self.__ref}/{item}')
        else:
            return _d

    def __setitem__(self, key, value):
        try:
            self.__instance_firebase.update_fb({key: value})
        except Exception as details:
            print(details)
            traceback.print_exc()
            return self
        else:
            return ArcarDict(dict.__setitem__(self, key, value), self.__ref)

    def __delitem__(self, key):
        try:
            r = self.instance_firebase.REF
            self.instance_firebase.REF += f'/{key}'
            self.instance_firebase.delete_fb()
            self.instance_firebase.REF = r
        except Exception as details:
            print(details)
            traceback.print_exc()
        else:
            dict.__delitem__(self, key)
        return self

    def get(self, k):
        _d = dict.get(self, k)
        if isinstance(_d, dict):
            _d = ArcarDict(_d, self.__ref)
        return _d

    def setdefault(self, k, default):
        if k not in self:
            try:
                self.__setitem__(k, default)
            except Exception as details:
                print(details)
                traceback.print_exc()
            else:
                return default

    def update(self, __m=None, **kwargs) -> None:
        pass

    def to_json(self, name_file: str = None):
        try:
            if name_file:
                with open(name_file, 'w', encoding='utf-8') as file:
                    json.dump(self, file)
            else:
                j = json.dumps(self)
                return j
        except Exception as details:
            print(details)
            traceback.print_exc()
