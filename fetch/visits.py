"""访问量统计（可选功能）。

默认不抓取：未配置 VISITS_COUNTER_URL 时保留现有 visits.json 原样不动。
main.py 的主流程没有对本模块做异常保护，因此这里捕获全部异常，
统计失败绝不能影响航警抓取、历史匹配和通知发送。

如需启用：在 counter.dev 创建站点后，把控制台的 dump 链接（含 token）
配置到仓库 Secret / 环境变量 VISITS_COUNTER_URL 即可。
"""
import datetime
import json
import os

OUTPUT_FILE = "visits.json"

COUNTER_URL = os.getenv("VISITS_COUNTER_URL", "")
SITE = os.getenv("VISITS_SITE", "sliverwolf233.github.io")
PAGE = os.getenv("VISITS_PAGE", "/notams/")

HEADERS = {
    "Accept": "text/event-stream",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) notams-visits/1.0",
}


def update_visits():
    """更新 visits.json；任何失败都只记录日志，绝不抛出。"""
    if not COUNTER_URL:
        print("[info] 未配置 VISITS_COUNTER_URL，跳过访问量抓取（保留现有 visits.json）")
        return

    import requests

    today = datetime.date.today().isoformat()
    print("[info] 正在获取最新访问数据...")
    try:
        with requests.get(COUNTER_URL, headers=HEADERS, stream=True, timeout=10) as r:
            r.raise_for_status()
            for line in r.iter_lines(decode_unicode=True):
                if (line.startswith(' ') and '"type":"dump"' in line) or (line.startswith('data: {"type":"dump"')):
                    data = json.loads(line[6:])
                    visits = (
                        data.get("payload", {})
                        .get("sites", {})
                        .get(SITE, {})
                        .get("visits", {})
                        .get("all", {})
                        .get("page", {})
                        .get(PAGE, 0)
                    )
                    result = {
                        "value": visits,
                        "updated_at": today
                    }
                    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    print(f"[ok] 成功更新 {OUTPUT_FILE}: 访问量={visits}, 日期={today}")
                    return

        print("[error] 未找到有效的 dump 数据（已忽略，不影响主流程）")

    except Exception as e:
        print(f"[error] 获取访问数据失败（已忽略，不影响主流程）: {e}")


if __name__ == "__main__":
    update_visits()
