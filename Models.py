from arcarFirebase.FirebaseModels import FirebaseBase


class M2(FirebaseBase):
    REF = 'm2'


class ProcessEngine(FirebaseBase):
    REF = 'm2/process-engine'


class Output(FirebaseBase):
    REF = 'm2/process-engine/output'


o = Output().get_node('0')
o['Nuevo_item'] = {'item': 2}
o.setdefault('Nuevo_item2', {"item": 3})
o2 = o.get('Nuevo_item2')
o2['item_inside'] = 1222
print(type(o))
