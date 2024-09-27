# import module
from mftool import Mftool

obj = Mftool()

print(obj.get_scheme_details("02"))


data = obj.get_scheme_codes()
print(len(data.keys()))
