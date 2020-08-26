from frugy.areas import CommonHeader, ChassisInfo, BoardInfo, ProductInfo
from frugy.multirecords import MultirecordArea
import yaml

class Fru:
    _area_table_lookup = {
        'ChassisInfo': 'chassis_info_offs',
        'BoardInfo': 'board_info_offs',
        'ProductInfo': 'product_info_offs',
        'MultirecordArea': 'multirecord_offs',
    }
    _area_table_lookup_rev = {v: k for k, v in _area_table_lookup.items()}

    def __init__(self, initdict=None):
        self.header = CommonHeader()
        self.areas = {}
        if initdict is not None:
            self.update(initdict)

    def factory(self, cls_name, cls_args=None):
        map = {
            'ChassisInfo': ChassisInfo,
            'BoardInfo': BoardInfo,
            'ProductInfo': ProductInfo,
            'MultirecordArea': MultirecordArea
        }
        if cls_name not in map:
            raise ValueError(f"unknown FRU area: {cls_name}")
        return map[cls_name](cls_args)

    def update(self, src):
        self.areas = {k: self.factory(k, src[k]) for k in src.keys()}

    def to_dict(self):
        return {k: v.to_dict() for k, v in self.areas.items()}

    def __repr__(self):
        return repr(self.to_dict())

    def serialize(self):
        self.header.reset()

        # Determine offsets for areas
        curr_offs = self.header.size_total()
        for area, offs in self._area_table_lookup.items():
            if area in self.areas:
                self.header[offs] = curr_offs
                curr_offs += self.areas[area].size_total()

        # Serialize everything
        result = self.header.serialize()
        for area in self._area_table_lookup.keys():
            if area in self.areas:
                result += self.areas[area].serialize()

        return result

    def deserialize(self, input):
        self.areas = {}
        self.header.deserialize(input)
        for k, v in self.header.to_dict().items():
            if v:
                obj_name = self._area_table_lookup_rev[k]
                obj = self.factory(obj_name)
                obj.deserialize(input[v:])
                self.areas[obj_name] = obj

    def load_yaml(self, fname):
        with open(fname, 'r') as infile:
            fru_dict = yaml.load(infile)
        self.update(fru_dict)
    
    def save_yaml(self, fname):
        with open(fname, 'w') as outfile:
            yaml.dump(self.to_dict(), outfile, default_flow_style=False)

    def load_bin(self, fname):
        with open(fname, 'rb') as infile:
            self.deserialize(infile.read())

    def save_bin(self, fname):
        with open(fname, 'wb') as outfile:
            outfile.write(self.serialize())