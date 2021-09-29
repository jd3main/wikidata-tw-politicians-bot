from typing import (
    Sequence,
)


def preview(s, head:int=5, tail:int=5, printer=None):
    if type(s)==list:
        preview_list(s, head, tail, printer)
    if type(s)==dict:
        preview_dict(s, head, tail, printer)


def preview_list(s:list, head:int=5, tail:int=5, item_printer=None):
    if item_printer is None:
        item_printer = lambda v: print(v)

    n = len(s)
    if n < head+tail:
        for i in range(n):
            item_printer(s[i])
    else:
        for i in range(head):
            item_printer(s[i])
        for i in range(n-tail, n):
            item_printer(s[i])
        
    print(f'({n} items)')

def preview_dict(d:list, head:int=5, tail:int=5, item_printer=None):
    if item_printer is None:
        item_printer = lambda k,v: print(f'{k}:\t{v}')

    n = len(d)
    for i,(k,v) in enumerate(d.items()):
        if i==head and i<n-tail:
            print('...')
        if i<head or i>=n-tail:
            item_printer(k,v)

    print(f'({n} items)')


def options_interface(description,
                      options:Sequence,
                      indices=None,
                      input_description=':',
                      upper_border='-',
                      lower_border='',
                      default:str=None,
                      case_sensitive=False,
    ) -> str:
    
    if indices is None:
        indices = [str(i) for i in range(1, len(options)+1)]

    index_width = max([_str_width(s) for s in indices]) + 1

    lines = []
    for idx, opt in zip(indices, options):
        lines.append(f'{idx.rjust(index_width)}) {opt}')
    width = max([_str_width(s) for s in lines])

    print(upper_border*width)
    print(description)
    for line in lines:
        print(line)
    print(lower_border*width)

    if case_sensitive:
        str_equal = lambda x,y: x==y
    else:
        str_equal = lambda x,y: x.lower()==y.lower()

    while True:
        input_value = input(input_description)
        for index in indices:
            if str_equal(index, input_value):
                return input_value
        if default != '':
            return default


def _str_width(s:str):
    width = 0
    for c in s:
        if ord(c) < 128:
            width += 1
        else:
            width += 2
    return width
