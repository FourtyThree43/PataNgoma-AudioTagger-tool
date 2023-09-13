from typing import List
from mediafile import MediaFile
from InquirerPy import inquirer

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

# print()
# print("\n".join(sorted([f"['{fld}']" for fld in valid_fields])))
# print("\n".join(sorted([f'"{fld}"' for fld in valid_fields])))
# print()

fields = inquirer.fuzzy(
    message="Select fields:",
    choices=valid_fields,
    multiselect=True,
    validate=lambda result: len(result) >= 1,
    invalid_message="minimum 1 selection",
    max_height="70%",
).execute()

print(words)
