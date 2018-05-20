#!/usr/bin/env python3.6
import argparse
import errno
import glob
import os.path
import re
import sys

# Replace this with your timezone.
DEFAULT_TIMEZONE='-04:00'

OCTO_DATE_SHORT_RE = re.compile('(\d{4}-\d\d-\d\d) (\d\d:\d\d)')
OCTO_DATE_FULL_RE = re.compile('(\d{4}-\d\d-\d\d) (\d\d:\d\d:\d\d) '
                               '([-+]\d\d)(\d\d)')

# List of headers that should be copied over as they are.
EXPECTED_HEADERS = ('title',)


def convert_file(src, dest):
    print(f'Converting {src}...')

    inf = open(src)
    outf = open(dest, 'w')

    # Keep the headers in a buffer until we know we've successfully parsed them
    # all.
    buffer = []

    first_line = inf.readline()
    if first_line.strip() != '---':
        print('  Error: Expected "---" at beginning of file but got '
              f'"{first_line}".')
        return False

    buffer.append(first_line)

    for line in inf:
        if line.strip() == '---':
            buffer.append(line)
            break

        attr, _, value = line.partition(':')
        if not attr:
            print(f'  Error parsing header "{line}"')
            return False

        attr = attr.strip()
        value = value.strip()

        # Need to remove "layout" and "comments" headers and reformat "date"
        # value.  If "published" exists, write "draft: true" if the value of
        # "published" is false.  If "categories" exists, put all list values
        # in quotes.
        if attr == 'layout':
            continue
        elif attr == 'comments':
            continue
        elif attr == 'published':
            if value == 'false':
                buffer.append('draft: true\n')
            continue
        elif attr == 'categories':
            # This assumes you don't have category names with quotes in them...
            cats = [x.strip() for x in
                    value.lstrip('[').rstrip(']').split(',')]
            cat_list_str = (', ').join(f'"{x}"' for x in cats)
            buffer.append(f'categories: [{cat_list_str}]\n')
        elif attr == 'date':
            # octopress dates are of the format "2018-05-17 12:54:49 -0400"
            # hugo dates are of the format "2018-05-17T12:54:49-04:00"
            new_date = None
            m = OCTO_DATE_FULL_RE.match(value)

            if m:
                new_date = f'{m.group(1)}T{m.group(2)}{m.group(3)}:{m.group(4)}'
            else:
                m = OCTO_DATE_SHORT_RE.match(value)
                if m:
                    new_date = f'{m.group(1)}T{m.group(2)}:00{DEFAULT_TIMEZONE}'

            if not new_date:
                print(f'  Error parsing date "{value}"')
                return False

            buffer.append(f'date: {new_date}\n')
        elif attr not in EXPECTED_HEADERS:
            print(f'  Unexpected header "{attr}"')
            return False
        else:
            buffer.append(line)

    outf.writelines(buffer)

    for line in inf:
        outf.write(line)

    print('Done.')
    return True


def main(src, dest):
    print(f'Converting all .md files in {src} and outputting to {dest}.')

    for d in (src, dest):
        if not os.path.exists(d):
            print(f'Error: {d} does not exist.')
            return errno.ENOENT
        if not os.path.isdir(d):
            print(f'Error: {d} is not a directory.')
            return errno.ENOTDIR

    files = glob.glob(os.path.join(src, '*.md'))

    if not files:
        print('No .md files found!')
        return errno.ENOENT

    for f in files:
        if not convert_file(f, os.path.join(dest, os.path.basename(f))):
            return errno.EINVAL

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert Octopress posts to Hugo format.')
    parser.add_argument('src', help='source directory of Octopress posts')
    parser.add_argument('dest', help='destination directory for Hugo posts')
    args = parser.parse_args()
    sys.exit(main(args.src, args.dest))
