import pint
import tokenize
import io
from collections import deque


#TODO: decide a place to hold the missing unit definitions that pint is not aware of
#from pathlib import Path 
#_unitsfile = Path(__file__).parent / "units_en.txt" 
#u = pint.UnitRegistry(_unitsfile)
ureg = pint.UnitRegistry()
ureg.define("molC = 12.0107 * g")


def to_slash_notation(txt):
    "Conver the units so Pint can understand them"
    res = []
    g = tokenize.tokenize(io.BytesIO(txt.encode('utf-8')).readline)
    while True:
        try:
            name, val, _, _, _ = next(g)
        except StopIteration:
            break
        if name == tokenize.ENCODING:
            continue
        elif name == tokenize.NAME:
            if val.isalpha():
                res.append(('NAME', val))
                continue
            if val.isalnum():
                for i, v in enumerate(val):
                    if not val[i].isalpha():
                        break
                val = val[:i] + '**' + val[i:]
                res.append(('NAME', val))
                continue
        elif name == tokenize.OP:
            res.append(('OP', val))
        elif name == tokenize.NUMBER:
            res.append(('NUMBER', val))
        elif name == tokenize.NEWLINE:
            break
        else:
            print(f"Ignoreing... {name}, {val}")
    indices = [index for index, (name, val) in enumerate(res) if name == 'NAME']
    indices.append(len(res))
    parts = [dict(res[start:end]) for start, end in zip(indices[:-1], indices[1:])]
    records = deque()
    for part in parts:
        if 'NUMBER' in part:
            part['NAME'] = part['NAME'] + "**" + part['NUMBER']
            operator = part.get('OP')
            if operator == '-':
                part.pop('OP')
                previous = records.pop()
                previous['OP'] = '/'
                records.append(previous)
        records.append(part)
    last_record = records.pop()
    t = [record.get('NAME', '') + ' ' + record.get('OP', '*') for record in records]
    t.append(last_record.get('NAME', '') + ' ' + last_record.get('OP', ''))
    return (" ".join(t)).strip()


def convert(a: str, b: str) -> float:
    """
    Returns the factor required to convert from unit "a" to unit "b"
    """
    #print(a, b)
    try:
        A = ureg(a)
    except: #  DimensionalityError, UndefinedUnitError
        A = to_slash_notation(a)
        A = ureg(A)
    try:
        B = ureg(b)
    except:
        B = to_slash_notation(b)
        B = ureg(B)
    print(A, B)
    return A.to(B).magnitude


def is_equal(a, b):
    "check if both 'b' and 'b' are equal"
    ...

def _quicktest():
    a = 1 * ureg.mmolC
    b = 1 * ureg.kg

    aa = 1 * ureg.mmolC /(ureg.m * ureg.m) / ureg.d
    bb = 1 * ureg.kg / (ureg.m * ureg.m) / ureg.s

    print(a.to(b))

    print(aa.to(bb))

    r = convert('mmolC/m2/d', 'kg m-2 s-1')
    print(r)
