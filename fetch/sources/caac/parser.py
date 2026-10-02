"""Parse CAAC NOTAM Summary PDFs into normalized area records.

Summary layout (text extracted by pdfplumber):

    A 2363/26 A) ZBPE ZYSH
    NOTAMN B) 2026/06/30/1600 C) 2026/08/31/1559
    E) A TEMPORARY PROHIBITED AREA ESTABLISHED BOUNDED BY:
    N395600E1192100-N395600E1193300-...
    BACK TO START.

Entries start at a line matching "<series> <number>/<year> ". Page furniture
(repeated page headers, standalone page numbers such as 4/12) must be stripped
first, because the extraction sometimes breaks one coordinate across lines,
for example N39 / newline / 4300E1192100.
"""
import datetime
import io
import re

import pdfplumber

from ..base import append_record, empty_data
from ..common import (
    EMPTY_TIME,
    PERMANENT_END,
    add_area_records,
    extract_fir,
    normalize_coordinate_notation,
    standardize_coordinate,
)

ENTRY_HEAD_RE = re.compile(r'^([A-Z]) (\d{1,4}/\d{2,4}) ', re.MULTILINE)
PAGE_NUMBER_RE = re.compile(r'^\d{1,3}/\d{1,3}$')
BC_RE = re.compile(
    r'B\)\s*(\d{4}/\d{2}/\d{2}/\d{4})\s+C\)\s*(PERM|\d{4}/\d{2}/\d{2}/\d{4})',
    re.IGNORECASE,
)
FG_RE = re.compile(
    r'\bF\)\s*([^\n]*?)\s+G\)\s*([^\n]+)', re.IGNORECASE,
)

# 军方/射击场条目常见措辞（压缩空白后）："5NMRADIUSOFAREACENTEREDONN390000E1170000"。
# 中间的填充词（OF AREA / AREA / POSITION 等）导致 common.extract_circle_area 的
# 严格模式不匹配，这里用允许间隔的宽松版本兜底。
# 另一类常见写法是圆心在前："CIRCLECENTEREDATN195905E1101121,WITHRADIUSOF130M"，
# 且 CAAC 常用纯米（M）作半径单位，统一换算成 KM。
LENIENT_CIRCLE_RE = re.compile(
    r'(?P<radius>\d+(?:\.\d+)?)(?P<unit>KM|NM|M)RADIUS.{0,60}?'
    r'CENTER(?:ED)?(?:ON|AT)?(?P<center>[NS]\d{4,6}[WE]\d{5,7}|\d{4,6}[NS]\d{5,7}[WE])',
    re.IGNORECASE,
)
CENTER_FIRST_CIRCLE_RE = re.compile(
    r'CENTER(?:ED)?(?:AT|ON)?'
    r'(?P<center>[NS]\d{4,6}[WE]\d{5,7}|\d{4,6}[NS]\d{5,7}[WE])'
    r'.{0,60}?RADIUS(?:OF|IS)?'
    r'(?P<radius>\d+(?:\.\d+)?)(?P<unit>KM|NM|M)\b',
    re.IGNORECASE,
)

_HEADER_MARKERS = (
    "PEOPLE'S REPUBLIC OF CHINA",
    'TELEGRAPHIC ADDRESS',
    'AFS:',
    'SITA:',
    'COMM:',
    'FAX:',
    'P.O.BOX',
    'AERONAUTICAL INFORMATION SERVICE',
    'CIVIL AVIATION ADMINISTRATION OF CHINA',
    'CIVIL AIR',
    'The following NOTAM',
    'canceled, time expired',
    'Summary',
)


def extract_text(pdf_bytes):
    """Extract the whole text of one summary PDF."""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return '\n'.join((page.extract_text() or '') for page in pdf.pages)


def split_entries(text):
    # Split one PDF text into entry chunks at "<series> <number>/<year> " lines.
    heads = list(ENTRY_HEAD_RE.finditer(text))
    chunks = []
    for index, head in enumerate(heads):
        end = heads[index + 1].start() if index + 1 < len(heads) else len(text)
        chunks.append(text[head.start():end])
    return chunks


def clean_entry(chunk):
    # Drop repeated page headers and standalone page-number lines.
    lines = []
    for line in chunk.splitlines():
        stripped = line.strip()
        if PAGE_NUMBER_RE.fullmatch(stripped):
            continue
        if any(marker in stripped for marker in _HEADER_MARKERS):
            continue
        lines.append(line)
    return '\n'.join(lines).strip()


def _format_site_time(value):
    parsed = datetime.datetime.strptime(value, '%Y/%m/%d/%H%M')
    return parsed.strftime('%d %b %H:%M %Y').upper()


def parse_time_window(chunk):
    # Convert B)/C) fields to the "dd MON HH:MM YYYY UNTIL ..." site format.
    match = BC_RE.search(chunk)
    if not match:
        return EMPTY_TIME
    start = _format_site_time(match.group(1))
    end_token = match.group(2).upper()
    end = PERMANENT_END if end_token == 'PERM' else _format_site_time(end_token)
    return f'{start} UNTIL {end}'


def parse_altitude(chunk):
    # Use F)/G) vertical limits when present; CAAC summaries have no Q-line.
    match = FG_RE.search(chunk)
    if not match:
        return 'None'
    lower = match.group(1).strip(' .,')
    upper = match.group(2).strip(' .,')
    if not lower or not upper:
        return 'None'
    return f'{lower} ~ {upper}'


def _lenient_circle(raw_message):
    # Fallback circular area for radius wording the strict matcher misses.
    compact = re.sub(r'\s+', '', normalize_coordinate_notation(raw_message))
    match = (LENIENT_CIRCLE_RE.search(compact)
             or CENTER_FIRST_CIRCLE_RE.search(compact))
    if not match:
        return ''
    center = standardize_coordinate(match.group('center'))
    radius = float(match.group('radius'))
    unit = match.group('unit').upper()
    if not center or radius <= 0:
        return ''
    if unit == 'M':
        # geometry 消费端只识别 KM/NM；米统一换算成 KM。
        unit = 'KM'
        radius = radius / 1000.0
        if radius < 0.01:
            return ''
    return f'CIRCLE|C={center}|R={radius:g}{unit}'


def parse_entries(text):
    # Parse one summary text into normalized records (source_type=CAAC).
    output = empty_data()
    for chunk in split_entries(text):
        raw_message = clean_entry(chunk)
        head = ENTRY_HEAD_RE.match(raw_message)
        if not head:
            continue
        code = f'{head.group(1)}{head.group(2)}'
        time_value = parse_time_window(raw_message)
        platid = f'CAAC:{code}'
        fir = extract_fir(raw_message, fallback='UNKNOWN')
        before = len(output['CODE'])
        add_area_records(
            output,
            code=code,
            raw_message=raw_message,
            time_value=time_value,
            platid=platid,
            fir=fir,
            source_type='CAAC',
        )
        if len(output['CODE']) == before:
            circle = _lenient_circle(raw_message)
            if circle:
                append_record(
                    output,
                    CODE=code,
                    TIME=time_value,
                    PLATID=platid,
                    RAWMESSAGE=raw_message,
                    ALTITUDE=parse_altitude(raw_message),
                    SOURCE='CAAC',
                    FIR=fir,
                    GEOMETRY=circle,
                )
    # add_area_records fills ALTITUDE from the Q-line, which CAAC lacks;
    # patch every row with the F)/G) vertical limits instead.
    for index, raw_message in enumerate(output['RAWMESSAGE']):
        output['ALTITUDE'][index] = parse_altitude(raw_message)
    return output


def parse_pdf(pdf_bytes):
    return parse_entries(extract_text(pdf_bytes))
