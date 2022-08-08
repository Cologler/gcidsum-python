# -*- coding: utf-8 -*-
#
# Copyright (c) 2022~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import *
import sys
import re
import pathlib

import xlgcid

def __enumerate_names(args):
    for arg in args:
        yield from pathlib.Path('.').glob(arg)

__output_pattern = re.compile('^(?P<gcid>[0-9a-f]{40})  (?P<name>.+)$', re.I)
def __parse_output(line: str):
    if match := __output_pattern.match(line):
        return match.group('gcid'), match.group('name')
    else:
        return None, None

def __get_gcid(path):
    try:
        return xlgcid.get_file_gcid_digest(path).hex().lower()
    except PermissionError:
        __error(f"can't open '{path}': Permission denied")
    except FileNotFoundError:
        __error(f"can't open '{path}': No such file or directory")

def __error(msg: str):
    print(f'gcidsum: {msg}', file=sys.stderr)

def __show_help():
    print('''Usage: gcidsum [-c[sw]] [FILE]...

Print or check GCID checksums

        -c      Check sums against list in FILEs
        -s      Don't output anything, status code shows success
        -w      Warn about improperly formatted checksum lines''')

def __parse_args(args: Tuple[str, ...]):
    s, w = False, False

    if c := args[0].startswith('-c'):
        s = 's' in args[0]
        w = 'w' in args[0]
        fs = args[1:]
    else:
        fs = args

    return {
        'c': c, 's': s, 'w': w,
        'fs': fs
    }

def main(argv=None):
    if argv is None:
        argv = sys.argv
    args = tuple(argv[1:])

    if not args or args == ('--help', ):
        return __show_help()

    pargs = __parse_args(args)

    if pargs['c']:
        failed = 0
        total = 0
        for path in __enumerate_names(pargs['fs']):
            for line in path.read_text('utf-8').splitlines():
                if line:
                    gcid_in_file, name = __parse_output(line)
                    if gcid_in_file:
                        eq = (gcid := __get_gcid(name)) and (gcid.lower() == gcid_in_file.lower())
                        total += 1
                        if not eq:
                            failed += 1
                        if not pargs['s']:
                            print(f"{name}: {'OK' if eq else 'FAILED'}")
                    elif pargs['w']:
                        __error(f'invalid format: {line}')
        if failed:
            __error(f'WARNING: {failed} of {total} computed checksums did NOT match')
    else:
        for path in __enumerate_names(pargs['fs']):
            if gcid := __get_gcid(path):
                output = f'{gcid}  {path}'
                assert __output_pattern.match(output)
                print(output)

if __name__ == '__main__':
    exit(main() or 0)