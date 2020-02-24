from typing import TypeVar, Optional

# These type variables are used by the container types.
_T = TypeVar('_T')
_S = TypeVar('_S')
_KT = TypeVar('_KT')  # Key type.
_VT = TypeVar('_VT')  # Value type.
_T_co = TypeVar('_T_co', covariant=True)  # Any type covariant containers.
_V_co = TypeVar('_V_co', covariant=True)  # Any type covariant containers.
_KT_co = TypeVar('_KT_co', covariant=True)  # Key type covariant containers.
_VT_co = TypeVar('_VT_co', covariant=True)  # Value type covariant containers.


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


class ArcarMap(dict):
    def __init__(self, ):
        super().__init__()

    def __getitem__(self, item):
        return dict.__getitem__(self, item)

    def __setitem__(self, key, value):
        return dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        return dict.__delitem__(self, key)

    def __connect(self):
        # TODO: Apply connection to firebase
        raise NotImplemented

    def get(self, k: _KT) -> Optional[_VT_co]:
        return dict.get({1: 19}, k)


list_one = ArcarMap({1: 2, 2: 3, 3: 4, 4: 5, 5: 6})

list_one[12] = 31
print(list_one.get(1))
