import json
from data import R, ADP, EXP, EXPERT, TEAM_OFF, OL_RANKS, SOS, BRIDGE, ENV_EXEMPT
from version import VERSION, STAMP, DATA_DATE, out
from league import (DIVISIONS, SLOTS_BY_YEAR, QB_ROUNDS, TE_ROUNDS,
                    PLAYOFF_PER_DIV, DRAFT_ORDER_2026, MY_SLOT_2026)

OL = {t: rk for rk, t, _, _ in OL_RANKS}

# Projected season points by positional rank, non-PPR with the flat +5 TE bonus.
# Anchors come from the value-over-replacement work earlier in this project.
OL = {t: rk for rk, t, _, _ in OL_RANKS}
POS_SOS_COL = {"QB": 1, "RB": 2, "WR": 3, "TE": 4, "K": 0}
MIN_GAP, PROP = 10, 0.30

from scoring import build as _build, env_adj

players = []
for row in _build():
    name, pos, team = row["n"], row["p"], row["t"]
    rank = row["rank"]
    adj = rank - env_adj(team, pos, rank, name)
    sos = SOS[team][POS_SOS_COL.get(pos, 0)] if (pos != "DST" and team in SOS) else None
    players.append({
        "n": name, "p": pos, "t": team, "r": rank, "a": adj,
        "adp": ADP.get(name), "ex": EXPERT.get(name), "f": row["f"] or "",
        "o": None if pos == "DST" else TEAM_OFF.get(team),
        "ol": None if pos == "DST" else OL.get(team),
        "s": sos, "note": row["note"].strip(),
        "br": BRIDGE[name][0] if name in BRIDGE else None,
        "bw": BRIDGE[name][1] if name in BRIDGE else None,
        "bn": BRIDGE[name][2] if name in BRIDGE else None,
        "pts": row["pts"], "v": row["v"],
    })

for p in players:
    sigs = [v for v in (p["adp"], p["ex"]) if v is not None]
    if p["f"] or not sigs:
        continue
    thr = max(MIN_GAP, p["a"] * PROP)
    if min(sigs) <= p["a"] - thr:
        p["f"] = "DO NOT TOUCH"
    elif max(sigs) >= p["a"] + thr:
        p["f"] = "REACH OK"

players.sort(key=lambda x: (x["a"], x["r"]))
for i, p in enumerate(players):
    p["i"] = i
    p["bp"] = i + 1          # board position 1..N, what the UI shows

KNOWN = sorted({n for yr in SLOTS_BY_YEAR.values() for n in yr})

HIST = {
    "qbByR3": {str(y): sum(1 for x in v if x <= 3) for y, v in QB_ROUNDS.items()},
    "qbByR6": {str(y): sum(1 for x in v if x <= 6) for y, v in QB_ROUNDS.items()},
    "teByR3": {str(y): sum(1 for x in v if x <= 3) for y, v in TE_ROUNDS.items()},
    "slots": {str(y): v for y, v in SLOTS_BY_YEAR.items()},
}

CFG = json.dumps({
    "players": players, "known": KNOWN, "div": DIVISIONS,
    "perDiv": PLAYOFF_PER_DIV, "hist": HIST,
}, separators=(",", ":"))

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>The Vandelay Industry War Room</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --ink:#14181F; --panel:#1D232D; --panel2:#232B36; --line:#2C3542;
  --paper:#EDEFF2; --muted:#8A94A3; --dim:#5C6675;
  --te:#F2A93B; --rb:#5B9BD8; --wr:#3FB89B; --qb:#A98BE0; --util:#6B7684;
  --good:#3FB89B; --bad:#E2685F; --east:#7FB2E5; --west:#E8A2C0;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--ink);color:var(--paper);
  font-family:Inter,system-ui,sans-serif;-webkit-font-smoothing:antialiased}
body{padding:0 0 92px;overflow-x:hidden}
main,aside,.panel,.cols>*{min-width:0}   /* grid children must be allowed to shrink */
.logbox,#simout,#posblock{max-width:100%}
.wrap{max-width:1240px;margin:0 auto;padding:0 14px}
h2,h3{font-family:'Barlow Condensed',sans-serif;font-weight:600;letter-spacing:.12em;
  text-transform:uppercase}
h2{font-size:15px} h3{font-size:13px;color:var(--muted)}
.mono{font-family:'IBM Plex Mono',monospace}
.ver{color:var(--te);letter-spacing:.08em}

header{border-bottom:1px solid var(--line);background:var(--ink);position:sticky;top:0;
  z-index:60;padding-top:env(safe-area-inset-top)}
.mast{display:flex;align-items:baseline;gap:12px;padding:9px 0 7px;flex-wrap:wrap}
.brand{font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:25px;
  letter-spacing:.05em;text-transform:uppercase;line-height:1}
.brand em{font-style:normal;color:var(--te)}
.sub{font-family:'IBM Plex Mono',monospace;font-size:10px;color:var(--dim);
  letter-spacing:.1em;text-transform:uppercase;margin-top:3px}
.counts{margin-left:auto;display:flex;gap:15px;font-family:'IBM Plex Mono',monospace}
.counts b{display:block;font-size:16px;font-weight:600}
.counts span{color:var(--dim);font-size:9px;letter-spacing:.09em;text-transform:uppercase}
.onclock{font-family:'Barlow Condensed',sans-serif;font-size:15px;font-weight:600;
  padding:4px 11px;border-radius:2px;background:var(--panel2);letter-spacing:.04em}
.onclock.you{background:var(--te);color:var(--ink)}

.runwatch{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;background:var(--line);
  border-top:1px solid var(--line)}
.rw{background:var(--panel);padding:6px 9px 7px}
.rw-top{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:6px}
.rw-pos{font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:13px;letter-spacing:.09em}
.rw-left{font-family:'IBM Plex Mono',monospace;font-size:9.5px;color:var(--muted)}
.pips{display:flex;gap:3px}
.pip{height:5px;flex:1;border-radius:1px;background:var(--line)}
.pip.on{background:currentColor}
.rw.hot{animation:pulse 1.6s ease-in-out infinite}
@keyframes pulse{0%,100%{background:var(--panel)}50%{background:#2A2318}}
.rw-msg{font-family:'IBM Plex Mono',monospace;font-size:9px;margin-top:6px;color:var(--dim);min-height:11px}
.rw.hot .rw-msg{color:var(--te)}

.panel{background:var(--panel);border:1px solid var(--line);border-radius:3px;padding:13px;margin:14px 0}
details.setup summary{cursor:pointer;list-style:none;font-family:'Barlow Condensed',sans-serif;
  font-size:15px;letter-spacing:.12em;text-transform:uppercase;font-weight:600;
  display:flex;align-items:center;gap:9px}
details.setup summary::-webkit-details-marker{display:none}
details.setup summary::before{content:'▸';color:var(--te);font-size:12px}
details.setup[open] summary::before{content:'▾'}
.slots{display:grid;grid-template-columns:repeat(auto-fill,minmax(215px,1fr));gap:7px;margin-top:12px}
.slotrow{display:flex;align-items:center;gap:7px;background:var(--panel2);
  border:1px solid var(--line);border-radius:2px;padding:5px 8px}
.slotrow.me{border-color:var(--te)}
.slotnum{font-family:'IBM Plex Mono',monospace;font-size:11px;width:17px;color:var(--muted)}
.divtag{font-family:'IBM Plex Mono',monospace;font-size:8px;letter-spacing:.09em;
  padding:2px 4px;border-radius:2px}
.divtag.E{background:rgba(127,178,229,.16);color:var(--east)}
.divtag.W{background:rgba(232,162,192,.16);color:var(--west)}
.slotrow input{flex:1;min-width:0;background:transparent;border:0;color:var(--paper);
  font-family:'Barlow Condensed',sans-serif;font-size:15px;outline:none}
.slotrow input:focus{color:var(--te)}
.mebtn{font-family:'IBM Plex Mono',monospace;font-size:8.5px;letter-spacing:.07em;
  border:1px solid var(--line);background:transparent;color:var(--dim);border-radius:2px;
  padding:3px 6px;cursor:pointer}
.slotrow.me .mebtn{background:var(--te);color:var(--ink);border-color:var(--te)}

.simrow{display:flex;gap:7px;flex-wrap:wrap}
.sandbar{border-color:var(--te);border-left:3px solid var(--te)}
.brow{display:flex;gap:7px;flex-wrap:wrap}
.hide{display:none}
.tabs{display:flex;gap:0;background:var(--ink);border-top:1px solid var(--line)}
.tab{flex:1;background:transparent;border:0;border-bottom:3px solid transparent;
 color:var(--muted);font-family:'Barlow Condensed',sans-serif;font-size:14px;
 letter-spacing:.09em;text-transform:uppercase;font-weight:600;padding:10px 4px;
 cursor:pointer;min-width:0;white-space:nowrap}
.tab:hover{color:var(--paper)}
.tab[aria-pressed="true"]{color:var(--te);border-bottom-color:var(--te);
 background:rgba(242,169,59,.06)}
.tab:focus-visible{outline:2px solid var(--te);outline-offset:-2px}
.tab .badge{font-family:'IBM Plex Mono',monospace;font-size:9px;color:var(--dim);
 margin-left:5px;letter-spacing:0}
.tab[aria-pressed="true"] .badge{color:var(--te)}
.teampick{display:flex;align-items:center;gap:8px;margin:2px 0 10px;
 font-family:'IBM Plex Mono',monospace;font-size:9.5px;color:var(--dim);
 letter-spacing:.1em;text-transform:uppercase}
#dataBox{width:100%;background:var(--panel2);color:var(--paper);border:2px solid var(--te);
 border-radius:3px;padding:11px;font-family:'IBM Plex Mono',monospace;font-size:12px;
 margin-top:10px;resize:vertical;-webkit-appearance:none}
#dataBox:focus{outline:none;border-color:var(--te)}
.teampick select{flex:1;min-width:0;background:var(--panel2);color:var(--paper);
 border:1px solid var(--line);border-radius:2px;padding:8px 9px;
 font-family:'Barlow Condensed',sans-serif;font-size:15px}
.teampick select:focus-visible{outline:2px solid var(--te);outline-offset:2px}
.logbox.logfull{max-height:none}
.grade{display:flex;align-items:baseline;gap:16px;flex-wrap:wrap}
.gbig{font-family:'Barlow Condensed',sans-serif;font-size:60px;font-weight:700;
 line-height:.9;color:var(--te)}
.bar{height:6px;background:var(--line);border-radius:3px;overflow:hidden;margin-top:4px}
.bar i{display:block;height:100%;background:var(--te)}
.callout{border-left:3px solid var(--line);padding:9px 0 9px 12px;margin:9px 0;
 font-size:13px;line-height:1.55;color:var(--muted)}
.callout b{color:var(--paper)}
.callout.win{border-color:var(--good)} .callout.loss{border-color:var(--bad)}
.callout.note{border-color:var(--te)}
table.lg{width:100%;border-collapse:collapse;font-size:12px}
table.lg th{font-family:'IBM Plex Mono',monospace;font-size:9px;color:var(--dim);
 letter-spacing:.07em;text-transform:uppercase;text-align:right;padding:6px 4px;
 font-weight:400;border-bottom:1px solid var(--line)}
table.lg th:first-child,table.lg td:first-child{text-align:left}
table.lg td{padding:6px 4px;text-align:right;border-bottom:1px solid var(--line);
 font-family:'IBM Plex Mono',monospace;font-size:11px}
table.lg td.nm{font-family:'Barlow Condensed',sans-serif;font-size:14px}
table.lg tr.me td{background:rgba(242,169,59,.1)}
table.lg tr.rival td:first-child{color:var(--east)}
summary.rechead{cursor:pointer;list-style:none;display:flex;align-items:baseline;
 gap:9px;margin-bottom:2px}
summary.rechead::-webkit-details-marker{display:none}
summary.rechead::before{content:'\25be';color:var(--te);font-size:11px;flex-shrink:0}
details:not([open]) summary.rechead::before{content:'\25b8'}
summary.rechead .hint{margin-left:auto;text-align:right}
.simbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:14px;
 padding-top:13px;border-top:1px solid var(--line)}
.simbar select{max-width:100%;background:var(--panel2);color:var(--paper);border:1px solid var(--line);
 border-radius:2px;padding:7px 9px;font-family:'IBM Plex Mono',monospace;font-size:10.5px}
.target{border:1px solid var(--te);border-left-width:3px;border-radius:3px;padding:12px 14px;
 background:rgba(242,169,59,.07);margin-top:11px}
.target b{font-family:'Barlow Condensed',sans-serif;font-size:23px;font-weight:700;color:var(--te);
 letter-spacing:.03em}
.target .why{font-size:12.5px;color:var(--muted);line-height:1.5;margin-top:5px}
.target .why em{font-style:normal;color:var(--paper)}
.poscols{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(230px,100%),1fr));gap:9px;margin-top:9px}
.poscard{background:var(--panel2);border:1px solid var(--line);border-radius:3px;padding:10px;
 border-left:3px solid var(--line)}
.poscard h4{font-family:'Barlow Condensed',sans-serif;font-size:14px;letter-spacing:.1em;
 text-transform:uppercase;font-weight:600;margin-bottom:2px}
.poscard .drop{font-family:'IBM Plex Mono',monospace;font-size:9px;color:var(--dim);margin-bottom:7px}
.pline{display:flex;align-items:baseline;gap:7px;padding:3px 0;font-size:13px}
.pline .pn{font-family:'Barlow Condensed',sans-serif;font-size:14.5px;flex:1;min-width:0;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pline .pv{font-family:'IBM Plex Mono',monospace;font-size:9.5px;color:var(--muted)}
.surv{font-family:'IBM Plex Mono',monospace;font-size:9.5px;padding:1px 4px;border-radius:2px}
.surv.hi{color:var(--good)} .surv.mid{color:var(--te)} .surv.lo{color:var(--bad)}
.simrow2{display:flex;gap:9px;padding:5px 0;border-bottom:1px solid var(--line);align-items:baseline}
.simrow2:last-child{border-bottom:0}
.simrow2 .tm{font-family:'IBM Plex Mono',monospace;font-size:9.5px;color:var(--dim);width:96px;flex-shrink:0}
.simrow2 .pl{font-family:'Barlow Condensed',sans-serif;font-size:15px;flex:1}
.recs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin-top:11px}
@media(max-width:760px){.recs{grid-template-columns:1fr}}
.rec{background:var(--panel2);border:1px solid var(--line);border-radius:3px;padding:11px;
  border-top:2px solid var(--te);display:flex;flex-direction:column;gap:7px}
.rec-kind{font-family:'IBM Plex Mono',monospace;font-size:8.5px;letter-spacing:.11em;color:var(--te)}
.rec-nm{font-family:'Barlow Condensed',sans-serif;font-size:20px;font-weight:600;line-height:1.1}
.rec-why{font-size:12px;color:var(--muted);line-height:1.45;flex:1}
.rec-why b{color:var(--paper);font-weight:600}

.searchbar{position:relative;margin:14px 0 11px}
#q{width:100%;background:var(--panel);border:1px solid var(--line);color:var(--paper);
  font-family:'Barlow Condensed',sans-serif;font-size:21px;padding:12px 15px;border-radius:3px;outline:none}
#q:focus{border-color:var(--te)}
#q::placeholder{color:var(--dim)}
.results{position:absolute;top:calc(100% + 5px);left:0;right:0;background:var(--panel2);
  border:1px solid var(--line);border-radius:3px;z-index:50;max-height:54vh;overflow:auto;display:none}
.results.show{display:block}

.filters{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:11px}
.chip{background:transparent;border:1px solid var(--line);color:var(--muted);
  font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.08em;padding:6px 10px;
  border-radius:2px;cursor:pointer;text-transform:uppercase}
.chip[aria-pressed="true"]{background:var(--paper);color:var(--ink);border-color:var(--paper)}
.chip:focus-visible{outline:2px solid var(--te);outline-offset:2px}

.cols{display:grid;grid-template-columns:1fr 300px;gap:18px;align-items:start}
@media(max-width:900px){.cols{grid-template-columns:1fr}}
.secthead{display:flex;align-items:baseline;gap:9px;margin:0 0 8px}
.secthead .hint{font-family:'IBM Plex Mono',monospace;font-size:9px;color:var(--dim);margin-left:auto}

.row{display:flex;align-items:center;gap:10px;padding:8px 11px;border:1px solid var(--line);
  border-radius:3px;background:var(--panel);margin-bottom:5px;border-left-width:3px;cursor:pointer}
.row.sel{background:var(--panel2);border-color:var(--dim)}
.rk{font-family:'IBM Plex Mono',monospace;font-size:12px;color:var(--muted);width:26px;
  text-align:right;flex-shrink:0}
.who{min-width:0;flex:1}
.nm{font-family:'Barlow Condensed',sans-serif;font-weight:600;font-size:17px;line-height:1.15;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.meta{font-family:'IBM Plex Mono',monospace;font-size:9px;color:var(--dim);margin-top:2px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tag{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:8px;letter-spacing:.08em;
  padding:2px 5px;border-radius:2px;margin-left:5px;vertical-align:1px}
.tag.reach{background:rgba(63,184,155,.15);color:var(--good)}
.tag.avoid{background:rgba(226,104,95,.15);color:var(--bad)}
.tag.trap{background:rgba(242,169,59,.15);color:var(--te)}
.tag.gone{background:rgba(226,104,95,.13);color:var(--bad)}
.tag.cliff{background:rgba(169,139,224,.15);color:var(--qb)}
.tag.early{background:rgba(63,184,155,.16);color:var(--good)}
.tag.late{background:rgba(127,178,229,.16);color:var(--east)}
.btn{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.07em;padding:7px 10px;
  border-radius:2px;border:1px solid var(--line);background:transparent;color:var(--muted);
  cursor:pointer;text-transform:uppercase;white-space:nowrap}
.btn:hover{color:var(--paper);border-color:var(--dim)}
.btn.go{border-color:rgba(242,169,59,.5);color:var(--te)}
.btn.go:hover{background:var(--te);color:var(--ink)}
.btn:focus-visible{outline:2px solid var(--te);outline-offset:2px}
.note{font-size:12.5px;line-height:1.5;color:var(--muted);padding:9px 11px 11px 47px;
  border:1px solid var(--line);border-top:0;border-left-width:3px;border-radius:0 0 3px 3px;
  background:var(--panel2);margin:-6px 0 5px}

aside .slot{display:flex;align-items:center;gap:9px;padding:6px 0;border-bottom:1px solid var(--line)}
aside .slot:last-child{border-bottom:0}
.slotlbl{font-family:'IBM Plex Mono',monospace;font-size:9px;color:var(--dim);width:32px;letter-spacing:.08em}
.slotnm{font-family:'Barlow Condensed',sans-serif;font-size:15px}
.slotnm.empty{color:var(--dim);font-style:italic;font-size:12.5px;font-family:Inter,sans-serif}
.logbox{max-height:290px;overflow-y:auto;margin-top:2px}
.logrow{display:flex;gap:8px;align-items:baseline;padding:5px 0;border-bottom:1px solid var(--line)}
.logrow:last-child{border-bottom:0}
.logrow.mine{background:rgba(242,169,59,.08);margin:0 -6px;padding-left:6px;padding-right:6px}
.logno{font-family:'IBM Plex Mono',monospace;font-size:9px;color:var(--dim);width:38px;flex-shrink:0}
.logpl{font-family:'Barlow Condensed',sans-serif;font-size:14.5px;flex:1;min-width:0;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.logtm{font-family:'IBM Plex Mono',monospace;font-size:8.5px;color:var(--dim);
 max-width:78px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex-shrink:0}
.logrow.mine .logtm{color:var(--te)}
.logempty{color:var(--dim);font-size:12.5px;font-style:italic;padding:6px 0}
.needwrap{overflow-x:auto;max-width:100%}
.needgrid{width:100%;border-collapse:collapse;font-family:'IBM Plex Mono',monospace;font-size:9.5px;margin-top:7px}
.needgrid th{color:var(--dim);font-weight:400;text-align:center;padding:3px 2px;letter-spacing:.06em}
.needgrid td{text-align:center;padding:3px 2px;color:var(--dim);border-top:1px solid var(--line)}
.needgrid td.nm{text-align:left;color:var(--paper);font-family:'Barlow Condensed',sans-serif;
  font-size:12.5px;white-space:nowrap;max-width:96px;overflow:hidden;text-overflow:ellipsis}
.needgrid td.y{color:var(--te)}
.needgrid tr.me td{background:rgba(242,169,59,.09)}
.needgrid tr.rival td{background:rgba(127,178,229,.05)}
.needgrid tr.rival td.nm{color:var(--paper)}
.needgrid tr:not(.me):not(.rival) td.nm{color:var(--dim)}
.empty-state{border:1px dashed var(--line);border-radius:3px;padding:24px;text-align:center;
  color:var(--dim);font-size:13px}
footer{position:fixed;bottom:0;left:0;right:0;background:var(--ink);border-top:1px solid var(--line);
  padding:9px 14px calc(9px + env(safe-area-inset-bottom));display:flex;gap:8px;align-items:center;z-index:70}
.status{font-family:'IBM Plex Mono',monospace;font-size:10px;color:var(--dim);margin-right:auto}
.pos-RB{border-left-color:var(--rb)} .pos-WR{border-left-color:var(--wr)}
.pos-TE{border-left-color:var(--te)} .pos-QB{border-left-color:var(--qb)}
.pos-K,.pos-DST{border-left-color:var(--util)}
.c-RB{color:var(--rb)} .c-WR{color:var(--wr)} .c-TE{color:var(--te)}
.c-QB{color:var(--qb)} .c-K,.c-DST{color:var(--util)}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <div class="mast">
      <div>
        <div class="brand">The Vandelay Industry <em>War Room</em></div>
        <div class="sub">Scarborough &middot; Season XXV &middot; Non-PPR &middot; No flex &middot; TE premium &nbsp;&middot;&nbsp; <span class="ver">__STAMP__</span></div>
      </div>
      <div class="counts">
        <div><b id="cPick">1</b><span>Pick</span></div>
        <div><b id="cRound">1</b><span>Round</span></div>
        <div><b id="cNext">&mdash;</b><span>You&rsquo;re up in</span></div>
      </div>
      <span class="onclock" id="onclock">Set the board</span>
    </div>
  </div>
  <div class="runwatch" id="runwatch"></div>
  <nav class="tabs" id="tabs">
    <button class="tab" data-pane="board" aria-pressed="true">Board</button>
    <button class="tab" data-pane="rosters" aria-pressed="false">Rosters</button>
    <button class="tab" data-pane="log" aria-pressed="false">Draft log</button>
    <button class="tab" data-pane="study" id="tabStudy" aria-pressed="false" style="display:none">Slot study</button>
    <button class="tab" data-pane="data" aria-pressed="false">Data</button>
  </nav>
</header>

<div class="wrap">
  <div class="panel sandbar" id="sandbar" style="display:none">
    <div class="secthead"><h2>Sandbox</h2>
      <span class="hint">Nothing here touches your real draft</span></div>
    <p class="sub" style="margin:0 0 10px">Board pre-filled with last year&rsquo;s slots. Simulate the room so you can see the recommendations work before draft day.</p>
    <div class="simrow">
      <button class="btn" data-sim="1">Sim 1 pick</button>
      <button class="btn go" data-sim="turn">Sim to my turn</button>
      <button class="btn" data-sim="12">Sim a full round</button>
      <button class="btn" data-sim="round3">Jump to round 3</button>
      <button class="btn" data-sim="round10">Jump to round 10</button>
      <button class="btn" data-sim="slot">Random slot</button>
    </div>
  </div>

  <details class="panel setup" id="setup" open>
    <summary>Draft board setup</summary>
    <p class="sub" style="margin:9px 0 0">Name each slot, then tap ME on yours. Divisions follow the slot: East 1&middot;3&middot;5&middot;8&middot;10&middot;12, West 2&middot;4&middot;6&middot;7&middot;9&middot;11. Top 4 from each division make the playoffs.</p>
    <div class="slots" id="slots"></div>
    <datalist id="known"></datalist>
    <div id="divsum" class="sub" style="margin-top:11px"></div>
  </details>

  <details class="panel" id="recpanel" style="display:none" open>
    <summary class="rechead"><h2 id="rectitle">On the clock</h2>
      <span class="hint" id="recsub"></span></summary>

    <div id="target"></div>

    <h3 style="margin:14px 0 0">Top 3 overall</h3>
    <div class="recs" id="recs"></div>

    <div id="posblock"></div>

    <div class="simbar">
      <button class="btn go" id="runsim">Run simulation</button>
      <select id="simn">
        <option value="2000">2,000 runs · instant</option>
        <option value="10000" selected>10,000 runs · a second</option>
        <option value="50000">50,000 runs · ~10s</option>
        <option value="100000">100,000 runs · ~20s</option>
      </select>
      <span class="sub" id="simstatus">Simulates every pick between now and your next turn</span>
    </div>
    <div id="simout"></div>
    <div class="brow" id="simturnRecWrap" style="display:none;margin-top:12px">
      <button class="btn go" id="simturnRec">Sim to my turn</button>
    </div>
  </details>

  <div class="searchbar">
    <input id="q" type="text" autocomplete="off" autocapitalize="off" spellcheck="false"
           placeholder="Type the player just taken &mdash; Enter logs him to the team on the clock">
    <div class="results" id="results"></div>
  </div>

  <section id="paneBoard">
    <div class="filters" id="filters"></div>
    <div class="secthead"><h2>Best available</h2>
      <button class="btn go" id="simturnBoard" style="display:none;margin-left:auto">Sim to my turn</button>
      <span class="hint" id="boardhint">By adjusted rank</span></div>
    <div id="board"></div>
  </section>

  <section id="paneRosters" class="hide">
    <div class="panel" style="margin-top:0">
      <div class="secthead"><h2 id="rosterTitle">My team</h2><span class="hint" id="mypts"></span></div>
      <label class="teampick">Viewing
        <select id="teamSel"></select>
      </label>
      <div id="roster"></div>
    </div>
    <div class="panel">
      <div class="secthead"><h2>Who still needs what</h2>
        <span class="hint">Division rivals on top</span></div>
      <div class="needwrap"><table class="needgrid" id="needgrid"></table></div>
    </div>
  </section>

  <section id="paneStudy" class="hide">
    <div class="panel" style="margin-top:0">
      <div class="secthead"><h2>Slot study</h2>
        <span class="hint">All twelve slots, auto-drafted</span></div>
      <p class="sub" style="margin:8px 0 0;line-height:1.6">Runs a full auto-mock from every slot and reports what each tends to land and miss. You know you are at slot 12, so the useful reading is what that slot is short of.</p>
      <div class="brow" style="margin-top:11px">
        <button class="btn go" id="runStudy">Run all 12 slots</button>
      </div>
      <div id="studyout" style="margin-top:13px"></div>
    </div>
  </section>

  <section id="paneData" class="hide">
    <div class="panel" style="margin-top:0">
      <div class="secthead"><h2>Paste an update</h2><span class="hint" id="dataStamp"></span></div>
      <textarea id="dataBox" rows="7" placeholder="Paste the block Claude gave you here, then tap Apply update."></textarea>
      <div class="brow" style="margin-top:9px">
        <button class="btn go" id="dataApply">Apply update</button>
        <button class="btn" id="dataRevert">Revert to built-in</button>
      </div>
      <div id="dataMsg" class="sub" style="margin-top:10px;line-height:1.6"></div>
      <p class="sub" style="margin:12px 0 0;line-height:1.7">Saves in this browser and reloads every time. No rebuild, no re-upload, no cache to fight.</p>
    </div>
    <div class="panel">
      <div class="secthead"><h2>What an update can change</h2></div>
      <p class="sub" style="line-height:1.8">ADP &middot; expert ranks &middot; my rank &middot; offence rank &middot; O-line rank &middot; strength of schedule &middot; injury notes &middot; flags &middot; bridge windows. Anything not in the update keeps its current value, so a small paste is fine.</p>
    </div>
  </section>

  <section id="paneLog" class="hide">
    <div class="panel" style="margin-top:0">
      <div class="secthead"><h2>Draft log</h2><span class="hint" id="logcount"></span></div>
      <div id="log" class="logbox logfull"></div>
    </div>
  </section>
</div>

<div class="wrap"><section id="report" class="hide"></section></div>

<footer>
  <span class="status" id="status">Set your board to begin</span>
  <button class="btn go" id="simturnFoot" style="display:none">Sim to my turn</button>
  <button class="btn" id="grade" style="display:none">End &amp; grade</button>
  <button class="btn" id="export">Copy log</button>
  <button class="btn" id="undo">Undo</button>
  <button class="btn" id="reset">Reset</button>
</footer>

<script>
const CFG = __CFG__;
const SANDBOX = __SANDBOX__;
const PRESET = __PRESET__;      // 2026 draft order, drawn 18 Aug
const MY_SLOT = __MYSLOT__;     // Jeff, slot 12
const SKEY = SANDBOX ? 'warroom_sandbox' : 'warroom2026';
const P = CFG.players, TEAMS = 12;
const POS = ['RB','WR','TE','QB','K','DST'];
const START = {QB:1, RB:2, WR:2, TE:1, K:1, DST:1};
const SLOTS = [['QB','QB'],['RB','RB'],['RB','RB'],['WR','WR'],['WR','WR'],['TE','TE'],['K','K'],['DST','DST']];
const TE_TIER = P.filter(x=>x.p==='TE').slice(0,6);
const DIVOF = {};
CFG.div.East.forEach(s=>DIVOF[s]='E'); CFG.div.West.forEach(s=>DIVOF[s]='W');

let picks = [];               // {i} in draft order; slot derived from position
let names = Array(13).fill('');
let me = 0, filter = 'ALL', cursor = 0, openNote = null;

const $ = id => document.getElementById(id);
const takenSet = () => new Set(picks.map(p=>p.i));
const pickNumber = (r,s) => (r-1)*TEAMS + (r%2 ? s : TEAMS+1-s);
const slotOnClock = n => { const r=Math.floor(n/TEAMS)+1, k=n%TEAMS;
                           return r%2 ? k+1 : TEAMS-k; };

function nextPicks(count){
  if(!me) return [];
  const out=[], done=picks.length;
  for(let r=1;r<=20 && out.length<count;r++){ const n=pickNumber(r,me); if(n>done) out.push(n); }
  return out;
}
const picksAway = () => { const n=nextPicks(1)[0]; return n===undefined?null:n-picks.length-1; };
const turnGap  = () => nextPicks(2)[1];

/* ---------- storage ---------- */
async function save(){
  try{ if(window.storage) await withTimeout(window.storage.set(SKEY,
        JSON.stringify({picks, names, me, recOpen, pane, viewTeam})), 1500); }catch(e){}
}
function withTimeout(p, ms){        // a storage call that never settles must not freeze the app
  return Promise.race([p, new Promise(res=>setTimeout(()=>res(null), ms))]);
}
async function load(){
  try{ if(!window.storage) return;
    const r = await withTimeout(window.storage.get(SKEY), 1500);
    if(r&&r.value){ const d=JSON.parse(r.value);
      picks=d.picks||[]; names=d.names||names; me=d.me||0;
      if(d.recOpen!==undefined) recOpen=d.recOpen;
      if(d.pane) pane=d.pane; if(d.viewTeam!==undefined) viewTeam=d.viewTeam; }
  }catch(e){}
}

/* ---------- sandbox: simulate the rest of the room ----------
   Other managers are modelled as drafting near market order with some noise,
   not off my board - otherwise the sim just confirms my own rankings. */
function marketRank(p, round){
  const s=[p.adp, p.ex].filter(v=>v!==null&&v!==undefined);
  let r = s.length ? Math.min(...s) : p.a*1.4;
  // Scarborough runs hot on QB and TE versus national ADP: 6 QBs and 4 TEs
  // were gone by the end of round 3 last year. Bias the sim to match the
  // actual room, otherwise practising against it teaches the wrong reflexes.
  if(p.p==='QB' && round>=2 && round<=7) r *= 0.52;
  if(p.p==='TE' && round>=2 && round<=5) r *= 0.72;
  return r;
}
// Soft caps so simulated rosters stay plausible instead of hoarding one position
const ROSTER_ROUNDS = 14;   // rounds in a Scarborough draft
const REPL_JS = {RB:145, WR:138, TE:108, QB:320, K:146, DST:136};  // mirrors scoring.py
const SIMCAP = {RB:5, WR:5, TE:2, QB:1, K:1, DST:1};
function simOne(){
  const taken=takenSet(), slot=slotOnClock(picks.length);
  const round=Math.floor(picks.length/TEAMS)+1, need=needsOf(slot);
  const have={}; rosterOf(slot).forEach(x=>have[x.p]=(have[x.p]||0)+1);
  let pool=P.filter(p=>!taken.has(p.i))
    .filter(p=>!((p.p==='K'||p.p==='DST') && round<10))
    .filter(p=>!((p.p==='QB'||p.p==='K'||p.p==='DST') && need[p.p]===0))
    .filter(p=>(have[p.p]||0) < SIMCAP[p.p])
    .sort((a,b)=>marketRank(a,round)-marketRank(b,round));
  /* Late on, a manager stops taking best-available and fills his lineup.
     Without this the simulated teams finish with no kicker or defence, which
     both flatters your mock grade and distorts who is really left on the board. */
  let left=0;
  for(let r=1;r<=ROSTER_ROUNDS;r++){ const n=(r-1)*TEAMS+(r%2?slot:TEAMS+1-slot);
    if(n>picks.length) left++; }
  const unfilled=POS.reduce((t,q)=>t+need[q],0);
  if(unfilled>0 && left<=unfilled){
    const must=pool.filter(p=>need[p.p]>0);
    if(must.length) pool=must;
  }
  if(!pool.length) pool=P.filter(p=>!taken.has(p.i))
    .filter(p=>(have[p.p]||0) < SIMCAP[p.p])
    .sort((a,b)=>marketRank(a,round)-marketRank(b,round));
  if(!pool.length) return false;
  // weighted toward the top of the board, with a long-ish tail for reaches
  const span=candSpan(picks.length, pool.length);
  picks.push({i: pool[gaussIdx(span)].i});
  return true;
}
/* Consensus is tight at the top of a draft and loosens as it goes: nobody is
   passing on the consensus 1.01, but round 9 is a free-for-all. A fixed
   six-wide candidate window made Gibbs the first pick only 36% of the time and
   turned pick 2 into a five-way coin flip. Widen the window as the draft runs. */
function candSpan(idx, poolLen){
  return Math.max(1, Math.min(poolLen, Math.min(6, Math.ceil((idx+1)/8)+1)));
}
function gauss(){ let u=0,v=0; while(!u)u=Math.random(); while(!v)v=Math.random();
  return Math.sqrt(-2*Math.log(u))*Math.cos(2*Math.PI*v); }
function simN(n){ for(let k=0;k<n;k++){ if(!simOne()) break; } openNote=null; save(); renderAll(); }
function simToTurn(){
  if(!me){ alert('Tap ME on a slot first.'); return; }
  let guard=0;
  while(slotOnClock(picks.length)!==me && guard++<300){ if(!simOne()) break; }
  openNote=null; save(); renderAll();
}
function simToRound(r){
  const target=(r-1)*TEAMS;
  let guard=0;
  while(picks.length<target && guard++<300){ if(!simOne()) break; }
  if(me) simToTurn(); else { openNote=null; save(); renderAll(); }
}

/* ---------- rosters ---------- */
function rosterOf(slot){
  return picks.filter((p,k)=>slotOnClock(k)===slot).map(p=>P[p.i]);
}
function needsOf(slot){
  const have={}; rosterOf(slot).forEach(x=>have[x.p]=(have[x.p]||0)+1);
  const need={}; POS.forEach(pos=>need[pos]=Math.max(0,START[pos]-(have[pos]||0)));
  return need;
}

/* ---------- run watch ---------- */
const TIER = {TE:6, RB:12, WR:12, QB:6};
function runwatch(){
  const taken=takenSet(), recent=picks.slice(-12).map(p=>P[p.i].p);
  $('runwatch').innerHTML = ['TE','RB','WR','QB'].map(pos=>{
    const top=P.filter(x=>x.p===pos).slice(0,TIER[pos]);
    const left=top.filter(x=>!taken.has(x.i)).length, inRun=recent.filter(x=>x===pos).length;
    const hot = pos==='TE' ? (inRun>=2||left<=3) : (pos==='QB' ? inRun>=2 : inRun>=4);
    let msg;
    if(pos==='TE') msg = left===0?'Elite tier gone':left<=2?'Last of the tier — go now'
                        :inRun>=2?'Run starting':left+' of top 6 left';
    else if(pos==='QB') msg = inRun>=2?'QB run — 6 went by R3 last year':left+' of top 6 left';
    else msg = inRun>=4?'Run: '+inRun+' of last 12':left+' of top '+TIER[pos]+' left';
    return '<div class="rw'+(hot?' hot':'')+'"><div class="rw-top">'
      +'<span class="rw-pos c-'+pos+'">'+pos+'</span><span class="rw-left">'+left+'/'+TIER[pos]+'</span></div>'
      +'<div class="pips c-'+pos+'">'+top.map(x=>'<i class="pip'+(taken.has(x.i)?'':' on')+'"></i>').join('')+'</div>'
      +'<div class="rw-msg">'+msg+'</div></div>';
  }).join('');
}

/* ---------- forward simulation ----------
   Simulates only the picks between now and my next turn, many times over.
   That is the question that matters on the clock - who survives the round
   trip - and it is thousands of times cheaper than simulating full drafts. */
const ROUNDS_MAX = 18;
let simCache = null;   // SIMCAP and gauss() are declared once, further down
let recOpen = true;    // collapsed state of the recommendation panel, remembered
let pane = 'board';    // which tab is showing
const picked = new Set();   // active filter chips; empty means everything
let viewTeam = 0;      // slot whose roster is on screen; 0 means "me"

// Precompute market order per round once; the only round dependence is the
// QB/TE bias, so this turns each simulated pick into a short array walk.
const ORDER_BY_ROUND = (()=>{
  const out={};
  for(let r=1;r<=ROUNDS_MAX;r++){
    out[r]=P.map(p=>p.i).sort((x,y)=>mktRank(P[x],r)-mktRank(P[y],r));
  }
  return out;
})();
function mktRank(p, round){
  const s=[p.adp,p.ex].filter(v=>v!==null&&v!==undefined);
  let r = s.length?Math.min(...s):p.a*1.4;
  if(p.p==='QB' && round>=2 && round<=7) r*=0.52;   // this league runs hot on QB
  if(p.p==='TE' && round>=2 && round<=5) r*=0.72;
  return r;
}
/* Index within the candidate window. The spread must scale with the window:
   a fixed |gauss|*2 put 62% of the weight on the SECOND option when the window
   was two wide, i.e. it preferred the lesser player. span/3 keeps the top of
   the draft tight (87% on the consensus pick) and the later rounds loose. */
function gaussIdx(span){
  return Math.min(span-1, Math.floor(Math.abs(gauss())*span/3));
}
function baseCounts(){
  const c={}; for(let s=1;s<=TEAMS;s++){ c[s]={};
    rosterOf(s).forEach(x=>c[s][x.p]=(c[s][x.p]||0)+1); }
  return c;
}
function runSim(N, done, progress){
  const myNext = nextPicks(1)[0];
  if(!myNext){ done(null); return; }
  const start = picks.length, gap = myNext - start - 1;
  const takenNow = new Uint8Array(P.length);
  picks.forEach(p=>takenNow[p.i]=1);
  const base = baseCounts();
  const survive = new Int32Array(P.length);
  const byOffset = Array.from({length:gap}, ()=>new Int32Array(P.length));
  const bestSum = {}, POSL=['RB','WR','TE','QB','K','DST'];
  POSL.forEach(q=>bestSum[q]=0);
  let n=0;
  function chunk(){
    const stop = Math.min(N, n+Math.max(200, Math.floor(N/40)));
    for(; n<stop; n++){
      const taken = takenNow.slice();
      const cnt = {}; for(let s=1;s<=TEAMS;s++) cnt[s]=Object.assign({}, base[s]);
      for(let g=0; g<gap; g++){
        const idx=start+g, slot=slotOnClock(idx), round=Math.floor(idx/TEAMS)+1;
        const ord=ORDER_BY_ROUND[Math.min(round,ROUNDS_MAX)];
        const cands=[];
        for(let k=0;k<ord.length && cands.length<6;k++){
          const pi=ord[k]; if(taken[pi]) continue;
          const p=P[pi], have=cnt[slot][p.p]||0;
          if((p.p==='K'||p.p==='DST') && round<10) continue;
          if(have>=SIMCAP[p.p]) continue;
          cands.push(pi);
        }
        if(!cands.length) break;
        const pick=cands[gaussIdx(candSpan(idx, cands.length))];
        taken[pick]=1; cnt[slot][P[pick].p]=(cnt[slot][P[pick].p]||0)+1;
        byOffset[g][pick]++;
      }
      const bestPos={};
      for(let i=0;i<P.length;i++){
        if(taken[i]) continue;
        survive[i]++;
        const p=P[i];
        if(bestPos[p.p]===undefined || p.v>bestPos[p.p]) bestPos[p.p]=p.v;
      }
      POSL.forEach(q=>bestSum[q]+= (bestPos[q]!==undefined?bestPos[q]:-999));
    }
    if(progress) progress(n/N);
    if(n<N) setTimeout(chunk,0);
    else {
      const expBest={}; POSL.forEach(q=>expBest[q]=bestSum[q]/N);
      simCache={N, gap, myNext, survive, byOffset, expBest, at:start};
      done(simCache);
    }
  }
  chunk();
}

/* ---------- recommendation engine ---------- */
function tierGap(p, taken){
  const nxt = P.find(x=>x.p===p.p && x.i!==p.i && !taken.has(x.i) && x.a>p.a);
  return nxt ? nxt.a-p.a : null;
}
function scoreAll(){
  const taken=takenSet(), need=needsOf(me), round=Math.floor(picks.length/TEAMS)+1;
  const gap=turnGap(), avail=P.filter(x=>!taken.has(x.i));
  return avail.map(p=>{
    let sc = p.v, why=[];
    const isNeed = need[p.p]>0;
    let myLeft=0; for(let r=1;r<=ROSTER_ROUNDS;r++) if(pickNumber(r,me)>picks.length) myLeft++;
    const unfilled=POS.reduce((t,q)=>t+need[q],0), urgency=unfilled/Math.max(1,myLeft);
    /* Bench value has a ceiling. A second TE is real insurance and a trade chip
       in a premium league; a THIRD is dead weight, and without a cap the engine
       hoarded seven of them because tight-end VOR stays high all the way down. */
    const held = rosterOf(me).filter(x=>x.p===p.p).length;
    if(isNeed){ sc+=25+urgency*65; }
    else if(p.p==='QB'||p.p==='K'||p.p==='DST'){ sc-=400; }   // never a second one
    else if(held >= SIMCAP[p.p]){ sc-=400; }                  // past a useful bench count
    else { sc-=40; }                                          // ordinary bench depth
    if(p.f==='REACH OK'){ sc+=18; why.push('priced below where you rate him'); }
    /* Jeff leans on Cummings and Richard, so nudge toward their view - but CAP it.
       The format edge (non-PPR, no flex, TE premium) is the actual advantage;
       a national ranking must not be allowed to undo it. */
    if(p.ex!==null && p.ex!==undefined){
      const lean=Math.max(-15, Math.min(15, (p.a - p.ex)*0.5));
      sc+=lean;
      if(lean>=8) why.push('CBS experts rank him well above where he is going');
      if(lean<=-8) why.push('CBS experts are notably lower on him than this board');
    }
    if(p.f==='DO NOT TOUCH'){ sc-=40; }
    if(p.f==='NAME TRAP'){ sc-=15; }
    if((p.p==='K'||p.p==='DST') && round<11) sc-=350;
    const cliff = tierGap(p, taken);
    if(cliff!==null && cliff>=12 && isNeed){ sc+=20; why.push('next '+p.p+' is '+cliff+' spots later'); }
    const sv=survPct(p.i);
    if(sv!==null && isNeed && sv<0.35){ sc+=30;
      why.push('simulation has him back at your turn only '+Math.round(sv*100)+'% of the time'); }
    /* Scale the scarcity bonus by how likely he really is to be gone on the
       round trip. The old binary test (adp < gap-6) jumped from 0 to 28 across
       one pick, which is what let a lower-value player outrank a higher one. */
    let lastChance = false;
    if(gap && p.adp && isNeed){
      const backOdds = 1/(1+Math.exp((gap-p.adp)*0.35));
      sc += 30*(1-backOdds);
      lastChance = backOdds < 0.35;
      if(backOdds < 0.2) why.push('almost certainly gone before your next turn');
    }
    if(p.p==='TE' && need.TE>0){
      const teLeft = TE_TIER.filter(x=>!taken.has(x.i)).length;
      if(teLeft<=3){ sc+=35; why.push('only '+teLeft+' of the premium TE tier left'); }
    }
    if(p.p==='QB' && need.QB>0 && round>=3 && round<=5){
      sc+=20; why.push('this league takes QBs early — 6 gone by R3 last year');
    }
    // Bridge value. Front-loaded fill-ins only matter once the starters are set;
    // back-loaded returns matter because the title is decided in weeks 15-17.
    if(p.br==='EARLY' && round>=9){ sc+=28; why.push('starts for you while '+p.bw+' holds'); }
    if(p.br==='LATE'  && round>=6){ sc+=20; why.push('discounted for an absence that ends before the playoffs'); }
    return {p, sc, why, cliff, lastChance, isNeed};
  }).sort((a,b)=>b.sc-a.sc);
}
/* Rough chance a player is still there at my next pick, without running the
   full simulation - used to keep the off-clock recommendations honest. */
function likelyThere(p){
  const s=survPct(p.i);
  if(s!==null) return s;
  const nxt=nextPicks(1)[0];
  if(!nxt || !p.adp) return 1;
  /* Logistic on the gap between his ADP and my pick. A flat line was far too
     generous - it gave a 1.6-ADP player a 37% chance of lasting to pick 4. */
  const slack=nxt-p.adp;              // positive = his ADP is before my pick
  return Math.max(0.02, Math.min(0.99, 1/(1+Math.exp(slack*0.6))));
}
const KD_ROUND = 11;      // earliest round a kicker or defence may be suggested
const QB_ROUND = 2;       // nobody takes a QB in round 1 of a 1QB league
function recommend(){
  const rd = Math.floor(picks.length/TEAMS)+1;
  /* The score already punishes an early K/DST, but the CARD SELECTORS below
     scan for "first player who fills a need with a tier gap" - and once the
     skill slots are full the only needs left ARE K and DST. That handed back
     Brandon Aubrey in round 7. Remove them from the pool outright until late. */
  const ranked = scoreAll().filter(c =>
      !(['K','DST'].includes(c.p.p) && rd < KD_ROUND)
   && !(c.p.p==='QB' && rd < QB_ROUND));
  const taken=takenSet(), need=needsOf(me), gap=turnGap();
  const onClock = slotOnClock(picks.length)===me;
  const out=[], used=new Set();
  // "he will be gone" is incoherent on a card that exists because he should be there
  const reasons = c => onClock ? c.why
      : c.why.filter(x=>!/gone before your next turn|of the time/.test(x));
  const push=(cand,kind,why)=>{ if(cand && !used.has(cand.p.i)){ used.add(cand.p.i);
    out.push({kind, p:cand.p, why}); } };

  let R2;
  if(onClock){ R2 = ranked; }
  else {
    R2 = ranked
      .filter(c=>likelyThere(c.p)>=0.45)
      .map(c=>Object.assign({}, c, {sc: c.sc*likelyThere(c.p)}))
      .sort((a,b)=>b.sc-a.sc);
    if(!R2.length) R2 = ranked;
  }
  const best = R2[0];
  const bw = best ? reasons(best) : [];
  push(best, onClock ? 'BEST OVERALL' : 'BEST EXPECTED', best ? (bw.length
        ? cap(bw[0])+'. '+(onClock ? 'Highest adjusted value on the board that fits your lineup.'
                                   : 'Best value once his odds of lasting are priced in.')
        : (onClock ? 'Highest adjusted value on the board that still fits an open lineup slot.'
                   : 'Best combination of value and likelihood of still being there.')) : '');

  /* Cliff reasoning is about a POSITION, not a player. The old version found
     the man sitting immediately above the drop, which meant that with McBride
     (6) and Bowers (11) both up it skipped McBride - his gap to the next TE is
     only 5 - and recommended the WORSE tight end. Work out which position falls
     off soonest, then take the best player at it. */
  let scarce = null, cliffPos = null, cliffSize = 0;
  ['RB','WR','TE','QB'].forEach(q=>{
    if(!need[q]) return;
    const at = R2.filter(c=>c.p.p===q).sort((a,b)=>b.p.v-a.p.v);
    if(at.length<2) return;
    const drop = at[0].p.v - at[1].p.v;      // points lost by missing the top one
    if(drop > cliffSize){ cliffSize = drop; cliffPos = q; scarce = at[0]; }
  });
  if(scarce && used.has(scarce.p.i)) scarce = null;
  push(scarce, 'BEFORE THE CLIFF', scarce
    ? 'Best '+cliffPos+' on the board, and the next one down is worth <b>'
      +cliffSize.toFixed(0)+' points less</b> over the season. This is the tier, and it ends with him.'
    : '');

  const urgent = onClock ? R2.find(c=>c.isNeed && c.lastChance && !used.has(c.p.i)) : null;
  push(urgent, 'WON\'T LAST', urgent
    ? 'ADP <b>'+urgent.p.adp.toFixed(0)+'</b> and your next turn is pick <b>'+gap+'</b>. If you want him it has to be now.'
    : '');

  const round0 = Math.floor(picks.length/TEAMS)+1;
  if(round0>=9){
    const br = ranked.find(c=>c.p.br==='EARLY' && !used.has(c.p.i));
    push(br, 'BRIDGE STARTER', br
      ? '<b>'+br.p.bw+'.</b> '+br.p.bn+' Cheap now because season-long ranks average the window away.'
      : '');
  }
  if(!onClock){
    const shown = new Set(out.map(o=>o.p.p));
    const safe = R2.find(c=>c.isNeed && likelyThere(c.p)>=0.85
                        && !used.has(c.p.i) && !shown.has(c.p.p))
              || R2.find(c=>c.isNeed && likelyThere(c.p)>=0.85 && !used.has(c.p.i));
    push(safe, 'SAFE BET', safe
      ? 'Very likely still on the board when you pick, and he fills an open '+safe.p.p+' slot.' : '');
  }
  let k=1;
  while(out.length<3 && k<R2.length){
    const c=R2[k++];
    const shown2 = new Set(out.map(o=>o.p.p));
    if(!used.has(c.p.i) && (out.length<2 || !shown2.has(c.p.p)))
      push(c,'ALSO WORTH IT',
      c.isNeed ? 'Fills an open '+c.p.p+' slot at fair value.'
               : 'Best value left if you would rather take the talent and sort the lineup later.');
  }
  return out.slice(0,3);
}
const cap = s => s.charAt(0).toUpperCase()+s.slice(1);

function survPct(i){
  if(!simCache || simCache.at!==picks.length) return null;
  return simCache.survive[i]/simCache.N;
}
function survTag(i){
  const s=survPct(i); if(s===null) return '';
  const c = s>=0.7?'hi':(s>=0.35?'mid':'lo');
  return '<span class="surv '+c+'">'+Math.round(s*100)+'% back</span>';
}

/* Which position to spend this pick on: the one where waiting costs most.
   Compares the best available now against what the simulation expects to be
   there on the round trip. */
function positionTargets(){
  if(!simCache || simCache.at!==picks.length) return null;
  const taken=takenSet(), need=needsOf(me);
  const out=[];
  ['RB','WR','TE','QB','K','DST'].forEach(q=>{
    if(!need[q]) return;
    const nowBest=P.filter(p=>p.p===q&&!taken.has(p.i)).sort((a,b)=>b.v-a.v)[0];
    if(!nowBest) return;
    const later=simCache.expBest[q];
    out.push({pos:q, now:nowBest.v, later, drop:nowBest.v-later, top:
      P.filter(p=>p.p===q&&!taken.has(p.i)).sort((a,b)=>b.v-a.v).slice(0,3)});
  });
  return out.sort((a,b)=>b.drop-a.drop);
}
function renderTarget(){
  const t=positionTargets();
  if(!t||!t.length){ $('target').innerHTML=''; $('posblock').innerHTML=''; return; }
  const top=t[0];
  const round=Math.floor(picks.length/TEAMS)+1;
  $('target').innerHTML='<div class="target"><b>Target '+top.pos+'</b>'
    +'<div class="why">Best '+top.pos+' available is worth <em>'+top.now.toFixed(0)+'</em> over replacement. '
    +'Across '+simCache.N.toLocaleString()+' simulations of the next '+simCache.gap+' picks, the best one still there at pick '
    +simCache.myNext+' averages <em>'+top.later.toFixed(0)+'</em> — you lose <em>'+top.drop.toFixed(0)+' points</em> by waiting. '
    +(t.length>1?'The cheapest position to defer is '+t[t.length-1].pos+' (costs '+t[t.length-1].drop.toFixed(0)+').':'')
    +'</div></div>';
  $('posblock').innerHTML='<h3 style="margin:16px 0 0">Top 3 by position</h3><div class="poscols">'
    +t.map(x=>'<div class="poscard pos-'+x.pos+'"><h4 class="c-'+x.pos+'">'+x.pos+'</h4>'
      +'<div class="drop">now '+x.now.toFixed(0)+' → expected '+x.later.toFixed(0)
      +' &nbsp;·&nbsp; cost of waiting '+x.drop.toFixed(0)+'</div>'
      +x.top.map(p=>'<div class="pline"><span class="pn">'+p.n+'</span>'
        +'<span class="pv">'+(p.v>0?'+':'')+p.v.toFixed(0)+'</span>'+survTag(p.i)
        +'<button class="btn" data-act="pick" data-i="'+p.i+'">Log</button></div>').join('')
      +'</div>').join('')+'</div>';
}
function renderSim(){
  if(!simCache || simCache.at!==picks.length){ $('simout').innerHTML=''; return; }
  const rows=[];
  for(let g=0; g<simCache.gap; g++){
    const arr=simCache.byOffset[g];
    let bi=-1, bv=0;
    for(let i=0;i<arr.length;i++) if(arr[i]>bv){bv=arr[i]; bi=i;}
    if(bi<0) continue;
    const idx=simCache.at+g, slot=slotOnClock(idx);
    rows.push('<div class="simrow2"><span class="tm">'+(names[slot]||('Team '+slot))+'</span>'
      +'<span class="pl"><span class="c-'+P[bi].p+'">'+P[bi].p+'</span> '+P[bi].n+'</span>'
      +'<span class="pv mono" style="font-size:9.5px;color:var(--muted)">'
      +Math.round(bv/simCache.N*100)+'%</span></div>');
  }
  $('simout').innerHTML='<h3 style="margin:16px 0 6px">Most likely picks before your turn</h3>'
    +(rows.join('')||'<div class="sub">You are on the clock now.</div>')
    +'<p class="sub" style="margin-top:9px;line-height:1.6">Percentages are how often that team took that player across '
    +simCache.N.toLocaleString()+' runs. Even the top choice is usually well under half — the room is genuinely uncertain, '
    +'and a single most-likely name is far less reliable than the survival odds on the board.</p>';
}

function renderRecs(){
  const onSlot = slotOnClock(picks.length);
  const mine = me && onSlot===me;
  const rp = $('recpanel');
  rp.style.display = me ? 'block' : 'none';
  if(rp.open !== recOpen) rp.open = recOpen;
  if(!rp.dataset.wired){                      // wire the toggle exactly once
    rp.dataset.wired = '1';
    rp.addEventListener('toggle', () => { recOpen = rp.open; save(); });
  }
  if(!me) return;
  const away = picksAway();
  const nxt = nextPicks(1)[0];
  $('rectitle').textContent = mine ? 'You are on the clock' : 'Likely there at your pick';
  $('recsub').textContent = mine
    ? 'Round '+(Math.floor(picks.length/TEAMS)+1)+' · pick '+(picks.length+1)
    : away+' pick'+(away===1?'':'s')+' away · filtered to who should survive to pick '+nxt;
  renderTarget(); renderSim();
  const r = recommend();
  $('recs').innerHTML = r.length ? r.map(x=>
    '<div class="rec"><div class="rec-kind">'+x.kind+'</div>'
    +'<div class="rec-nm">'+x.p.n+'</div>'
    +'<div class="meta"><span class="c-'+x.p.p+'">'+x.p.p+'</span> · '+x.p.t
    +(x.p.adp?' · ADP '+x.p.adp.toFixed(0):'')+' · rank '+x.p.a+'</div>'
    +'<div class="rec-why">'+x.why
    +(slotOnClock(picks.length)===me ? ''
      : '<br><span class="mono" style="font-size:10px;color:var(--dim)">'
        +Math.round(likelyThere(x.p)*100)+'% chance he is still there</span>')+'</div>'
    +'<button class="btn go" data-act="pick" data-i="'+x.p.i+'">Log this pick</button></div>'
  ).join('') : '<div class="empty-state">Nobody left to recommend.</div>';
}

/* ---------- in-app data updates ----------
   The board is baked into this file, so refreshing it used to mean a rebuild,
   a download, a re-upload and a cache fight. Instead an update is a small JSON
   patch: paste it, it applies to the players by name and persists here. */
const DKEY = SKEY + '_data';
let dataStamp = 'built in';

function applyPatch(patch, quiet){
  if(!patch || !Array.isArray(patch.players)) throw new Error('no players array');
  const byName = {}; P.forEach(p=>byName[p.n]=p);
  let hit=0, missed=[];
  patch.players.forEach(u=>{
    const p = byName[u.n];
    if(!p){ missed.push(u.n); return; }
    hit++;
    // only overwrite what the patch actually carries
    if(u.adp!==undefined) p.adp=u.adp;
    if(u.ex!==undefined)  p.ex=u.ex;
    if(u.r!==undefined)   p.r=u.r;
    if(u.a!==undefined)   p.a=u.a;
    if(u.o!==undefined)   p.o=u.o;
    if(u.ol!==undefined)  p.ol=u.ol;
    if(u.s!==undefined)   p.s=u.s;
    if(u.f!==undefined)   p.f=u.f;
    if(u.note!==undefined)p.note=u.note;
    if(u.br!==undefined){ p.br=u.br; p.bw=u.bw||p.bw; p.bn=u.bn||p.bn; }
    if(u.pts!==undefined){ p.pts=u.pts; }
    if(u.v!==undefined){ p.v=u.v; }
  });
  P.sort((a,b)=>a.a-b.a);
  P.forEach((p,i)=>{ p.bp=i+1; });
  dataStamp = patch.stamp || 'updated';
  if(!quiet){
    $('dataMsg').innerHTML = '<b style="color:var(--good)">Applied.</b> '+hit
      +' players updated'+(missed.length? ', '+missed.length+' name'
      +(missed.length===1?'':'s')+' not on the board: '+missed.slice(0,4).join(', ')
      +(missed.length>4?'…':'') : '')+'. Stamp: '+dataStamp;
  }
  return {hit, missed};
}
async function saveData(txt){
  try{ if(window.storage) await withTimeout(window.storage.set(DKEY, txt), 1500); }catch(e){}
}
async function loadData(){
  try{
    if(!window.storage) return;
    const r = await withTimeout(window.storage.get(DKEY), 1500);
    if(r && r.value){ applyPatch(JSON.parse(r.value), true); }
  }catch(e){}
}
function renderData(){
  const el=$('dataStamp'); if(el) el.textContent = dataStamp;
}

/* ---------- slot study ----------
   Runs a complete auto-draft from each slot, several times, and compares the
   slots against EACH OTHER at every lineup position. Ranking positions inside
   one slot just returns RB and QB every time, because those score most in raw
   points regardless of where you pick. */
const STUDY_REPS = 5;
function fullSimForSlot(slot){
  const savePicks=picks, saveMe=me, saveCache=simCache;
  picks=[]; me=slot; simCache=null;
  while(picks.length < ROSTER_ROUNDS*TEAMS){
    if(slotOnClock(picks.length)===slot){
      const r=recommend(); if(!r.length) break;
      picks.push({i:r[0].p.i}); simCache=null;
    } else if(!simOne()) break;
  }
  const roster=rosterOf(slot);
  picks=savePicks; me=saveMe; simCache=saveCache;
  return roster;
}
function runSlotStudy(){
  $('studyout').innerHTML='<div class="sub">Running '+(TEAMS*STUDY_REPS)+' drafts, about ten seconds…</div>';
  setTimeout(()=>{
    const res=[];
    for(let s=1;s<=TEAMS;s++){
      let tot=0; const acc=new Array(SLOTS.length).fill(0);
      for(let rep=0;rep<STUDY_REPS;rep++){
        const L=lineupOf(fullSimForSlot(s));
        tot+=L.total;
        L.filled.forEach((f,j)=>{ acc[j]+= f.p ? (f.p.pts-REPL_JS[SLOTS[j][1]]) : 0; });
      }
      res.push({s, avg:tot/STUDY_REPS, shape:acc.map(a=>a/STUDY_REPS)});
    }
    const means=SLOTS.map((_,j)=>res.reduce((t,r)=>t+r.shape[j],0)/TEAMS);
    const best=Math.max(...res.map(r=>r.avg)), worst=Math.min(...res.map(r=>r.avg));
    const rows=res.map(r=>{
      const d=SLOTS.map((sl,j)=>({l:sl[0], v:r.shape[j]-means[j]})).sort((a,b)=>b.v-a.v);
      const gets=d.filter(x=>x.v>4).slice(0,2).map(x=>x.l+' +'+x.v.toFixed(0)).join(', ');
      const miss=d.filter(x=>x.v<-4).slice(-1).map(x=>x.l+' '+x.v.toFixed(0)).join('');
      return '<tr class="'+(r.s===me?'me':'')+'"><td class="nm">'+r.s+'</td><td>'+DIVOF[r.s]+'</td>'
        +'<td>'+r.avg.toFixed(0)+'</td><td>'+(r.avg-best>=0?'—':(r.avg-best).toFixed(0))+'</td>'
        +'<td style="text-align:left;color:var(--good)">'+(gets||'—')+'</td>'
        +'<td style="text-align:left;color:var(--bad)">'+(miss||'—')+'</td></tr>';}).join('');
    $('studyout').innerHTML=
      '<div style="overflow:auto"><table class="lg"><thead><tr><th>Slot</th><th>Div</th>'
      +'<th>Lineup</th><th>vs best</th><th style="text-align:left">Tends to land</th>'
      +'<th style="text-align:left">Tends to miss</th></tr></thead><tbody>'+rows+'</tbody></table></div>'
      +'<div class="callout note" style="margin-top:12px"><b>How to read it.</b> '
      +'&ldquo;Tends to land&rdquo; and &ldquo;tends to miss&rdquo; compare that slot against the other eleven '
      +'at the same lineup position, so <b>RB +50</b> means drafting there gets you a back roughly 50 points '
      +'better than the typical slot, and <b>TE &minus;30</b> means the premium tight ends are usually gone.</div>'
      +'<div class="callout"><b>Do not over-read it.</b> Best-to-worst spread is '+(best-worst).toFixed(0)
      +' points and the middle of the table shuffles on a re-run, because the simulated room drafts with '
      +'randomness. Only the large repeatable effects mean anything. The gap between a good and a bad draft '
      +'from the SAME slot is far larger than anything here.</div>';
  },30);
}

/* ---------- post-draft grading ----------
   Ported from the standalone mock so there is one practice tool, not two
   codebases drifting apart. */
function lineupOf(roster){
  const used=new Set(), filled=[];
  SLOTS.forEach(s=>{
    const c=roster.filter(m=>m.p===s[1]&&!used.has(m.i)).sort((a,b)=>b.pts-a.pts);
    if(c.length){ used.add(c[0].i); filled.push({slot:s[0], p:c[0]}); }
    else filled.push({slot:s[0], p:null});
  });
  return {filled, total:filled.reduce((t,f)=>t+(f.p?f.p.pts:0),0),
          bench:roster.filter(m=>!used.has(m.i))};
}
function letter(pct){
  return pct>=1.02?'A+':pct>=.99?'A':pct>=.96?'A-':pct>=.93?'B+':pct>=.90?'B'
        :pct>=.87?'B-':pct>=.84?'C+':pct>=.81?'C':pct>=.78?'C-':pct>=.74?'D':'F';
}
function showReport(){
  const teams=[];
  for(let s=1;s<=TEAMS;s++)
    teams.push({s, name:s===me?'YOU — '+(names[s]||'Vandelay')+' (slot '+s+')'
                              :(names[s]||('Team '+s)),
                L:lineupOf(rosterOf(s)), div:DIVOF[s]});
  const sorted=[...teams].sort((a,b)=>b.L.total-a.L.total);
  const mine=teams[me-1], rank=sorted.findIndex(t=>t.s===me)+1;
  const divT=teams.filter(t=>t.div===mine.div).sort((a,b)=>b.L.total-a.L.total);
  const divRank=divT.findIndex(t=>t.s===me)+1;

  const bySlot=SLOTS.map((s,k)=>{
    const vals=teams.map(t=>t.L.filled[k].p?t.L.filled[k].p.pts:0);
    return {label:s[0], mean:vals.reduce((a,b)=>a+b,0)/TEAMS,
            mine:mine.L.filled[k].p?mine.L.filled[k].p.pts:0,
            who:mine.L.filled[k].p?mine.L.filled[k].p.n:'— empty —'};
  });
  const edges=bySlot.map(x=>({...x, d:x.mine-x.mean})).sort((a,b)=>b.d-a.d);

  // counterfactual: at each of my picks, the best I could have taken instead
  const myIdx=[]; for(let k=0;k<picks.length;k++) if(slotOnClock(k)===me) myIdx.push(k);
  const misses=[];
  myIdx.forEach(k=>{
    const before=picks.slice(0,k), tk=new Set(before.map(p=>p.i));
    const have={}; before.forEach((p,j)=>{ if(slotOnClock(j)===me)
      have[P[p.i].p]=(have[P[p.i].p]||0)+1; });
    const nd={}; POS.forEach(q=>nd[q]=Math.max(0,START[q]-(have[q]||0)));
    const got=P[picks[k].i], rd=Math.floor(k/TEAMS)+1;
    const alt=P.filter(p=>!tk.has(p.i)&&nd[p.p]>0&&p.v>got.v
              && !(['K','DST'].includes(p.p)&&rd<ROSTER_ROUNDS-3))
              .sort((a,b)=>b.v-a.v)[0];
    if(alt && alt.v-got.v>15)
      misses.push({round:rd, got, alt, d:alt.v-got.v});
  });
  misses.sort((a,b)=>b.d-a.d);

  const best=(()=>{ const t=[];
    myIdx.forEach(k=>{ const before=picks.slice(0,k), tk=new Set(before.map(p=>p.i));
      const have={}; t.forEach(x=>have[x.p]=(have[x.p]||0)+1);
      const nd={}; POS.forEach(q=>nd[q]=Math.max(0,START[q]-(have[q]||0)));
      const rd=Math.floor(k/TEAMS)+1;
      const c=P.filter(p=>!tk.has(p.i)&&!t.some(y=>y.i===p.i)&&nd[p.p]>0
             && !(['K','DST'].includes(p.p)&&rd<ROSTER_ROUNDS-3))
             .sort((a,b)=>b.v-a.v)[0];
      if(c) t.push(c); });
    return lineupOf(t).total; })();
  const eff = best>0 ? mine.L.total/best : 0;

  const vals=myIdx.map(k=>({p:P[picks[k].i], pick:k+1,
    edge:P[picks[k].i].adp ? (k+1)-P[picks[k].i].adp : null})).filter(x=>x.edge!==null);
  const steals=[...vals].sort((a,b)=>b.edge-a.edge).slice(0,2);
  const reaches=[...vals].sort((a,b)=>a.edge-b.edge).slice(0,2);

  const rows=sorted.map((t,k)=>'<tr class="'+(t.s===me?'me':(t.div===mine.div?'rival':''))+'">'
    +'<td class="nm">'+(k+1)+'. '+t.name+'</td><td>'+t.div+'</td><td>'+t.L.total.toFixed(0)+'</td>'
    +SLOTS.map((s,j)=>'<td>'+(t.L.filled[j].p?t.L.filled[j].p.pts.toFixed(0):'—')+'</td>').join('')
    +'</tr>').join('');

  const strong=sorted.slice(0,3).map(t=>{
    const ed=SLOTS.map((s,j)=>({l:s[0], d:(t.L.filled[j].p?t.L.filled[j].p.pts:0)-bySlot[j].mean}))
      .sort((a,b)=>b.d-a.d).slice(0,2);
    return '<div class="callout note"><b>'+t.name+'</b> — '+t.L.total.toFixed(0)
      +' pts. Built on '+ed.map(e=>e.l+' (+'+e.d.toFixed(0)+' vs league)').join(' and ')+'.</div>';
  }).join('');

  $('report').classList.remove('hide');
  $('report').innerHTML=
   '<div class="panel"><div class="grade">'
   +'<div><div class="sub">Draft grade</div><div class="gbig">'+letter(eff)+'</div></div>'
   +'<div style="flex:1;min-width:210px"><div class="sub">Starting lineup</div>'
   +'<div style="font-family:\'Barlow Condensed\',sans-serif;font-size:30px">'+mine.L.total.toFixed(0)+' pts</div>'
   +'<div class="bar"><i style="width:'+Math.min(100,eff*100).toFixed(0)+'%"></i></div>'
   +'<div class="sub" style="margin-top:5px">'+(eff*100).toFixed(0)+'% of the best lineup reachable from your picks ('+best.toFixed(0)+')</div></div>'
   +'<div><div class="sub">League</div><div style="font-family:\'Barlow Condensed\',sans-serif;font-size:30px">'
   +rank+' of 12</div><div class="sub">'+mine.div+' division: '+divRank+' of 6 · '
   +(divRank<=CFG.perDiv?'<span style="color:var(--good)">makes playoffs</span>'
                        :'<span style="color:var(--bad)">misses</span>')+'</div></div></div></div>'

   +'<div class="panel"><h2>Where it went well</h2>'
   +(edges.filter(e=>e.d>8).slice(0,3).map(e=>'<div class="callout win"><b>'+e.label+' — '+e.who+'</b><br>'
     +e.mine.toFixed(0)+' pts against a league average of '+e.mean.toFixed(0)
     +'. <b>+'+e.d.toFixed(0)+'</b> on the field every week.</div>').join('')
    || '<div class="callout">No position clearly beat the field. Balanced, which in a 4-of-6 playoff format survives but rarely wins a title.</div>')
   +(steals.length&&steals[0].edge>8?'<div class="callout win"><b>Best value:</b> '
     +steals.map(s=>s.p.n+' at pick '+s.pick+' (ADP '+s.p.adp.toFixed(0)+')').join('; ')+'</div>':'')
   +'</div>'

   +'<div class="panel"><h2>Where it did not</h2>'
   +(edges.filter(e=>e.d<-8).slice(-3).reverse().map(e=>'<div class="callout loss"><b>'+e.label+' — '+e.who+'</b><br>'
     +e.mine.toFixed(0)+' pts against a league average of '+e.mean.toFixed(0)
     +'. <b>'+e.d.toFixed(0)+'</b> every week.</div>').join('')
    || '<div class="callout">No glaring hole. Nothing dragged the lineup down.</div>')
   +(reaches.length&&reaches[0].edge<-8?'<div class="callout loss"><b>Biggest reach:</b> '
     +reaches.map(s=>s.p.n+' at pick '+s.pick+' (ADP '+s.p.adp.toFixed(0)+')').join('; ')+'</div>':'')
   +'</div>'

   +'<div class="panel"><h2>What to do differently</h2>'
   +(misses.length?misses.slice(0,4).map(x=>'<div class="callout note">Round '+x.round
     +': you took <b>'+x.got.n+'</b> ('+x.got.v.toFixed(0)+' over replacement). <b>'+x.alt.n
     +'</b> was there at '+x.alt.v.toFixed(0)+' and filled the same kind of hole — <b>'
     +x.d.toFixed(0)+' points</b> left on the table.</div>').join('')
    :'<div class="callout note">Nothing material. At every pick you took at or near the best available player who fit an open slot.</div>')
   +'</div>'

   +'<div class="panel"><h2>Strongest teams and why</h2>'+strong+'</div>'

   +'<div class="panel"><h2>Full league</h2><div style="overflow:auto"><table class="lg"><thead><tr>'
   +'<th>Team</th><th>Div</th><th>Total</th>'+SLOTS.map(s=>'<th>'+s[0]+'</th>').join('')
   +'</tr></thead><tbody>'+rows+'</tbody></table></div>'
   +'<p class="sub" style="margin-top:10px;line-height:1.6">Points are estimates from a positional-rank curve built for this scoring, not a stat projection. Read the gaps between teams, not the absolute numbers.</p></div>'
   +'<div class="brow" style="margin-bottom:20px"><button class="btn" id="backToDraft">Back to the board</button></div>';
  $('backToDraft').onclick=()=>{ $('report').classList.add('hide');
    window.scrollTo(0,0); };
  window.scrollTo(0, $('report').offsetTop || 0);
}

/* ---------- rows ---------- */
function tag(f){ return f==='REACH OK'?'<span class="tag reach">REACH OK</span>'
  :f==='DO NOT TOUCH'?'<span class="tag avoid">AVOID AT ADP</span>'
  :f==='NAME TRAP'?'<span class="tag trap">NAME TRAP</span>':''; }
function metaLine(p){
  const b=[p.t]; if(p.adp)b.push('ADP '+p.adp.toFixed(1));
  if(p.o)b.push('OFF '+p.o); if(p.ol)b.push('OL '+p.ol); if(p.s)b.push('SOS '+p.s.toFixed(0));
  return b.join('  ·  ');
}
function rowHTML(p, sel, taken){
  const gap = taken?tierGap(p,taken):null, tg=turnGap();
  const cliff=(gap!==null&&gap>=12)?'<span class="tag cliff">CLIFF · NEXT '+p.p+' +'+gap+'</span>':'';
  const gone=(tg&&p.adp&&p.adp<tg-6)?'<span class="tag gone">GONE BY YOUR TURN</span>':'';
  const br = p.br==='EARLY'?'<span class="tag early">BRIDGE '+p.bw+'</span>'
           : p.br==='LATE' ?'<span class="tag late">PAYS OFF '+p.bw+'</span>':'';
  return '<div class="row pos-'+p.p+(sel?' sel':'')+'" data-i="'+p.i+'">'
    +'<span class="rk">'+p.bp+'</span>'
    +'<div class="who"><div class="nm">'+p.n+tag(p.f)+br+cliff+gone+survTag(p.i)+'</div>'
    +'<div class="meta"><span class="c-'+p.p+'">'+p.p+'</span>  ·  '+metaLine(p)+'</div></div>'
    +'<button class="btn go" data-act="pick" data-i="'+p.i+'">Log</button></div>'
    +(openNote===p.i&&(p.note||p.bn)
        ?'<div class="note pos-'+p.p+'">'
         +(p.bn?'<b>'+(p.br==='EARLY'?'Early window ':'Back-loaded ')+p.bw+'.</b> '+p.bn+'<br><br>':'')
         +(p.note||'')+'</div>':'');
}
function renderBoard(){
  const taken=takenSet();
  const list=P.filter(p=>!taken.has(p.i)&&passFilter(p)).slice(0,60);
  $('board').innerHTML = list.length?list.map(p=>rowHTML(p,false,taken)).join('')
    :'<div class="empty-state">Nobody left matching those filters.</div>';
  const bh=$('boardhint');
  if(bh) bh.textContent = picked.size
    ? [...picked].join(' + ')+' · '+list.length+' shown'
    : 'By adjusted rank';
}
const FILTERS=['ALL',...POS,'EARLY','LATE'];
const FLABEL={EARLY:'BRIDGE · EARLY', LATE:'BRIDGE · LATE'};
const BRIDGEF=new Set(['EARLY','LATE']);
function renderFilters(){
  $('filters').innerHTML=FILTERS.map(f=>{
    const on = f==='ALL' ? picked.size===0 : picked.has(f);
    return '<button class="chip" data-f="'+f+'" aria-pressed="'+on+'">'
      +(FLABEL[f]||f)+'</button>';
  }).join('');
}
/* Chips combine rather than replace, so RB + WR shows both. Positions OR
   together, bridge windows OR together, and the two groups AND with each
   other - "RB + WR + EARLY" means early-window backs and receivers. */
function passFilter(p){
  if(!picked.size) return true;
  const pos=[...picked].filter(f=>!BRIDGEF.has(f));
  const br=[...picked].filter(f=>BRIDGEF.has(f));
  if(pos.length && !pos.includes(p.p)) return false;
  if(br.length && !br.includes(p.br)) return false;
  return true;
}
function toggleFilter(f){
  if(f==='ALL'){ picked.clear(); }
  else if(picked.has(f)){ picked.delete(f); }
  else { picked.add(f); }
  renderFilters(); renderBoard();
}

/* ---------- setup ---------- */
function renderSetup(){
  $('known').innerHTML = CFG.known.map(n=>'<option value="'+n+'">').join('');
  $('slots').innerHTML = Array.from({length:TEAMS},(_,k)=>{
    const s=k+1;
    return '<div class="slotrow'+(me===s?' me':'')+'" data-s="'+s+'">'
      +'<span class="slotnum">'+s+'</span>'
      +'<span class="divtag '+DIVOF[s]+'">'+DIVOF[s]+'</span>'
      +'<input list="known" data-s="'+s+'" value="'+(names[s]||'')+'" placeholder="Team '+s+'">'
      +'<button class="mebtn" data-me="'+s+'">ME</button></div>';
  }).join('');
  if(me){
    const d=DIVOF[me], mates=(d==='E'?CFG.div.East:CFG.div.West).filter(s=>s!==me);
    $('divsum').innerHTML = 'You are slot <b style="color:var(--paper)">'+me+'</b>, '
      +(d==='E'?'East':'West')+' division. Your '+mates.length+' rivals for a playoff spot: '
      + mates.map(s=>'<b style="color:var(--paper)">'+(names[s]||('Team '+s))+'</b> ('+s+')').join(', ')
      + '. &nbsp;<b style="color:var(--te)">'+CFG.perDiv+' of these 6 make the playoffs</b> — you only have to '
      + 'finish ahead of '+(mates.length-CFG.perDiv)+'. The other division is irrelevant to your seeding, '
      + 'so these are the only rosters worth tracking closely.';
  } else $('divsum').textContent='';
}

/* ---------- roster + needs ---------- */
function showPane(p){
  pane = p;
  ['board','rosters','log','study','data'].forEach(x=>{
    const el=$('pane'+x.charAt(0).toUpperCase()+x.slice(1));
    if(el) el.classList.toggle('hide', x!==p);
  });
  document.querySelectorAll('.tab').forEach(t=>
    t.setAttribute('aria-pressed', String(t.dataset.pane===p)));
  // Switching tabs used to leave you wherever you had scrolled to, so the top
  // of the new pane was off screen. Jump back up.
  try{ window.scrollTo(0,0); }catch(e){}
  save();
}
function renderTabs(){
  const taken=takenSet();
  const avail=P.filter(x=>!taken.has(x.i)).length;
  const t=document.querySelector('.tab[data-pane="board"]');
  if(t) t.innerHTML='Board<span class="badge">'+avail+'</span>';
  const l=document.querySelector('.tab[data-pane="log"]');
  if(l) l.innerHTML='Draft log<span class="badge">'+picks.length+'</span>';
  const r=document.querySelector('.tab[data-pane="rosters"]');
  const slot=viewTeam||me;
  if(r) r.innerHTML='Rosters'+(slot?'<span class="badge">'+rosterOf(slot).length+'</span>':'');
}
function renderTeamSel(){
  const sel=$('teamSel'); if(!sel) return;
  const cur=String(viewTeam||me||1);
  sel.innerHTML=Array.from({length:TEAMS},(_,k)=>{
    const s=k+1, d=DIVOF[s];
    const label=(s===me?'YOU — ':'')+(names[s]||('Team '+s))+'  ·  slot '+s+' '+d
      +(me&&d===DIVOF[me]&&s!==me?'  · rival':'');
    return '<option value="'+s+'">'+label+'</option>';
  }).join('');
  sel.value=cur;
  if(!sel.dataset.wired){
    sel.dataset.wired='1';
    sel.onchange=()=>{ viewTeam=+sel.value; save(); renderRoster(); renderTabs(); };
  }
}
function renderRoster(){
  renderTeamSel();
  const slot = viewTeam || me;
  const title = $('rosterTitle');
  if(title) title.textContent = (slot===me) ? 'My team'
              : ((names[slot]||('Team '+slot))+"'s team");
  const mine = slot?rosterOf(slot):[]; const used=new Set(); const filled={};
  SLOTS.forEach((s,k)=>{ const h=mine.find(m=>m.p===s[1]&&!used.has(m.i));
    if(h){used.add(h.i);filled[k]=h;} });
  const tot=Object.values(filled).reduce((t,f)=>t+(f&&f.pts?f.pts:0),0);
  if($('mypts')) $('mypts').textContent = tot ? tot.toFixed(0)+' pts' : '';
  $('roster').innerHTML = SLOTS.map((s,k)=>{const f=filled[k];
    return '<div class="slot"><span class="slotlbl c-'+s[1]+'">'+s[0]+'</span>'
      +(f?'<span class="slotnm">'+f.n+'</span>':'<span class="slotnm empty">open</span>')+'</div>';}).join('')
    + (mine.filter(m=>!used.has(m.i)).length
        ? '<div style="margin-top:9px;padding-top:9px;border-top:1px solid var(--line)">'
          +'<div class="sub" style="margin-bottom:4px">Bench</div>'
          +mine.filter(m=>!used.has(m.i)).map(b=>'<div class="slotnm" style="font-size:13.5px">'
          +'<span class="c-'+b.p+' mono" style="font-size:9px">'+b.p+'</span> '+b.n+'</div>').join('')+'</div>'
        : '');
}
function renderNeeds(){
  const head='<tr><th style="text-align:left">Team</th><th></th>'
    +POS.map(p=>'<th>'+p+'</th>').join('')+'</tr>';
  // Division rivals first — they are the only teams you are racing for a spot.
  const order=[...Array(TEAMS).keys()].map(k=>k+1)
    .sort((a,b)=>{
      const ra=me&&DIVOF[a]===DIVOF[me]?0:1, rb=me&&DIVOF[b]===DIVOF[me]?0:1;
      return ra-rb || a-b; });
  const rows=order.map(s=>{
    const n=needsOf(s), rival = me && DIVOF[s]===DIVOF[me] && s!==me;
    return '<tr'+(me===s?' class="me"':(rival?' class="rival"':''))+'>'
      +'<td class="nm">'+(names[s]||('Team '+s))+'</td>'
      +'<td><span class="divtag '+DIVOF[s]+'">'+DIVOF[s]+'</span></td>'
      +POS.map(p=>'<td class="'+(n[p]>0?'y':'')+'">'+(n[p]>0?n[p]:'·')+'</td>').join('')+'</tr>';
  }).join('');
  $('needgrid').innerHTML=head+rows;
}
function renderLog(){
  const n=picks.length;
  $('logcount').textContent = n ? n+' of '+(ROUNDS_MAX*TEAMS>n?168:n)+' picks' : '';
  if(!n){ $('log').innerHTML='<div class="logempty">No picks logged yet.</div>'; return; }
  const out=[];
  for(let k=n-1;k>=0;k--){                 // newest at the top
    const s=slotOnClock(k), p=P[picks[k].i], rd=Math.floor(k/TEAMS)+1;
    out.push('<div class="logrow'+(s===me?' mine':'')+'">'
      +'<span class="logno">'+(k+1)+' · R'+rd+'</span>'
      +'<span class="logpl"><span class="c-'+p.p+'">'+p.p+'</span> '+p.n+'</span>'
      +'<span class="logtm">'+(s===me?'YOU':(names[s]||('Tm '+s)))+'</span></div>');
  }
  $('log').innerHTML=out.join('');
}
function renderCounts(){
  const n=picks.length, onSlot=slotOnClock(n);
  $('cPick').textContent=n+1;
  $('cRound').textContent=Math.floor(n/TEAMS)+1;
  const away=picksAway();
  $('cNext').textContent = me?(away===0?'NOW':away+' picks'):'—';
  const oc=$('onclock');
  oc.textContent = (names[onSlot]||('Team '+onSlot))+' · '+DIVOF[onSlot];
  oc.className = 'onclock'+(me&&onSlot===me?' you':'');
  const last=picks[picks.length-1];
  $('status').textContent = last
    ? 'Pick '+n+': '+P[last.i].n+' → '+(names[slotOnClock(n-1)]||('Team '+slotOnClock(n-1)))
    : (me?'Ready — '+(names[onSlot]||('Team '+onSlot))+' is on the clock':'Set your board to begin');
}
function renderAll(){ runwatch(); renderBoard(); renderRoster(); renderNeeds();
                      renderLog(); renderCounts(); renderRecs(); renderTabs(); search(); }

/* ---------- actions ---------- */
function draft(i){
  if(picks.some(p=>p.i===+i)) return;
  picks.push({i:+i}); openNote=null; simCache=null; save(); $('q').value=''; cursor=0; renderAll();
}
function doSim(){
  const N=+$('simn').value;
  $('runsim').disabled=true;
  runSim(N, res=>{ $('runsim').disabled=false;
      $('simstatus').textContent = res
        ? N.toLocaleString()+' runs over the next '+res.gap+' picks'
        : 'No further picks to simulate';
      renderAll(); },
    f=>{ $('simstatus').textContent='Running… '+Math.round(f*100)+'%'; });
}
document.addEventListener('click', e=>{
  const b=e.target.closest('[data-act="pick"]'); if(b){ draft(b.dataset.i); return; }
  const m=e.target.closest('[data-me]'); if(m){ me=+m.dataset.me; save(); renderSetup(); renderAll(); return; }
  const tb=e.target.closest('[data-pane]'); if(tb){ showPane(tb.dataset.pane); return; }
  const c=e.target.closest('[data-f]'); if(c){ toggleFilter(c.dataset.f); return; }
  const row=e.target.closest('.row'); if(row){ const i=+row.dataset.i;
    openNote=(openNote===i?null:i); renderBoard(); return; }
  const sim=e.target.closest('[data-sim]');
  if(sim){
    const v=sim.dataset.sim;
    if(v==='turn') simToTurn();
    else if(v==='slot'){ me=1+Math.floor(Math.random()*TEAMS); save(); renderSetup(); renderAll(); }
    else if(v==='round3') simToRound(3);
    else if(v==='round10') simToRound(10);
    else simN(+v);
  }
});
document.addEventListener('input', e=>{
  if(e.target.matches('input[list="known"]')){ names[+e.target.dataset.s]=e.target.value;
    save(); renderNeeds(); renderCounts(); renderSetup2(); }
});
function renderSetup2(){ if(me) renderSetup(); }
$('undo').onclick=()=>{ picks.pop(); simCache=null; save(); renderAll(); };
$('runsim').onclick=doSim;
if($('runStudy')) $('runStudy').onclick=runSlotStudy;
if($('dataApply')) $('dataApply').onclick=()=>{
  const txt=$('dataBox').value.trim();
  if(!txt){ $('dataMsg').textContent='Paste an update first.'; return; }
  try{
    const patch=JSON.parse(txt);
    applyPatch(patch);
    saveData(txt);
    simCache=null; renderAll(); renderData();
  }catch(e){
    $('dataMsg').innerHTML='<b style="color:var(--bad)">Could not read that.</b> '
      +'Paste the whole block Claude gave you, including the outer braces. ('+e.message+')';
  }
};
if($('dataRevert')) $('dataRevert').onclick=()=>{
  if(!confirm('Discard the pasted update and go back to the data built into this file?')) return;
  try{ if(window.storage) window.storage.delete(DKEY); }catch(e){}
  $('dataMsg').innerHTML='Reverted. <b>Reload the page</b> to load the built-in board.';
};
if($('grade')) $('grade').onclick=()=>{
  if(!me){ alert('Tap ME on your slot first.'); return; }
  if(!picks.length){ alert('Log some picks first.'); return; }
  showReport();
};
['simturnFoot','simturnBoard','simturnRec'].forEach(id=>{
  const el=$(id); if(el) el.onclick=simToTurn;
});
$('reset').onclick=()=>{ if(confirm('Clear every pick? Team names and your slot are kept.')){
  picks=[]; save(); renderAll(); } };
$('export').onclick=()=>{
  const lines=picks.map((p,k)=>{const s=slotOnClock(k);
    return (k+1)+'. R'+(Math.floor(k/TEAMS)+1)+'  '+(names[s]||('Team '+s))
      +'  —  '+P[p.i].p+' '+P[p.i].n+(s===me?'   <-- MINE':'');});
  const mine=me?rosterOf(me).map(x=>x.p+' '+x.n):[];
  navigator.clipboard.writeText('SCARBOROUGH — draft log\n\n'+lines.join('\n')
    +'\n\nVANDELAY INDUSTRIES ('+mine.length+')\n'+mine.join('\n')).then(
    ()=>$('status').textContent='Draft log copied',
    ()=>$('status').textContent='Could not copy — check browser permissions');
};

/* ---------- search ---------- */
function matches(){
  const v=$('q').value.trim().toLowerCase(); if(!v) return [];
  const taken=takenSet();
  return P.filter(p=>!taken.has(p.i)&&p.n.toLowerCase().includes(v)).slice(0,8);
}
function search(){
  const m=matches(), box=$('results');
  if(!m.length){ box.classList.remove('show'); box.innerHTML=''; return; }
  cursor=Math.min(cursor,m.length-1);
  box.innerHTML=m.map((p,k)=>rowHTML(p,k===cursor,takenSet())).join('');
  box.classList.add('show');
}
$('q').addEventListener('input',()=>{cursor=0;search();});
$('q').addEventListener('keydown',e=>{
  const m=matches();
  if(e.key==='ArrowDown'){e.preventDefault();cursor=Math.min(cursor+1,m.length-1);search();}
  else if(e.key==='ArrowUp'){e.preventDefault();cursor=Math.max(cursor-1,0);search();}
  else if(e.key==='Enter'&&m[cursor]){e.preventDefault();draft(m[cursor].i);}
  else if(e.key==='Escape'){$('q').value='';search();}
});

function boot(){
  // The 2026 order is known, so seat everyone by default in BOTH builds.
  if(!names.some(Boolean)){ PRESET.forEach((n,k)=>names[k+1]=n); }
  if(!me) me = MY_SLOT;
  if(SANDBOX){
    $('sandbar').style.display='block';
    // Duplicate the most-used control so it is reachable without scrolling
    ['simturnFoot','simturnBoard','grade','tabStudy'].forEach(id=>{
      const el=$(id); if(el) el.style.display='inline-block';
    });
    const w=$('simturnRecWrap'); if(w) w.style.display='flex';
    const bh=$('boardhint'); if(bh) bh.style.display='none';
    if(!names.some(Boolean)){ PRESET.forEach((n,k)=>names[k+1]=n); }
    if(!me) me = Math.max(1, PRESET.indexOf('Vandelay Industries')+1);
  }
  renderSetup(); renderFilters(); renderAll(); renderData(); showPane(pane);
  if(me) $('setup').open = false;
}

/* Draw the board immediately, THEN try to restore saved state. Awaiting storage
   before the first render meant that in any environment where the storage
   promise never settled, the page loaded completely empty. */
try { boot(); } catch(e){ console.error('boot failed', e); }
Promise.all([load(), loadData()])
  .then(()=>{ try{ boot(); }catch(e){} })
  .catch(()=>{});
</script>
</body>
</html>
"""

import json as _json
PRESET = _json.dumps(DRAFT_ORDER_2026, separators=(",", ":"))
MY_SLOT = MY_SLOT_2026

def emit(path, sandbox):
    html = (HTML.replace("__CFG__", CFG)
                .replace("__SANDBOX__", "true" if sandbox else "false")
                .replace("__PRESET__", PRESET)
                .replace("__MYSLOT__", str(MY_SLOT))
                .replace("__STAMP__", STAMP))
    if sandbox:
        html = html.replace("<title>The Vandelay Industry War Room</title>",
                            f"<title>War Room Sandbox {STAMP}</title>")
        html = html.replace("The Vandelay Industry <em>War Room</em>",
                            "War Room <em>Sandbox</em>")
        html = html.replace(
            "Scarborough &middot; Season XXV &middot; Non-PPR &middot; No flex &middot; TE premium",
            "Practice mode &middot; simulated room &middot; separate from your live draft")
    else:
        html = html.replace("<title>The Vandelay Industry War Room</title>",
                            f"<title>Vandelay War Room {STAMP}</title>")
    open(path, "w").write(html)
    return len(html)

a = emit(out("war_room", "html"), False)
b = emit(out("war_room_sandbox", "html"), True)
print("players:", len(players), "| known teams:", len(KNOWN))
print(f"war room {STAMP}: {a/1024:.0f} KB | sandbox: {b/1024:.0f} KB")
print("preset slots:", SLOTS_BY_YEAR[2025])
