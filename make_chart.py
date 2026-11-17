"""Buduje chart.html (krzywe kapitału i obsunięcia) z results.json.

Wykres jest rysowany tutaj jako statyczne SVG, więc działa też bez JavaScriptu;
skrypt w stronie dodaje tylko podgląd wartości pod kursorem.
"""
import json
import math

SHOW = ["Trend ostrożny (10% zmienności)", "Trend bez skalowania (50/50)", "Kup i trzymaj 50/50"]
SHORT = ["Trend ostrożny", "Trend bez skalowania", "Kup i trzymaj"]
COL = ["var(--s1)", "var(--s2)", "var(--s3)"]
W, ML, MR, MT, MB = 920, 48, 170, 8, 24

data = json.load(open("results.json"))
dates = data["dates"]
n = len(dates)
eq = [data["series"][s] for s in SHOW]


def drawdown(v):
    out, peak = [], -1.0
    for x in v:
        peak = max(peak, x)
        out.append(x / peak - 1)
    return out


dd = [drawdown(v) for v in eq]
pl = lambda x, d=1: f"{x:.{d}f}".replace(".", ",")
mult = lambda x: pl(x, 2) + "×"
pct = lambda x: pl(x * 100) + "%"


def svg(rows, h, ticks, fmt_tick, fmt, label, log=False, zero_top=False):
    f = math.log if log else (lambda x: x)
    flat = [x for r in rows for x in r]
    lo, hi = f(min(flat)), f(max(flat))
    if zero_top:
        hi = 0.0
    X = lambda i: ML + (W - ML - MR) * i / (n - 1)
    Y = lambda v: MT + (h - MT - MB) * (1 - (f(v) - lo) / (hi - lo))
    o = [f'<svg viewBox="0 0 {W} {h}" role="img" aria-label="{label}" data-h="{h}" data-lo="{lo}" data-hi="{hi}" data-log="{int(log)}">']
    for t in ticks:
        if lo <= f(t) <= hi:
            o.append(f'<line x1="{ML}" x2="{W-MR}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="var(--grid)"/>')
            o.append(f'<text x="{ML-6}" y="{Y(t)+4:.1f}" text-anchor="end">{fmt_tick(t)}</text>')
    seen = {dates[0][:4]}
    for i, d in enumerate(dates):
        if d[:4] not in seen:
            seen.add(d[:4])
            o.append(f'<line x1="{X(i):.1f}" x2="{X(i):.1f}" y1="{h-MB}" y2="{h-MB+4}" stroke="var(--axis)"/>')
            o.append(f'<text x="{X(i):.1f}" y="{h-6}" text-anchor="middle">{d[:4]}</text>')
    o.append(f'<line x1="{ML}" x2="{W-MR}" y1="{h-MB}" y2="{h-MB}" stroke="var(--axis)"/>')
    for k, r in enumerate(rows):
        path = "".join(f'{"M" if i == 0 else "L"}{X(i):.1f} {Y(v):.1f}' for i, v in enumerate(r))
        o.append(f'<path d="{path}" fill="none" stroke="{COL[k]}" stroke-width="2" stroke-linejoin="round"/>')
    # etykiety na końcach linii, rozsunięte, żeby się nie nakładały
    ends = sorted(((Y(r[-1]), k) for k, r in enumerate(rows)))
    placed = []
    for y, k in ends:
        if placed and y - placed[-1][0] < 15:
            y = placed[-1][0] + 15
        placed.append((y, k))
    for y, k in placed:
        o.append(f'<circle cx="{X(n-1):.1f}" cy="{Y(rows[k][-1]):.1f}" r="4" fill="{COL[k]}" stroke="var(--surface)" stroke-width="2"/>')
        o.append(f'<text class="lbl" x="{X(n-1)+10:.1f}" y="{y+4:.1f}">{SHORT[k]} {fmt(rows[k][-1])}</text>')
    o.append("</svg>")
    return "".join(o)


eq_svg = svg(eq, 360, [0.25, 0.5, 1, 2, 5, 10, 20, 50], lambda t: f"{t:g}".replace(".", ",") + "×", mult,
             "Wartość kapitału w czasie", log=True)
dd_svg = svg(dd, 240, [0, -0.2, -0.4, -0.6, -0.8], lambda t: f"{round(t*100)}%", pct,
             "Obsunięcie od szczytu w czasie", zero_top=True)
years = (n - 1) / 365
rows_html = "".join(
    f"<tr><td>{SHOW[k]}</td><td>{mult(eq[k][-1])}</td><td>{pct(eq[k][-1] ** (1 / years) - 1)}</td><td>{pct(min(dd[k]))}</td></tr>"
    for k in range(len(SHOW)))
legend = "".join(f'<span><i style="background:{COL[k]}"></i>{s}</span>' for k, s in enumerate(SHOW))

HTML = r"""<!doctype html>
<html lang="pl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Backtest trendu BTC/ETH</title>
<style>
:root{--surface:#fcfcfb;--page:#f9f9f7;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;
--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a}
@media (prefers-color-scheme:dark){:root{--surface:#1a1a19;--page:#0d0d0d;--ink:#f0efec;--ink2:#c3c2b7;--grid:#2c2c2a;--axis:#383835;
--s1:#3987e5;--s2:#d95926;--s3:#199e70}}
body{margin:0;padding:24px 16px;background:var(--page);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:960px;margin:0 auto}
h1{font-size:20px;margin:0 0 4px}
p.sub{margin:0 0 16px;color:var(--ink2)}
.card{background:var(--surface);border:1px solid var(--grid);border-radius:8px;padding:16px;margin-bottom:16px;position:relative}
h2{font-size:14px;margin:0 0 2px}
.note{color:var(--ink2);font-size:12px;margin:0 0 8px}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;margin:0 0 12px;font-size:13px;color:var(--ink2)}
.legend i{display:inline-block;width:14px;height:3px;border-radius:2px;margin-right:6px;vertical-align:middle}
.scroll{overflow-x:auto}
svg{width:100%;min-width:640px;height:auto;display:block}
svg text{fill:var(--muted);font-size:11px}
svg text.lbl{fill:var(--ink2);font-size:12px}
.tip{position:absolute;pointer-events:none;background:var(--surface);border:1px solid var(--axis);border-radius:6px;padding:8px 10px;font-size:12px;
box-shadow:0 2px 8px rgba(0,0,0,.15);display:none;white-space:nowrap;z-index:2}
.tip b{display:block;margin-bottom:4px}
.tip i{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
.tip span{float:right;margin-left:16px;font-variant-numeric:tabular-nums;color:var(--ink)}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{text-align:right;padding:6px 8px;border-bottom:1px solid var(--grid);font-variant-numeric:tabular-nums}
th:first-child,td:first-child{text-align:left}
th{color:var(--ink2);font-weight:600}
</style></head><body><main>
<h1>Podążanie za trendem kontra „kup i trzymaj”</h1>
<p class="sub">BTC i ETH na spocie, __START__ – __END__, koszt 0,15% na stronę. Symulacja historyczna, nie prognoza.</p>
<div class="legend">__LEGEND__</div>
<div class="card"><h2>Wartość kapitału</h2><p class="note">Kapitał początkowy = 1, skala logarytmiczna</p><div class="scroll" id="eq">__EQ__</div><div class="tip"></div></div>
<div class="card"><h2>Obsunięcie od szczytu</h2><p class="note">Spadek wartości względem dotychczasowego maksimum</p><div class="scroll" id="dd">__DD__</div><div class="tip"></div></div>
<div class="card"><h2>Podsumowanie</h2><div class="scroll"><table><tr><th>Wariant</th><th>Kapitał końcowy</th><th>Zwrot roczny</th><th>Najgłębsze obsunięcie</th></tr>__ROWS__</table></div></div>
</main>
<script>
const D=__DATA__,G=__GEOM__,NS="http://www.w3.org/2000/svg",n=D.dates.length;
const el=(t,a,p)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);p.appendChild(e);return e};
const pct=x=>(x*100).toFixed(1).replace(".",",")+"%",mult=x=>x.toFixed(2).replace(".",",")+"×";
function hover(id,rows,fmt){
  const host=document.getElementById(id),svg=host.querySelector("svg"),card=host.parentElement,tip=card.querySelector(".tip");
  const h=+svg.dataset.h,lo=+svg.dataset.lo,hi=+svg.dataset.hi,f=svg.dataset.log==="1"?Math.log:x=>x;
  const x=i=>G.ML+(G.W-G.ML-G.MR)*i/(n-1),y=v=>G.MT+(h-G.MT-G.MB)*(1-(f(v)-lo)/(hi-lo));
  const cross=el("line",{y1:G.MT,y2:h-G.MB,stroke:"var(--axis)",visibility:"hidden"},svg);
  const dots=rows.map((r,k)=>el("circle",{r:4,fill:G.COL[k],stroke:"var(--surface)","stroke-width":2,visibility:"hidden"},svg));
  const hit=el("rect",{x:G.ML,y:G.MT,width:G.W-G.ML-G.MR,height:h-G.MT-G.MB,fill:"transparent"},svg);
  hit.addEventListener("pointermove",ev=>{
    const b=svg.getBoundingClientRect(),sx=(ev.clientX-b.left)*G.W/b.width;
    const i=Math.max(0,Math.min(n-1,Math.round((sx-G.ML)/(G.W-G.ML-G.MR)*(n-1))));
    cross.setAttribute("x1",x(i));cross.setAttribute("x2",x(i));cross.setAttribute("visibility","visible");
    dots.forEach((d,k)=>{d.setAttribute("cx",x(i));d.setAttribute("cy",y(rows[k][i]));d.setAttribute("visibility","visible")});
    tip.innerHTML="<b>"+D.dates[i]+"</b>"+rows.map((r,k)=>'<div><i style="background:'+G.COL[k]+'"></i>'+G.SHORT[k]+"<span>"+fmt(r[i])+"</span></div>").join("");
    tip.style.display="block";
    const cb=card.getBoundingClientRect(),px=ev.clientX-cb.left;
    tip.style.left=(px>cb.width/2?px-tip.offsetWidth-14:px+14)+"px";tip.style.top=(ev.clientY-cb.top-10)+"px";
  });
  hit.addEventListener("pointerleave",()=>{tip.style.display="none";cross.setAttribute("visibility","hidden");dots.forEach(d=>d.setAttribute("visibility","hidden"))});
}
hover("eq",D.eq,mult);hover("dd",D.dd,pct);
</script></body></html>
"""

payload = {"dates": dates, "eq": eq, "dd": [[round(x, 4) for x in r] for r in dd]}
geom = {"W": W, "ML": ML, "MR": MR, "MT": MT, "MB": MB, "COL": COL, "SHORT": SHORT}
html = (HTML.replace("__DATA__", json.dumps(payload)).replace("__GEOM__", json.dumps(geom, ensure_ascii=False))
        .replace("__EQ__", eq_svg).replace("__DD__", dd_svg).replace("__ROWS__", rows_html)
        .replace("__LEGEND__", legend).replace("__START__", dates[0]).replace("__END__", dates[-1]))
open("chart.html", "w").write(html)
print("chart.html", len(html) // 1024, "KB")
