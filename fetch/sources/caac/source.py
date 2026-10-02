from ..base import DATA_FIELDS, DataSource, SourceResult, empty_data
from .client import CAACClient
from .parser import parse_pdf


class CAACDataSource(DataSource):
    """CAAC eAIP monthly NOTAM Summary (eaipchina.cn), location-independent."""

    name = 'caac'
    # 更新不定期且站点在国外访问不稳定；标记为可选，失败不阻塞主流程。
    optional = True

    def __init__(self, config, locations, client=None):
        super().__init__(config, locations)
        section = config['CAAC'] if config.has_section('CAAC') else {}
        self.client = client or CAACClient(
            base_url=section.get('base_url', 'https://www.eaipchina.cn/eaip'),
            timeout=int(section.get('timeout', 30)),
            months_back=int(section.get('months_back', 2)),
        )

    def fetch(self):
        try:
            documents = self.client.fetch_latest()
            if not documents:
                return SourceResult(
                    provider=self.name,
                    success=False,
                    error='当月与回溯月份的 CAAC NOTAM Summary 均下载失败',
                )
            merged = empty_data()
            for name, pdf_bytes in documents:
                parsed = parse_pdf(pdf_bytes)
                for field_name in DATA_FIELDS:
                    merged[field_name].extend(parsed[field_name])
            data = _dedupe_by_code(merged)
            return SourceResult(
                provider=self.name,
                data=data,
                success=bool(data.get('CODE')),
                error=None if data.get('CODE') else '解析结果为空',
                stats={'documents': len(documents), 'records': len(data.get('CODE', []))},
            )
        except Exception as exc:
            return SourceResult(provider=self.name, success=False, error=str(exc))


def _dedupe_by_code(data):
    # 同一 NOTAM 可能同时出现在当月与上月快照；按 CODE 保留先出现的（当月）。
    seen = set()
    output = empty_data()
    for index, code in enumerate(data.get('CODE', []) or []):
        if code in seen:
            continue
        seen.add(code)
        for field_name in DATA_FIELDS:
            values = data.get(field_name, []) or []
            output[field_name].append(str(values[index] if index < len(values) else ''))
    return output
