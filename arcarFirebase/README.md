# Arcar Firebase

Ejemplos de uso 


Creando modelos
```python
from arcarFirebase.FirebaseModels import FirebaseBase


class Example(FirebaseBase):
    REF = 'some_path_ref'

class Exmple2(FirebaseBase):
    REF = 'some/path_ref'

```


Ejemplo de actualizacion de datos
```python
from arcarFirebase.FirebaseModels import FirebaseBase

class Example(FirebaseBase):
    REF = 'some_path_ref'


example = Example().get_all()

# update string value
example['some_node_string'] = 'somedata'

# update dictionary value
example['some_node_dict'] = {"key": "value"}

# update Array value
example['some_node_array'] = ['value1', 'value2', 'value3']

# update numeric value
example['some_node_numeric'] = 12

# deep update
example['some_node']['some_deep_node'] = 'some data'

```

