"""
晋江首页趋势分析脚本
用法：python jjwxc_analyzer.py
依赖：纯标准库，无需额外安装
需要：修改下方 GITHUB_TOKEN / GITHUB_OWNER / GITHUB_REPO 常量
"""

import base64
import json
import urllib.request
import urllib.error
from datetime import date
from html.parser import HTMLParser


# ── 配置 ──────────────────────────────────────────────
GITHUB_TOKEN = "your_token_here"   # 替换成你的 GitHub PAT
GITHUB_OWNER = "MaXXXineinurarea"
GITHUB_REPO  = "imeanyeah"
TODAY        = date.today().isoformat()   # e.g. 2026-04-10
OUTPUT_FILE  = f"jjwxc_trend_analysis_{TODAY}.md"

JJWXC_URLS = [
    "https://www.jjwxc.net/",
    "https://www.jjwxc.net/topten.php?orderby=marknum",
    "https://www.jjwxc.net/topten.php?orderby=commentnum&t=1",
]

GENRE_KEYWORDS = {
    "我在XX句式": ["我在"],
    "古代/古言":  ["古代", "古言", "古穿", "清穿", "皇"],
    "游戏/系统":  ["游戏", "系统", "BOSS", "副本"],
    "修仙/仙侠":  ["修仙", "仙", "师父", "师尊", "道"],
    "爽文/打脸":  ["始作俑者", "扫黑", "强者", "爽"],
    "甜宠/甜文":  ["欢迎", "做客", "甜"],
    "悬疑/权谋":  ["秘密", "同谋", "弑", "监狱"],
    "现代都市":   ["房间", "欢迎"],
    "穿越":       ["穿越", "穿"],
    "重生":       ["重生"],
    "星际":       ["星际", "联邦", "帝国"],
    "虫族":       ["虫族", "虫", "zerg"],
}


# ── 抓取标题 ─────────────────────────────────────────
class TitleParser(HTMLParser):
    """简单解析 <a> 标签内的文字作为候选标题"""
    def __init__(self):
        super().__init__()
        self.titles = []
        self._in_a = False
        self._buf = ""

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._in_a = True
            self._buf = ""

    def handle_endtag(self, tag):
        if tag == "a" and self._in_a:
            text = self._buf.strip()
            # 过滤：只保留2~30字且包含中文的标题
            if 2 <= len(text) <= 30 and any("\u4e00" <= c <= "\u9fff" for c in text):
                self.titles.append(text)
            self._in_a = False

    def handle_data(self, data):
        if self._in_a:
            self._buf += data


def fetch_titles(url: str) -> list[str]:
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; JJAnalyzer/1.0)"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("gbk", errors="replace")
        parser = TitleParser()
        parser.feed(html)
        return list(dict.fromkeys(parser.titles))   # 去重保序
    except Exception as e:
        print(f"  [warn] 抓取失败 {url}: {e}")
        return []


def collect_all_titles() -> list[str]:
    seen, result = set(), []
    for url in JJWXC_URLS:
        print(f"  抓取: {url}")
        for t in fetch_titles(url):
            if t not in seen:
                seen.add(t)
                result.append(t)
    return result


# ── 分析 ─────────────────────────────────────────────
def count_keywords(titles: list[str]) -> dict[str, int]:
    return {
        genre: sum(1 for t in titles if any(kw in t for kw in kws))
        for genre, kws in GENRE_KEYWORDS.items()
    }


def bar(n: int, total: int, width: int = 14) -> str:
    filled = round(n / total * width) if total else 0
    return "█" * filled + "░" * (width - filled)


def pct(n: int, total: int) -> str:
    return f"{round(n / total * 100)}%" if total else "0%"


def stars(n: int, base: int = 0) -> str:
    filled = min(5, n + base)
    return "★" * filled + "☆" * (5 - filled)


# ── 生成报告 ─────────────────────────────────────────
def build_report(titles: list[str], counts: dict[str, int]) -> str:
    total = len(titles) or 1
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    heat_rows = "\n".join(
        f"{genre:<14}  {bar(n, total)}  {pct(n, total)}"
        + ("  ← 本届MVP" if i == 0 else ("  ← 缺席" if n == 0 else ""))
        for i, (genre, n) in enumerate(sorted_counts)
    )

    title_rows = "\n".join(
        f"| {i+1} | {t} | — |"
        for i, t in enumerate(titles[:20])
    )

    return f"""# 晋江首页流量密码解码报告
> 数据采集日期：{TODAY}
> 数据来源：晋江文学城首页推荐、热门榜单（共采集 {len(titles)} 个标题）
> 声明：本报告含大量主观吐槽，请带着快乐阅读

---

## 原始数据：今日首页捞到的标题（前20条）

| # | 标题 | 推测类型 |
|---|------|---------|
{title_rows}

---

## 关键词词频热力图

```
{heat_rows}
```

---

## 类型五维评估表

| 维度 | 评分 | 说明 |
|------|------|------|
| 爽感 | {stars(counts.get("爽文/打脸", 0), 2)} | 打脸爽文、系统金手指全线出击 |
| 甜度 | {stars(counts.get("甜宠/甜文", 0), 2)} | 甜宠有但不是主角，师徒甜撑场 |
| 世界观深度 | ★★★☆☆ | 修仙/游戏做了点建构，其余较浅 |
| 悬疑反转 | {stars(counts.get("悬疑/权谋", 0), 1)} | 悬疑文今天不是主流 |
| 独立女性叙事 | ★★★★☆ | 「我」视角强，主角自主性高 |
| 星际/科幻 | {stars(counts.get("星际", 0))} | {"今天有" if counts.get("星际", 0) else "今天：全员缺席"} |
| 虫族 | {stars(counts.get("虫族", 0))} | {"今天有" if counts.get("虫族", 0) else "今天：全员缺席"} |

---

## 今日流行标题公式解析

### 公式 A：「我在XX做XX」型
> 结构：`我在 + [时空背景] + [离谱动词] + [反差宾语]`
>
> 造句：「我在星际扫地遇见了虫族皇帝」、「我在修仙界开了家奶茶店」

### 公式 B：「成为XX的我」型
> 结构：`成为 + [意外身份] + 的我`
>
> 变体：「成为反派亲妈的我躺平了」、「成为男主白月光的我想跑路」

### 公式 C：「我的XX超XX的」型
> 结构：`我的 + [关系词] + 超 + [形容词] + 的`
>
> 续集联动：「我的师父超有钱的，我的师兄超会撒娇的，我的系统超不靠谱的」

---

## 首席编辑吐槽专栏

**关于「我在XX」开头的书名：**
拜托，已经第108本了。但每次看到「我在[奇怪地点]做[离谱职业]」，还是会点进去。

**关于游戏文的爆发：**
游戏+系统是万能的——配古代=古穿游戏文，配现代=竞技文，配修仙=修仙系统文。

**关于星际虫族的缺席：**
你们去哪了？是在等皇帝蜕壳吗？首页没有你们，少了那股外激素味。

---

## 基于当前数据的爆款预测

> **《我在修仙界开了家黑心游戏公司》**
>
> 类型标签：`#修仙` `#游戏文` `#爽文` `#甜宠` `#系统` `#穿越` `#反派养成`

概率评估：**78.6%** 会在三个月内看到同款书名出现在首页。

---

## 总结

| 今天晋江在热的 | 今天晋江不在的 |
|-------------|-------------|
| 「我在X做X」句式 | 星际虫族 |
| 游戏系统文 | 末世丧尸 |
| 修仙爽文 | 豪门狗血 |
| 古言权谋 | ABO（今天） |
| 师徒甜宠 | 科幻硬核 |

**一句话总结：{TODAY} 的晋江首页，修仙游戏古言三足鼎立，穿越重生是背景色，虫族在等待时机卷土重来。**

---

*本报告由 jjwxc_analyzer.py 自动生成 | 数据来源：晋江文学城首页 | 分析手法：科学+胡说八道*
"""


# ── 上传到 GitHub ─────────────────────────────────────
def github_upload(content: str, filepath: str, message: str) -> str:
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{filepath}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "JJAnalyzer/1.0",
    }

    # 检查文件是否已存在，取 sha 用于更新
    sha = None
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            sha = json.loads(resp.read())["sha"]
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise

    payload: dict = {"message": message, "content": encoded}
    if sha:
        payload["sha"] = sha

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="PUT",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        return data["content"]["html_url"]


# ── 主流程 ───────────────────────────────────────────
if __name__ == "__main__":
    print("=== 晋江首页趋势分析 ===")
    print(f"分析日期：{TODAY}")
    print()

    print("[1/3] 抓取标题...")
    titles = collect_all_titles()
    print(f"  共获取 {len(titles)} 个标题")

    print("[2/3] 分析关键词...")
    counts = count_keywords(titles)
    for genre, n in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {genre:<14} {n} 本")

    print("[3/3] 生成报告并上传...")
    report = build_report(titles, counts)
    file_url = github_upload(
        report,
        OUTPUT_FILE,
        f"Auto: JJWXC trend analysis for {TODAY}",
    )
    print(f"  上传成功：{file_url}")
    print()
    print("完成！")
