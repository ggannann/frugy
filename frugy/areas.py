from frugy.types import FruAreaVersioned, FruAreaDelimited, fixed_field, string_field
from datetime import datetime, timedelta

_language_code = 0  # Use English and UTF-8 as default encoding

class CommonHeader(FruAreaVersioned):
    _schema = [
        ('internal_use_offs', fixed_field('u8', default=0)),
        ('chassis_info_offs', fixed_field('u8', default=0)),
        ('board_info_offs', fixed_field('u8', default=0)),
        ('product_info_offs', fixed_field('u8', default=0)),
        ('multirecord_offs', fixed_field('u8', default=0)),
    ]

    def __getitem__(self, key):
        return self._get(key) * 8

    def __setitem__(self, key, value):
            if value % 8 != 0:
                raise RuntimeError("Offset not aligned to 64 bit")
            self._set(key, value // 8)
    
    def reset(self):
        for item in self._dict:
            self._set(item, 0)


class ChassisInfo(FruAreaDelimited):
    _schema = [
        ('type', fixed_field('u8')),
        ('part_number', string_field()),
        ('serial_number', string_field()),
    ]

class BoardInfo(FruAreaDelimited):
    _schema = [
        ('language_code', fixed_field('u8', default=_language_code)),
        ('mfg_date_time', fixed_field('u24', default=0)),
        ('manufacturer', string_field()),
        ('product_name', string_field()),
        ('serial_number', string_field()),
        ('part_number', string_field()),
        ('fru_file_id', string_field()),
        # TODO: do we need custom manufacturing info fields?
    ]

    _time_ref = datetime(1996, 1, 1)

    def _set_mfg_date_time(self, timestamp):
        if timestamp is not None:
            td = timestamp - BoardInfo._time_ref
            minutes = td.seconds // 60 + td.days * (60*24)
            self._set('mfg_date_time', minutes)
        else:
            self._set('mfg_date_time', 0)

    def _get_mfg_date_time(self):
        minutes = self._get('mfg_date_time')
        if minutes != 0:
            timestamp = BoardInfo._time_ref + timedelta(minutes=minutes)
            return timestamp
        else:
            return None

class ProductInfo(FruAreaDelimited):
    _schema = [
        ('language_code', fixed_field('u8', default=_language_code)),
        ('manufacturer', string_field()),
        ('product_name', string_field()),
        ('part_number', string_field()),
        ('version', string_field()),
        ('serial_number', string_field()),
        ('asset_tag', string_field()),
        ('fru_file_id', string_field()),
        # TODO: do we need custom manufacturing info fields?
    ]
