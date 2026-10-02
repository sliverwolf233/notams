"""Download CAAC eAIP NOTAM Summary packages from eaipchina.cn.

URL pattern (verified):
  https://www.eaipchina.cn/eaip/homeFile/NOTAM_SUMMARY/
      NOTAM%20Summary%20In%20Aug.2026/2026-08.zip?token=null
"""
import datetime
import io
import subprocess
import zipfile

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

MONTH_ABBREVIATIONS = (
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
)


class _TLSAdapter(HTTPAdapter):
    """ Relax cipher defaults; eaipchina.cn rejects Python's narrow default set."""

    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(ciphers='DEFAULT:@SECLEVEL=1')
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)


def notam_summary_urls(base_url: str, year: int, month: int):
    # Return candidate URLs for one month's summary zip.
    # 归档命名不统一：Aug 刊是 "2026-08.zip"，Apr 刊是
    # "NOTAM Summary In APR.2026.zip"，因此每个月份文件夹按多个候选名探测。
    index = month - 1
    capitalized = MONTH_ABBREVIATIONS[index]
    upper = capitalized.upper()
    folder = f'NOTAM%20Summary%20In%20{capitalized}.{year}'
    return [
        f'{base_url.rstrip("/")}/homeFile/NOTAM_SUMMARY/{folder}/{year}-{month:02d}.zip?token=null',
        f'{base_url.rstrip("/")}/homeFile/NOTAM_SUMMARY/{folder}/NOTAM%20Summary%20In%20{upper}.{year}.zip?token=null',
        f'{base_url.rstrip("/")}/homeFile/NOTAM_SUMMARY/{folder}/NOTAM%20Summary%20In%20{capitalized}.{year}.zip?token=null',
    ]


class CAACClient:
    def __init__(self, base_url='https://www.eaipchina.cn/eaip', timeout=30,
                 months_back=2, session=None):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.months_back = max(1, int(months_back))
        self.session = session or requests.Session()
        if not session:
            self.session.mount('https://', _TLSAdapter())

    def _download(self, url):
        # 优先 requests（放宽密码套件）；被服务器 TLS 指纹策略拒绝时回退 curl。
        try:
            response = self.session.get(
                url, timeout=self.timeout,
                headers={'User-Agent': 'Mozilla/5.0 notams-caac/1.0'},
            )
            response.raise_for_status()
            return response.content
        except Exception as exc:
            print(f'[CAAC] requests 通道失败，改用 curl: {exc}')
        result = subprocess.run(
            ['curl', '-sS', '-f', '-L', '--max-time', str(self.timeout),
             '-A', 'Mozilla/5.0 notams-caac/1.0', url],
            capture_output=True, timeout=self.timeout + 15,
        )
        if result.returncode != 0 or not result.stdout:
            raise RuntimeError(
                f'curl 下载失败 (exit={result.returncode}): '
                f'{result.stderr.decode("utf-8", "replace")[:200]}')
        return result.stdout

    def fetch_month(self, year, month):
        # Returns a list of (pdf_name, pdf_bytes) tuples, or [] on failure.
        for url in notam_summary_urls(self.base_url, year, month):
            try:
                content = self._download(url)
                if not content.startswith(b'PK'):
                    raise RuntimeError('响应不是 zip 归档（可能为 404 错误页）')
                documents = []
                with zipfile.ZipFile(io.BytesIO(content)) as archive:
                    for name in archive.namelist():
                        if name.upper().endswith('.PDF'):
                            documents.append((name, archive.read(name)))
            except Exception as exc:
                print(f'[CAAC] {year}-{month:02d} 候选下载失败: {exc}')
                continue
            print(f'[CAAC] {year}-{month:02d} 下载成功: {len(documents)} 个 PDF')
            return documents
        print(f'[CAAC] {year}-{month:02d} 所有候选包名均不可用')
        return []

    def fetch_latest(self, today=None):
        # 站点只保留最新一期汇总，且发布节奏不规律（可能滞后数月）。
        # 从当前月往回扫描，取第一个能下载到的月份即可：最新快照包含
        # 此前所有仍在生效的 NOTAM；失效条目由主流程按时间过滤。
        anchor = today or datetime.date.today()
        for offset in range(self.months_back):
            month_index = anchor.year * 12 + anchor.month - 1 - offset
            year, month = divmod(month_index, 12)
            month += 1
            found = self.fetch_month(year, month)
            if found:
                return found
        return []
