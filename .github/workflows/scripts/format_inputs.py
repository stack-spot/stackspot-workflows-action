import json
import sys

json_str = ''.join(sys.argv[1:])
params = json.loads(json_str)
out = ''

for key in params.keys():
    val = params[key].replace('"','\"').replace(" ", "\ ")
    out += f' --{key} {val}'

print(f'stk_inputs={out}')