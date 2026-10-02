<div align="center">

# 🌐 NOTAM 航警地图 · NOTAM Map Viewer

![GitHub stars](https://img.shields.io/github/stars/sliverwolf233/notams?style=social)
![GitHub forks](https://img.shields.io/github/forks/sliverwolf233/notams?style=social)
![GitHub issues](https://img.shields.io/github/issues/sliverwolf233/notams)
[![Website](https://img.shields.io/badge/website-online-brightgreen)](https://sliverwolf233.github.io/notams/)
</div>

[English](#english) | [中文](#中文)

## Website: https://sliverwolf233.github.io/notams/ <br>

---

<a id="english"></a>
## English

This project parses NOTAMs and related maritime safety notices to extract rocket launch areas, debris zones, and restricted zones, then visualizes them on a map. It also includes historical archive matching, source reconciliation, image export, coordinate lookup, and distance measurement features.<br>

**If you find this project helpful, please consider giving it a ⭐ on GitHub. Your support helps us keep improving and adding new features.**

**This project is modified from [Joey0609/notams](https://github.com/Joey0609/notams) (originally FallingFengre/notams), redeployed by [sliverwolf233](https://github.com/sliverwolf233).**<br>

## <span style="font-weight:bold;">Disclaimer: This site only displays NOTAM information for reference and study. It is not a source of operational flight data — always consult official AIP / NOTAM publications for flight operations. Do not use this project for illegal purposes.</span>

### Project Overview

NOTAMs (Notice to Airmen) are aviation notices that warn pilots about temporary hazards, including restricted areas, debris zones, and other flight limitations. For rocket launch missions, these notices often contain the area boundary, effective time, notice number, and supporting remarks, making them an important source for identifying launch activity and hazard zones. The project parses these notices into structured coordinates and combines them with time windows and source metadata for unified display.

The current pipeline covers three main data sources: NOTAM notices, NGA MSI maritime safety information, and USCG NOTMAR. These sources do not share a single consistent text format, so the parser handles coordinate extraction, time normalization, area filtering, and deduplication before writing the final results to the map and local data files.

### Typical Format

NOTAMs often look like this:<br>

> A1690/23 - A TEMPORARY DANGER AREA ESTABLISHED BOUNDED BY: N392852E0955438-N385637E0955854-N390118E0970056-N393335E0965708 BACK TO START. VERTICAL LIMITS:SFC-UNL. SFC - UNL, 06 JUL 03:18 2023 UNTIL 06 JUL 04:45 2023. CREATED: 05 JUL 07:40 2023

In this example, “A1690/23” is the NOTAM serial number, the sequence of coordinates defines the hazard area, and “06 JUL 03:18 2023 UNTIL 06 JUL 04:45 2023” is the effective time window. The wording may vary across countries and sea areas, but the core information usually remains the same: notice ID, time range, and coordinate boundaries.

### Usage

After startup, the project automatically fetches data, generates structured results, and renders them on the map. The map focuses on information needed for current visibility and analysis rather than preserving every original notice in full. When the same event appears from multiple sources, the system keeps the most complete and interpretable fields and tries to avoid being overwritten by empty or default values.

#### Data-source selection

Providers are selected in `config.ini`:

```ini
[DATA_SOURCES]
enabled = faa, daip, msi, uscg, caac
```

This deployment enables all five active providers in priority order. Duplicate records with the same `SOURCE + CODE` keep the version from the first configured provider. `[ICAO] codes` supplies the shared location list.

Available providers are `faa`, `daip`, `dins` (legacy adapter), `msi` (legacy adapter), `uscg` (USCG NOTMAR), and `caac` (CAAC eAIP monthly NOTAM summary from eaipchina.cn; updates irregularly, the client scans back month by month for the latest issue). Provider-specific request and parsing code lives under `fetch/sources/<provider>/`. Every provider emits the same normalized fields, while `main.py` only performs aggregation, filtering, classification, and persistence.

The DAIP certificate chain is commonly absent from the Python/Certifi default trust store, so the sample configuration uses `verify_ssl = false`. Set it to `true` when the corresponding CA certificates are installed in the runtime environment.

```text
fetch/sources/
├── base.py
├── common.py
├── manager.py
├── faa/
├── daip/
├── dins/
├── msi/
├── uscg/
└── caac/
```

If you find a bug or want to improve the project, feel free to open an Issue or Pull Request.

**Open Source License and Third-Party Libraries**

This project uses the following third-party open-source software:

Leaflet v1.9.4  
Copyright (c) 2010-2025, Volodymyr Agafonkin  
License: BSD 2-Clause License  
Website: <https://leafletjs.cn/>  
License file: static/leaflet/LICENSE

---

<a id="中文"></a>
## 中文

本项目用于从 NOTAM 及相关海事安全信息中提取火箭发射、碎片落区及危险区坐标，并将其可视化展示在地图上。除了基础的区域绘制能力，网站还有历史归档、来源匹配、图片导出、经纬度查询、测距等功能。<br>

**如果你觉得这个项目有帮助，欢迎在 GitHub 上点个 ⭐。你的支持会鼓励我们持续改进并添加更多功能。谢谢！**

**本项目基于 [Joey0609/notams](https://github.com/Joey0609/notams)（原版 FallingFengre/notams）修改，由 [sliverwolf233](https://github.com/sliverwolf233) 部署维护。**<br>

## <span style="font-weight:bold;">免责声明：本站仅用于 NOTAM 航行通告的信息展示与学习交流，不构成任何飞行或运行依据。实际飞行运行请以官方 AIP / NOTAM 资料为准，请勿将本项目用于非法用途。</span>

### 项目概述

NOTAM（Notice to Airmen）是用于提示飞行活动风险的航空通告，其中常包含临时危险区、碎片落区、航行限制区等信息。对于火箭发射任务，这类通告往往会直接给出区域边界、有效时间、编号和补充说明，因此可以作为发射活动和危险区研判的重要数据来源。项目会把这些文本信息解析成结构化坐标，再结合时间窗口和来源标识进行统一展示。

当前项目主要覆盖三类数据：NOTAM 航警、NGA MSI 海警信息，以及 USCG NOTMAR 海事通告。不同来源的原文格式并不完全一致，因此解析链路会同时处理坐标提取、时间标准化、区域过滤和重复项去重，最终输出到前端地图和本地数据文件中。

### 典型格式

NOTAM 通常如下：  <br>

> A1690/23 - A TEMPORARY DANGER AREA ESTABLISHED BOUNDED BY: N392852E0955438-N385637E0955854-N390118E0970056-N393335E0965708 BACK TO START. VERTICAL LIMITS:SFC-UNL. SFC - UNL, 06 JUL 03:18 2023 UNTIL 06 JUL 04:45 2023. CREATED: 05 JUL 07:40 2023

其中，“A1690/23” 是 NOTAM 编号，“N392852E0955438-N385637E0955854-N390118E0970056-N393335E0965708” 一类内容是坐标点序列，围成的区域就是需要展示的危险区。“06 JUL 03:18 2023 UNTIL 06 JUL 04:45 2023” 则是有效时间，可用于判断事件窗口。不同国家和海域的通告措辞会有所变化，但核心信息通常仍然是编号、时间和坐标边界。

### 使用说明

项目启动后会自动抓取数据、生成结构化结果并绘制到地图中。地图侧重展示当前有效和可视化分析所需的信息，而不是保留每条原文的完整格式。若同一事件同时出现在不同来源，系统会优先保留更完整、可解释性更强的字段，并尽量避免被空值或默认值覆盖。

#### 数据源配置

数据源由 `config.ini` 的 `[DATA_SOURCES]` 选择。本站当前启用全部五个可用数据源，按优先级聚合（CAAC eAIP 月度汇总更新不定期，客户端会逐月回溯找最新一期）：

```ini
[DATA_SOURCES]
enabled = faa, daip, msi, uscg, caac
```

相同 `SOURCE + CODE` 的记录会保留先出现的数据源版本。`[ICAO] codes` 是所有航空 NOTAM 数据源共用的查询位置列表。当前可选模块为：

- `faa`：FAA NOTAM Search JSON 接口，支持位置查询以及 `freeform_terms` 自由文本查询。
- `daip`：DAIP Mobile JSON 接口，解析 `group[].notams[].list[]` 中的标准 NOTAM 原文。
- `dins`：旧 FAA DINS HTML 数据源的兼容适配器。
- `msi`：现有海事安全信息数据源的兼容适配器。
- `uscg`：USCG NAVCEN Local Notice to Mariners（NOTMAR）GeoJSON 数据源。
- `caac`：中国民航 eAIP NOTAM Summary 月度汇总（eaipchina.cn），覆盖国内长期有效区域航警。

每个模块负责自己的网络请求和原始响应解析，统一输出 `CODE`、`COORDINATES`、`TIME`、`PLATID`、`RAWMESSAGE`、`ALTITUDE`、`SOURCE`、`FIR`。主流程只负责聚合、区域过滤、有效期过滤、分类和落盘。

DAIP 当前使用的证书链通常不在 Python/Certifi 默认信任库内，因此示例配置为 `verify_ssl = false`。如果运行环境已经安装对应 CA 证书，应改为 `true`；也可以在 `DAIPClient` 中传入受信任 CA 文件路径后再启用校验。

#### 数据源目录

```text
fetch/sources/
├── base.py          # 统一接口、结果对象和字段结构
├── common.py        # 各航空数据源共用的 NOTAM 字段解析工具
├── manager.py       # 读取配置、加载模块、按配置顺序聚合去重
├── faa/             # FAA 请求、解析和数据源入口
├── daip/            # DAIP 请求、解析和数据源入口
├── dins/            # 旧 DINS 兼容适配器
├── msi/             # MSI 兼容适配器
├── uscg/            # USCG NOTMAR 数据源
└── caac/            # CAAC eAIP NOTAM Summary 月度汇总
```

新增数据源时，实现 `DataSource.fetch()` 并在 `fetch/sources/manager.py` 注册即可；其余业务层不需要修改。

欢迎提交 Pull Request 或 Issue 来帮助完善功能和修正问题！<br>

**开源许可与第三方库**

本项目使用了以下第三方开源软件：

Leaflet v1.9.4  
Copyright (c) 2010-2025, Volodymyr Agafonkin  
License: BSD 2-Clause License  
Website: <https://leafletjs.cn/>  
License file: static/leaflet/LICENSE
