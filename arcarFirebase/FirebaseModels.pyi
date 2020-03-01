import warnings
from typing import TypeVar, MutableMapping, Generic, Mapping, MutableSequence

_T = TypeVar('_T')
_S = TypeVar('_S')
_KT = TypeVar('_KT')  # Key type.
_VT = TypeVar('_VT')  # Value type.
_T_co = TypeVar('_T_co', covariant=True)  # Any type covariant containers.
_V_co = TypeVar('_V_co', covariant=True)  # Any type covariant containers.
_KT_co = TypeVar('_KT_co', covariant=True)  # Key type covariant containers.
_VT_co = TypeVar('_VT_co', covariant=True)  # Value type covariant containers.
ArcarDict = TypeVar('ArcarDict')


class FirebaseBase:

    #
    #     def __get_ref(self): ...
    #
    def get_all(self) -> ArcarDict: ...

    #     def set_fb(self, data: Mapping[_KT, _VT]) -> ArcarDict: ...
    #
    #     def update_fb(self, data: Mapping[_KT, _VT]) -> ArcarDict: ...
    #
    #     def delete_fb(self) -> ArcarDict: ...
    #
    def get_node(self, node: _KT) -> ArcarDict: ...


class ArcarDict(MutableMapping[_KT, _VT], Generic[_KT, _VT]):
    def __init__(self, firebase_json: dict, _ref: str):
        self.__instance_firebase = None
        self.__ref = None
        ...

    def __getitem__(self, key: _KT) -> ArcarDict: ...

    def __setitem__(self, key: _KT, value: _VT) -> ArcarDict: ...

    def __delete__(self, key: _KT) -> ArcarDict: ...

    def get(self, k: _KT) -> ArcarDict: ...

    def setdefault(self, k: _KT, default: _VT = ...) -> _VT: ...

    def update(self, __m: Mapping[_KT, _VT], **kwargs: _VT) -> None:
        warnings.warn('Not implemented', DeprecationWarning, stacklevel=2)

    def to_json(self, name: str): ...


class ArcarArray(MutableSequence[_T], Generic[_T]): ...
