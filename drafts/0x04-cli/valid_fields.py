from typing import List
from mediafile import MediaFile

fields: List[str] = [
    field for field in dir(MediaFile) if not field.startswith("_")
]

ignore = [
    'add_field', 'as_dict', 'delete', 'save', 'update', 'readable_fields',
    'sorted_fields'
]

for fld in ignore:
    fields.remove(fld)

valid_fields: List[str] = fields

"""
print each valid key in a new line.
"""

print()
print("\n".join(sorted([f"['{fld}']" for fld in valid_fields])))
print("\n".join(sorted([f'"{fld}"' for fld in valid_fields])))
print()


