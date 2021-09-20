
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