# Love Escalator Translation Tool

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows-lightgrey.svg)

**A translation quality check and management tool for PC-98 era visual novels**

[English](README.md) | [中文](README_zh.md)

</div>

---

## Table of Contents

- [About Love Escalator](#about-love-escalator)
- [Features](#features)
- [Screenshots](#screenshots)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Compatibility](#compatibility)
- [License](#license)

---

## About Love Escalator

**Love Escalator** (ラブ・エスカレーター) is a Japanese adult visual novel game released in **April 1998** for the **NEC PC-9800 series** (PC-98). It was developed by **Umitsuki Production** (海月製作所) and is often considered one of the last prominent PC-98 eroge.

### Game Story

The story follows Takashi Kurosaki, a high school student whose best friend Tooru Wakiya asks him to help win the heart of Rie Kawai - a girl Takashi secretly loved since middle school. As Takashi approaches Rie, he discovers she also had feelings for him all along. The game explores the complex emotional journey of two people reconnecting while keeping their relationship secret from their friend.

### Game Features

- **Genre**: Romance Anime ADV / Visual Novel
- **Release Date**: April 17, 1998
- **Platform**: PC-98 (DOS) / Windows 98
- **Developer**: Umitsuki Production
- **Notable**: Often called "PC-98's last eroge" due to its late release in the PC-98 era
- **Animation**: Rich animated sequences that were highly praised for their quality

---

## Features

### Core Functions

| Feature | Description |
|---------|-------------|
| 🔍 **Search & Filter** | Search through translations and filter by status |
| ⏭️ **Navigation** | Jump to specific ID, next/previous item |
| 🤖 **AI Translation** | Integration with Groq API for AI-powered translation suggestions |
| 💾 **Database Sync** | Two-way sync between SQLite database and JSON source file |
| 📋 **Batch Operations** | Export/backup database |

### Data Management

- **Translation Status Tracking**: Mark translations as fixed/verified
- **Statistics**: View total, translated, fixed counts
- **History**: Keep track of all modifications

### UI Features

- **Responsive Design**: Clean, modern interface
- **Character Counter**: Real-time character count for translations
- **XSS Protection**: Secure content rendering
- **Request Timeout**: Prevents hanging requests

---

## Screenshots

```
┌─────────────────────────────────────────────────────────────┐
│  翻译质量检查工具                                               │
│  [同步原文] [同步翻译] [⚙ 设置] [📖 查看教程]                              │
│  ⚠ 注意：同步即从原文件里重新提取内容到数据库...                            │
├─────────────────────────────────────────────────────────────┤
│  总记录数: 16968  已翻译: 12345  已确认: 8000  待确认: 3000          │
├──────────┬──────────────────────────────────────────────────┤
│ 跳转     │  ┌────┬─────┐                                    │
│ [____] → │  │ID  │原文 │                                    │
│ 搜索     │  ├────┼─────┤                                    │
│ [____] → │  │0001│今天 │ ← 选中行                           │
│ 过滤     │  │0002│明天 │                                    │
│ ☑显示已确认│  │0003│后天 │                                    │
│ [确认]   │  └────┴─────┘                                    │
├──────────┴──────────────────────────────────────────────────┤
│  ID: 0001 | 文件: dth.eqa | 索引: 0                          │
│  原文 (jp):                                                  │
│  ひな子ちゃんを誘って、ねりま園にやってきた。                   │
│                                                             │
│  选项 A - 当前翻译 (cn):                    [📋复制]          │
│  我邀请雏子酱，一起来到了练马园。                              │
│                                                             │
│  选项 B - AI建议: [🔄刷新] [📋复制]                         │
│  (加载中...)                                                │
│                                                             │
│  编辑区:                                                    │
│  ┌─────────────────────────────────────┐ [📋复制]           │
│  │                                     │                     │
│  └─────────────────────────────────────┘                     │
│  字数: 22                                                    │
│                                                             │
│                        [保存→跳转]                          │
└─────────────────────────────────────────────────────────────┘
                              [← 上一条] [下一条 →]
```

---

## Requirements

### System Requirements

- **OS**: Linux / Windows (WSL recommended for Windows)
- **Python**: 3.8+
- **Network**: For AI translation features (Groq API)

### Python Dependencies

- `requests` - HTTP library for API calls
- `sqlite3` - Built-in database support
- Standard library modules: `json`, `http.server`, etc.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/Love-escalator-translation-tool.git
cd Love-escalator-translation-tool

# Install dependencies (if needed)
pip install requests

# Start the server
python3 check_translation.py --port 5382
```

Or use the provided shell script:

```bash
chmod +x start.sh
./start.sh
```

---

## Usage

### Web Interface

Open your browser and navigate to:

```
http://localhost:5382
```

### Main Operations

1. **Initialize Database**: Click "同步原文" to sync original Japanese text
2. **Search**: Use the search box to find specific translations
3. **Filter**: Toggle "显示已确认" to show/hide verified entries
4. **Edit**: Modify translations in the editor area
5. **Save**: Click "保存→跳转" to save and move to next entry
6. **Navigation**: Use buttons or keyboard shortcuts to navigate

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main page |
| `/api/next` | GET | Get next unfixed item |
| `/api/update` | POST | Update translation |
| `/api/translate` | POST | AI translation |
| `/api/db/sync-jp` | POST | Sync original text from source |
| `/api/db/sync-cn` | POST | Sync translations from source |
| `/api/search` | GET | Search translations |

---

## Data Flow

```
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│   table.json    │────▶│  translation_status │◀───▶│   Web UI        │
│  (Source File)  │     │      .db            │     │  (Browser)     │
│                 │     │    (SQLite)         │     │                 │
│  - jp (原文)    │     │  - jp              │     │  - View/Edit    │
│  - cn (翻译)    │     │  - cn              │     │  - Navigation   │
│  - jpHex        │     │  - is_fixed        │     │  - AI Suggest   │
│  - cnHex        │     │  - is_translated   │     │                 │
└─────────────────┘     └─────────────────────┘     └─────────────────┘
        │                         │                         │
        │ 同步原文              更新翻译                  │
        └───────────────────────┴─────────────────────────┘
```

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3, http.server, SQLite |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Database** | SQLite |
| **Data Format** | JSON |

---

## Compatibility

### PC-98 Game Support

This tool is designed for **PC-98 era games** (1990s Japanese visual novels) and may be compatible with:

- Games using similar JSON-based translation data structures
- Visual novels with Japanese text requiring translation management
- PC-98 era games that have been extracted to text format

### Usage with loveEscalatorTL Project

**This tool is designed to work with the [loveEscalatorTL](https://github.com/dantecsm/loveEscalatorTL) project.**

The workflow is:
1. Use **loveEscalatorTL** to extract text from the original PC-98 game files and generate the `table.json` file
2. Use **this tool** to manage, review, and improve the translation quality
3. The translated data can then be integrated back into the game using loveEscalatorTL

### Extending to Other PC-98 Games

Due to the general-purpose design of the data structure, this tool can also be used for:
- Translation organization of other PC-98 visual novels
- Translation data management using similar JSON formats
- Any project requiring batch translation quality check

### Data Structure Requirements

The tool expects `table.json` in the following format:

```json
{
  "filename.eqa": [
    {
      "jp": "Japanese text",
      "cn": "Chinese translation",
      "jpHex": "...",
      "cnHex": "...",
      "startIdx": 123,
      "endIdx": 456
    }
  ]
}
```

---

## License

MIT License

Copyright (c) 2024

---

## Acknowledgments

- Love Escalator was developed by Umitsuki Production (海月製作所)
- Released in 1998 for PC-98 platform

---

## Disclaimer

This tool is for translation management purposes only. Please respect the original game's copyright and intellectual property rights when using this tool for translation work.

<div align="center">

**Happy Translating!** 🎮📝

</div>
