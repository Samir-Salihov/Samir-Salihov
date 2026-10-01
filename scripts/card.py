"""Brutalist neofetch-style profile card -> dist/card.svg
Runs in GitHub Actions (needs GITHUB_TOKEN, USERNAME)."""
import base64, datetime, json, os, random, sys, urllib.request
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER = os.environ.get("USERNAME", "Samir-Salihov")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.environ.get("OUT", os.path.join(ROOT, "dist", "card.svg"))

# ---- edit your info here ----
INFO = [
    ("Role",   "Backend developer / product analyst"),
    ("Stack",  "Python, DRF, PostgreSQL, Redis"),
    ("Focus",  "AI-driven engineering"),
    ("Next",   "System analysis"),
]
HIDE_LANGS = {"Jupyter Notebook"}
# ------------------------------

INK, YEL, BLUE, RED, WHITE, GREY = "#0A0A0A", "#FFE600", "#2B3BFF", "#FF3B1F", "#FFFFFF", "#8A8A8A"
LANG_COLORS = [INK, BLUE, YEL, RED, "#BDBDBD"]

QUERY = """
query($login: String!, $from: DateTime!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } }
      }
    }
    contributionsCollection(from: $from) {
      totalCommitContributions
      contributionCalendar { totalContributions }
    }
  }
}"""


def fetch():
    year_start = f"{datetime.date.today().year}-01-01T00:00:00Z"
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER, "from": year_start}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"})
    data = json.load(urllib.request.urlopen(req))
    if "errors" in data:
        sys.exit(f"GraphQL error: {data['errors']}")
    u = data["data"]["user"]
    langs = {}
    for r in u["repositories"]["nodes"]:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            if n not in HIDE_LANGS:
                langs[n] = langs.get(n, 0) + e["size"]
    return {
        "created": u["createdAt"][:10],
        "repos": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "followers": u["followers"]["totalCount"],
        "commits": u["contributionsCollection"]["totalCommitContributions"],
        "contribs": u["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "langs": langs,
    }


def uptime(created):
    c = datetime.date.fromisoformat(created)
    t = datetime.date.today()
    months = (t.year - c.year) * 12 + t.month - c.month - (t.day < c.day)
    y, m = divmod(max(months, 0), 12)
    parts = []
    if y: parts.append(f"{y} year{'s' * (y != 1)}")
    if m or not y: parts.append(f"{m} month{'s' * (m != 1)}")
    return ", ".join(parts)


def fonts():
    def b(n): return base64.b64encode(open(os.path.join(ROOT, "assets", n), "rb").read()).decode()
    return (f"@font-face{{font-family:'JB';font-weight:400;src:url(data:font/woff;base64,{b('jbmono-400.woff')}) format('woff')}}"
            f"@font-face{{font-family:'JB';font-weight:800;src:url(data:font/woff;base64,{b('jbmono-800.woff')}) format('woff')}}")


# 7x9 pixel "S"
S_GLYPH = ["0111110", "1100011", "1100000", "1110000", "0111110",
           "0000111", "0000011", "1100011", "0111110"]


def monogram(x0, y0, cell):
    rnd = random.Random(42)
    out = []
    for li in range(2):
        for r, row in enumerate(S_GLYPH):
            for c, bit in enumerate(row):
                if bit != "1":
                    continue
                x = x0 + li * (8 * cell) + c * cell
                y = y0 + r * cell
                color = INK
                roll = rnd.random()
                if roll < 0.10: color = YEL
                elif roll < 0.14: color = RED
                elif roll < 0.20: color = BLUE
                d = 0.3 + rnd.random() * 1.1
                out.append(f'<rect x="{x}" y="{y}" width="{cell-3}" height="{cell-3}" fill="{color}" '
                           f'stroke="{INK}" stroke-width="{2 if color != INK else 0}" class="px" style="animation-delay:{d:.2f}s"/>')
    return "\n".join(out)


def line(x, y, key, val, width, delay, cw=12):
    dots = "." * max(2, width - len(key) - len(str(val)) - 2)
    n = width
    return (f'<text x="{x}" y="{y}" class="ln"><tspan class="k">{escape(key)}</tspan>'
            f'<tspan class="d"> {dots} </tspan><tspan class="v">{escape(str(val))}</tspan></text>'
            f'<rect x="{x-2}" y="{y-20}" width="{n*cw+6}" height="28" class="wipe" '
            f'style="animation-delay:{delay:.2f}s;animation-timing-function:steps({max(n//2,4)},end)"/>')


def render(d):
    W, H, S = 1200, 572, 12
    cw_, ch_ = W - S, H - S
    X = 492
    out = []
    y = 124
    out.append(f'<text x="{X}" y="{y}" class="ln hd">{USER.lower().replace("-", "@", 1)}</text>'
               f'<rect x="{X-2}" y="{y-20}" width="300" height="28" class="wipe" style="animation-delay:.2s;animation-timing-function:steps(8,end)"/>')
    y += 30
    out.append(f'<line x1="{X}" y1="{y-10}" x2="{X+640}" y2="{y-10}" stroke="{INK}" stroke-width="3" class="rule"/>')
    info = INFO + [("Uptime", uptime(d["created"]))]
    delay = 0.45
    for k, v in info:
        y += 34
        out.append(line(X, y, k, v, 53, delay)); delay += 0.12

    y += 30
    out.append(f'<line x1="{X}" y1="{y-8}" x2="{X+640}" y2="{y-8}" stroke="{INK}" stroke-width="3" stroke-dasharray="6 6"/>')
    stats = [("Repos", d["repos"]), ("Stars", d["stars"]),
             ("Commits", d["commits"]), ("Contribs", d["contribs"])]
    for i in range(0, len(stats), 2):
        y += 34
        for j in range(2):
            k, v = stats[i + j]
            out.append(line(X + j * 336, y, k, v, 25, delay)); delay += 0.1

    # languages bar
    total = sum(d["langs"].values()) or 1
    top = [kv for kv in sorted(d["langs"].items(), key=lambda kv: -kv[1])[:5] if kv[1] / total >= 0.01][:4]
    y += 34
    bx, bw, by, bh = X, 640, y, 26
    out.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="{WHITE}" stroke="{INK}" stroke-width="3"/>')
    cx = bx
    shown = sum(s for _, s in top) or 1
    legend = []
    lx = X
    for i, (name, size) in enumerate(top):
        w = bw * size / shown
        col = LANG_COLORS[i % len(LANG_COLORS)]
        out.append(f'<rect x="{cx:.1f}" y="{by}" width="{w:.1f}" height="{bh}" fill="{col}" stroke="{INK}" stroke-width="3" '
                   f'class="seg" style="animation-delay:{delay + i*0.15:.2f}s"/>')
        cx += w
        label = f"{name} {size/total*100:.0f}%"
        legend.append(f'<rect x="{lx}" y="{by+44}" width="14" height="14" fill="{col}" stroke="{INK}" stroke-width="2"/>'
                      f'<text x="{lx+22}" y="{by+57}" class="lg">{escape(label)}</text>')
        lx += 22 + len(label) * 9.6 + 26
    out += legend

    body = "\n".join(out)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs><style>
{fonts()}
text{{font-family:'JB'}}
.ln{{font-size:20px;font-weight:400}}
.hd{{font-weight:800;fill:{INK}}}
.k{{fill:{BLUE};font-weight:800}}
.d{{fill:{GREY}}}
.v{{fill:{INK}}}
.lg{{font-size:16px;fill:{INK}}}
.bar{{font-size:18px;fill:{WHITE};font-weight:800}}
.wipe{{fill:{WHITE};transform-box:fill-box;transform-origin:right;animation:wipe .6s both}}
@keyframes wipe{{from{{transform:scaleX(1)}}to{{transform:scaleX(0)}}}}
.px{{animation:px .01s steps(1) both}}
@keyframes px{{from{{opacity:0}}to{{opacity:1}}}}
.seg{{transform-box:fill-box;transform-origin:left;animation:seg .35s steps(5,end) both}}
@keyframes seg{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
.blink{{animation:blink 1s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
</style></defs>
<rect x="{S}" y="{S}" width="{cw_}" height="{ch_}" fill="{BLUE}"/>
<rect x="2" y="2" width="{cw_-4}" height="{ch_-4}" fill="{WHITE}" stroke="{INK}" stroke-width="4"/>
<rect x="2" y="2" width="{cw_-4}" height="54" fill="{INK}"/>
<rect x="24" y="21" width="16" height="16" fill="{RED}"/>
<rect x="48" y="21" width="16" height="16" fill="{YEL}"/>
<rect x="72" y="21" width="16" height="16" fill="{BLUE}"/>
<text x="112" y="36" class="bar">~ $ neofetch --user {escape(USER)}</text>
<rect x="{112 + (len(USER) + 23) * 10.8 + 6:.0f}" y="20" width="11" height="20" fill="{YEL}" class="blink"/>
<line x1="450" y1="56" x2="450" y2="{ch_-2}" stroke="{INK}" stroke-width="4"/>
{monogram(44, 176, 25)}
<text x="44" y="{ch_-40}" class="lg" style="font-weight:800">since {d["created"][:4]}</text>
{body}
</svg>'''


if __name__ == "__main__":
    data = json.load(open(os.environ["MOCK"])) if os.environ.get("MOCK") else fetch()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write(render(data))
    print("written", OUT)
