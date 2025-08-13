#!/usr/bin/env python3
import csv
import json
import fiona
import os
import re
import sys
import logging
from pyproj import CRS, Transformer
from collections import namedtuple
from typing import Any


# orig_id is the dict key
EhrEntry = namedtuple('EhrEntry', ['nimetus', 'addr', 'year'])


def choose_one(options: list[str], path: str) -> str:
    if not options:
        logging.error('Missing data files')
        return ''

    if len(options) == 1:
        return os.path.join(path, options[0])

    for i, fn in enumerate(options, 1):
        print(f'{i}. {fn}')
    decision = input('Which one: ').strip()
    if re.match(r'^\d+$', decision):
        d = int(decision)
        if d >= 1 and d <= len(options):
            return os.path.join(path, options[d-1])

    return ''


def choose_sources() -> tuple[str, str]:
    path = os.path.join(os.path.dirname(__file__), '..', 'data')
    files = os.listdir(path)

    ehr_files = [f for f in files if re.match(r'ehr.*\.csv', f)]
    ehr = choose_one(ehr_files, path)

    etak_files = [f for f in files if re.match(r'ETAK.*\.zip', f)]
    etak = choose_one(etak_files, path)

    return ehr, etak


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s %(message)s',
        datefmt='%H:%M:%S')
    ehr_file, etak_zip = choose_sources()
    if not etak_zip or not ehr_file:
        sys.exit(1)

    logging.info('Reading %s', ehr_file)
    ehr: dict[int, EhrEntry] = {}
    with open(ehr_file, 'r') as f:
        r = csv.DictReader(f, delimiter=';')
        for line in r:
            code = line['ehr_kood'].strip()
            if not code or code[0] != '1':
                continue

            # If no date, we have no use for it.
            # kav_kasutus_kp is a weird thing from old document,
            # an intended opening date.
            year = line['esmane_kasutus']  # or line['kav_kasutus_kp']
            if not year:
                continue
            if len(year) > 4:
                year = year[:4]
            if not re.match(r'^\d{4}$', year):
                continue

            ehr[int(code)] = EhrEntry(
                nimetus=line['nimetus'] or line['ehitise_tyyp'],
                addr=line['taisaadress'],
                year=year,
            )
    logging.info('Done, read %s records', len(ehr))

    count = 0
    logging.info('Iterating over %s', etak_zip)
    with fiona.open('/E_401_hoone_ka.shp', vfs=f'zip://{etak_zip}') as shp:
        p_in = CRS.from_proj4(shp.crs.to_proj4())
        p_out = CRS.from_epsg(4326)
        transformer = Transformer.from_crs(p_in, p_out)
        for hoone in shp:
            if hoone['geometry']['type'] != 'Polygon':
                continue

            # Find the relevant EHR entry, skip if not found
            ehr_gid = hoone['properties'].get('ehr_gid')
            if not ehr_gid or not re.match(r'^\d+$', str(ehr_gid)):
                continue
            ehr_entry = ehr.get(int(ehr_gid))
            if not ehr_entry:
                continue

            try:
                coords = []
                for ring in hoone['geometry']['coordinates']:
                    coord = list(zip(*ring))
                    x2, y2 = transformer.transform(coord[0], coord[1])
                    coords.append(list(zip(y2, x2)))
                props = hoone['properties']

                data: dict[str, Any] = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': coords,
                    },
                    'properties': {
                        'type': ehr_entry.nimetus,
                        'addr': ehr_entry.addr,
                        'year': int(ehr_entry.year),
                    },
                }
                height = props.get('korgus_m')
                if height:
                    data['properties']['height'] = int(height)
                print(json.dumps(data, ensure_ascii=False))
                count += 1
            except Exception as e:
                logging.exception('Failed to write data: %s', e)
                break
    logging.info('All done, written %s records.', count)
