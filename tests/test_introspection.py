import os
import unittest
from frugy.fru import Fru
from frugy.fru_registry import FruRecordType, rec_enumerate, rec_lookup_by_name

class TestIntrospection(unittest.TestCase):
    _docs_path = 'docs'

    def doc_record_schema_md(self, rec_name):
        try:
            schema = rec_lookup_by_name(rec_name)._schema
        except AttributeError:
            return ''

        w1 = 25
        w2 = 20
        w3 = 60
        result = f'|{"Name".ljust(w1)}|{"Type".ljust(w2)}|{"Opt".ljust(w3)}\n'\
                 f'|{"-" * w1}|{"-" * w2}|{"-" * w3}|\n'

        for entry in schema:
            e_name = entry[0]
            if e_name.startswith('_'):
                continue
            e_name = f'`{e_name}`'
            e_inst = entry[1]
            e_args = ''
            e_opt = ''
            if e_inst._description == 'int':
                e_args = f'({e_inst.args[0]})'
                if 'constants' in e_inst.kwargs:
                    e_opt = ', '.join(k for k in e_inst.kwargs['constants'].keys())
                    #e_opt = ', '.join(f'{k}={v}' for k, v in e_inst.kwargs['constants'].items())
            elif e_inst._description == 'array':
                e_args = f'({e_inst.args[0].__name__})'
            elif e_inst._description in ('str', 'strarray', 'bytes', 'ipv4'):
                pass
            else:
                e_args = e_inst.args
                e_opt = e_inst.kwargs

            e_type = f'{e_inst._description} {e_args}'
            result += f'|{e_name.ljust(w1)}|{e_type.ljust(w2)}|{str(e_opt).ljust(w3)}|\n'
        return result

    def doc_supported_records_md(self):
        w1 = 36
        w2 = 80
        result = '# Supported records\n'
        for rec_type in list(FruRecordType):
            rec_list = rec_enumerate(rec_type)
            if len(rec_list) != 0:
                result += f'\n## {rec_type.name}\n\n'
                result += '|' + 'Name'.ljust(w1) + '|' + 'Definition'.ljust(w2) + '|\n'
                result += '|' + '-' * w1 +         '|' + '-' * w2               + '|\n'
                for r in rec_list:
                    result += f'|{r.__name__.ljust(w1)}|{str(r.__doc__).strip().ljust(w2)}|\n'
        return result

    def test_doc_supported_records(self):
        os.makedirs(self._docs_path, 0o755, exist_ok=True)
        with open(os.path.join(self._docs_path, 'records.md'), 'w') as f:
            f.write(self.doc_supported_records_md())
    
    def test_doc_schemas(self):
        os.makedirs(self._docs_path, 0o755, exist_ok=True)
        result = ''
        categories = {
            'ipmi': [FruRecordType.ipmi_area, FruRecordType.ipmi_multirecord],
            'picmg': [FruRecordType.picmg_multirecord, FruRecordType.picmg_secondary],
            'fmc': [FruRecordType.fmc_multirecord, FruRecordType.fmc_secondary],
        }
        for category in categories:
            result = f'\n# {category.upper()} records\n\n'
            for rec_type in categories[category]:
                rec_list = rec_enumerate(rec_type)
                if len(rec_list) != 0:
                    for r in rec_list:
                        schema_doc = self.doc_record_schema_md(r.__name__)
                        if len(schema_doc) == 0:
                            continue
                        result += f'\n## {r.__name__}\n{str(r.__doc__).strip()}\n\n'
                        result += schema_doc
            with open(os.path.join(self._docs_path, f'{category}.md'), 'w') as f:
                f.write(result)
