import json
import sys

json_str = ''.join(sys.argv[1:])
params = json.loads(json_str)
out = ''

for key in params.keys():
    out += f' --{key} "{params[key]}"'

print(f'starter_inputs={out}')