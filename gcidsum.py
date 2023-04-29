# -*- coding: utf-8 -*-
#
# Copyright (c) 2022~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import Tuple, List
import sys
import re
import pathlib
import os
import glob

import xlgcid

class OpenFileError(Exception):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(*args)
        self.message = str(message)

def _enumerate_paths(pattern: str):
    if '**' in pattern:
        # sha1sum does not support recursive.
        raise OpenFileError(f"can't open '{pattern}': Invalid argument")

    try:
        if os.path.isabs(pattern):
            if os.name == 'nt':
                drive, path = os.path.splitdrive(pattern)
                # C: resolve to ~, C:\ resolve to C:, see https://stackoverflow.com/questions/48810950/
                drive += '\\'
                path = path.removeprefix('\\').removeprefix('/')
                items = list(pathlib.Path(drive).glob(path))
            else:
                path = pattern.removeprefix('/')
                items = list(pathlib.Path('/').glob(path))
        else:
            try:
                #items = list(pathlib.Path('.').glob(pattern))
                items = glob.glob(pattern)
            except re.error:
                items = [pattern] if os.path.exists(pattern) else None
    except ValueError as ve:
        raise OpenFileError(ve)
    else:
        if items is None:
            raise OpenFileError(f"can't open '{pattern}': Invalid argument")
        else:
            yield from items

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
        __echo_error_message(f"can't open '{path}': Permission denied")
    except FileNotFoundError:
        __echo_error_message(f"can't open '{path}': No such file or directory")

def __echo_error_message(msg: str):
    print(f'gcidsum: {msg}', file=sys.stderr)

def __show_help():
    print('''Usage: gcidsum [-cswe] [FILE]...

Print or check GCID checksums

        -c      Check sums against list in FILEs
        -s      Don't output anything, status code shows success
        -w      Warn about improperly formatted checksum lines
        -e      If exist, the first FILE should be a exists gcidsum file to exclude''')

def __parse_args(args: Tuple[str, ...]):
    excluded = None

    opt = {}
    opt.update(dict.fromkeys(list('cswe'), False))

    if args[0].startswith('-'):
        fs = args[1:]
        for o in 'cswe':
            opt[o] = o in args[0]
    else:
        fs = args

    if opt['e']:
        if fs:
            excluded, *fs = fs
        else:
            __echo_error_message('Missing the gcidsum file (for -e options)')
            exit()

    opt['fs'] = fs
    opt['excluded'] = excluded

    return opt

def gcidsum_main(args: List[str]):
    if not args or args == ('--help', ):
        return __show_help()

    pargs = __parse_args(args)

    def enumerate_from_args(args):
        for arg in args:
            yield from _enumerate_paths(arg)

    if pargs['e']:
        excluded_lines = pathlib.Path(pargs['excluded']).read_text('utf-8').splitlines()
        excluded = set(__parse_output(x)[1] for x in excluded_lines)
    else:
        excluded = ()

    def is_excluded(name) -> bool:
        return str(name) in excluded

    if pargs['c']:
        failed = 0
        total = 0
        for path in enumerate_from_args(pargs['fs']):
            for line in pathlib.Path(path).read_text('utf-8').splitlines():
                if line:
                    gcid_in_file, name = __parse_output(line)

                    if is_excluded(name):
                        continue

                    if gcid_in_file:
                        eq = (gcid := __get_gcid(name)) and (gcid.lower() == gcid_in_file.lower())
                        total += 1
                        if not eq:
                            failed += 1
                        if not pargs['s']:
                            print(f"{name}: {'OK' if eq else 'FAILED'}")
                    elif pargs['w']:
                        __echo_error_message(f'invalid format: {line}')
        if failed:
            __echo_error_message(f'WARNING: {failed} of {total} computed checksums did NOT match')
    else:
        for path in enumerate_from_args(pargs['fs']):
            if is_excluded(path):
                continue

            if gcid := __get_gcid(path):
                output = f'{gcid}  {path}'
                assert __output_pattern.match(output)
                print(output)

def main(argv=None):
    try:
        if argv is None:
            argv = sys.argv
        return gcidsum_main(tuple(argv[1:]))
    except OpenFileError as e:
        __echo_error_message(e.message)
        return 1
    except KeyboardInterrupt:
        return 1

if __name__ == '__main__':
    exit(main() or 0)
