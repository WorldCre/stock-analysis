# -*- coding: utf-8 -*-
"""
stock-analysis v3 — HTML 仪表盘生成(从树状目录读取)
====================================================
用法: python build_dashboards.py --stock-dir analyses/海尔智家-sh600690 [--output-dir <path>]
读取 data.json + 各 .md 文件, 生成 history-zh.html + outlook-zh.html
"""
import json, os, sys, argparse, datetime as _dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import get_repo_root
import markdown_parser as mp

ap = argparse.ArgumentParser()
ap.add_argument("--stock-dir", required=True)
ap.add_argument("--output-dir", help="HTML 输出目录(默认 <stock-dir>/html/)")
args = ap.parse_args()

STOCK_DIR = os.path.abspath(args.stock_dir)
OUT_DIR = args.output_dir or os.path.join(STOCK_DIR, "html")
os.makedirs(OUT_DIR, exist_ok=True)

# ============ 读取数据 ============
data = json.load(open(os.path.join(STOCK_DIR, "data.json"), encoding="utf-8"))
stats = data['stats']; meta = data['meta']
monthly = data['monthly']; annual = data.get('annual', [])
compare_series = data.get('compare_series', []); volume = data.get('volume', [])

# 读取树状分析 .md
ana = mp.load_analysis_dir(STOCK_DIR)
key_events = ana['events']; phases = ana['phases']; drawdowns = ana['drawdowns']
moat = ana['moat']; three_good = ana['three_good']; three_good_verdict = ana['three_good_verdict']
chain = ana['chain']; scenarios = ana['scenarios']
valuation_floor = ana['valuation_floor']; valuation_evolution = ana['valuation_evolution']
catalysts = ana['catalysts']; watchpoints = ana['watchpoints']; strategy = ana['strategy_framework']

NAME = meta['name']; CODE = meta['code']; MARKET = meta['market']
CUTOFF = meta['cutoff']; BENCH = meta.get('benchmark', '基准指数')
LATEST = stats['latest']; ATH = stats['ath']; DD_ATH = stats['dd_from_ath']
YTD = annual[-1]['change'] if annual else "N/A"

# ============ JS 数据 ============
series_js = json.dumps([[m['m'], m['p']] for m in monthly], ensure_ascii=False)
ke_js = json.dumps(key_events, ensure_ascii=False)
phases_js = json.dumps(phases, ensure_ascii=False)
annual_js = json.dumps(annual, ensure_ascii=False)
dd_js = json.dumps(drawdowns, ensure_ascii=False)
val_js = json.dumps(valuation_evolution, ensure_ascii=False)
compare_js = json.dumps(compare_series, ensure_ascii=False)
volume_js = json.dumps(volume, ensure_ascii=False)
moat_js = json.dumps(moat, ensure_ascii=False)
tg_js = json.dumps(three_good, ensure_ascii=False)
tg_verdict_js = json.dumps(three_good_verdict, ensure_ascii=False)
chain_js = json.dumps(chain, ensure_ascii=False)

# 情景
bull_path = scenarios.get('bull', [LATEST*1.05, LATEST*1.10, LATEST*1.15, LATEST*1.20, LATEST*1.25, LATEST*1.30])
base_path = scenarios.get('base', [LATEST*1.02, LATEST*1.04, LATEST*1.06, LATEST*1.08, LATEST*1.10, LATEST*1.14])
bear_path = scenarios.get('bear', [LATEST*0.96, LATEST*0.92, LATEST*0.88, LATEST*0.84, LATEST*0.80, LATEST*0.76])
bull_t=round(bull_path[-1],2); base_t=round(base_path[-1],2); bear_t=round(bear_path[-1],2)
bull_chg=round((bull_t/LATEST-1)*100,1); base_chg=round((base_t/LATEST-1)*100,1); bear_chg=round((bear_t/LATEST-1)*100,1)

targets = []
for t in (catalysts.get('analyst_targets') or []):
    targets.append(t)
avg_target = round(sum(t['target'] for t in targets)/len(targets), 1) if targets else round(LATEST*1.15, 1)
avg_chg = round((avg_target/LATEST-1)*100, 1)

q_labels = []
d = _dt.datetime.strptime(CUTOFF, "%Y-%m-%d")
for i in range(6):
    d = d + _dt.timedelta(days=95)
    q_labels.append(f"{d.year}Q{(d.month-1)//3+1}")

CSS = r'''*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0d1117;--card:#161b22;--card2:#1c2330;--border:#30363d;--blue:#58a6ff;--green:#3fb950;--red:#f85149;--yellow:#d29922;--text:#e6edf3;--text2:#8b949e}
body{background:var(--bg);color:var(--text);font-family:'Segoe UI',-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;padding:20px;line-height:1.6}
h1{font-size:24px;margin-bottom:4px}h2{font-size:18px;margin:24px 0 12px;padding-bottom:8px;border-bottom:1px solid var(--border)}h3{font-size:15px;margin:16px 0 8px;color:var(--blue)}
.sub{color:var(--text2);font-size:13px;margin-bottom:16px}
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:20px}
.kpi{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px}
.kpi .label{font-size:12px;color:var(--text2)}.kpi .val{font-size:20px;font-weight:600;margin-top:4px}
.kpi .val.up{color:var(--green)}.kpi .val.down{color:var(--red)}.kpi .val.blue{color:var(--blue)}
.card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:16px;margin-bottom:16px}
.chart-wrap{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:16px;margin-bottom:16px;height:500px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:8px 10px;text-align:left;border-bottom:1px solid var(--border)}th{color:var(--text2);font-weight:600;font-size:12px}
.pos{color:var(--green)}.neg{color:var(--red)}
.phase-card{background:var(--card2);border-left:3px solid var(--blue);border-radius:4px;padding:12px 14px;margin-bottom:10px;cursor:pointer;transition:background .15s}
.phase-card:hover{background:#222a38}.phase-head{display:flex;justify-content:space-between;align-items:center}.phase-title{font-weight:600;font-size:14px}.phase-change{font-size:13px;font-weight:600}.phase-body{font-size:12.5px;color:var(--text2);margin-top:6px;display:none}.phase-card.open .phase-body{display:block}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;background:#21262d;color:var(--text2)}
.drawdown-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
.dd-card{background:var(--card2);border-radius:6px;padding:12px;border-top:2px solid var(--red)}.dd-card .depth{font-size:20px;font-weight:700;color:var(--red)}
.dd-type{display:inline-block;padding:1px 7px;border-radius:3px;font-size:10px;margin-left:6px}
.dd-type.sys{background:#1f3a5f;color:var(--blue)}.dd-type.idio{background:#3f1f1f;color:var(--red)}.dd-type.mixed{background:#3f2f1f;color:var(--yellow)}
.panel{position:fixed;top:0;right:-440px;width:420px;height:100vh;background:var(--card);border-left:1px solid var(--border);box-shadow:-4px 0 20px rgba(0,0,0,.5);padding:24px;transition:right .3s;z-index:100;overflow-y:auto}.panel.open{right:0}
.panel-close{position:absolute;top:16px;right:16px;cursor:pointer;color:var(--text2);font-size:20px;background:none;border:none}
.panel-nav{display:flex;justify-content:space-between;margin-top:20px}.panel-nav button{background:var(--card2);color:var(--text);border:1px solid var(--border);border-radius:4px;padding:6px 14px;cursor:pointer;font-size:13px}.panel-nav button:hover{background:#222a38}
.panel-date{color:var(--blue);font-size:13px}.panel-price{font-size:28px;font-weight:700;margin:6px 0}.panel-title{font-size:18px;font-weight:600;margin-bottom:10px}.panel-bg{font-size:13.5px;color:var(--text2);line-height:1.7}
.hint{font-size:12px;color:var(--text2);text-align:center;margin-top:8px}
.disclaimer{font-size:11px;color:var(--text2);text-align:center;margin-top:24px;padding:12px;border:1px dashed var(--border);border-radius:6px}
.real-badge{display:inline-block;background:#1f3a1f;color:var(--green);padding:2px 8px;border-radius:3px;font-size:11px;margin-left:8px}'''

HIST = r'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>@@NAME@@ 历史走势仪表盘</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>@@CSS@@</style></head><body>
<h1>📊 @@NAME@@ 历史走势仪表盘 <span class="real-badge">✓ 真实数据</span></h1>
<div class="sub">@@CODE@@ (@@MARKET@@) | 截止 @@CUTOFF@@ | 前复权真实历史 | 基准 @@BENCH@@ | 月线 @@MCOUNT@@ 点 | 全量拉取 @@FFDATE@@</div>
<div class="kpi-grid">
<div class="kpi"><div class="label">历史最高 ATH</div><div class="val up">¥@@ATH@@</div><div class="hint">@@ATH_DATE@@</div></div>
<div class="kpi"><div class="label">当前价</div><div class="val blue">¥@@LATEST@@</div><div class="hint">@@LATEST_DATE@@</div></div>
<div class="kpi"><div class="label">较ATH回撤</div><div class="val down">@@DD_ATH@@%</div><div class="hint">距高点</div></div>
<div class="kpi"><div class="label">YTD</div><div class="val @@YTDCLS@@">@@YTD@@</div><div class="hint">年内</div></div>
<div class="kpi"><div class="label">52周高/低</div><div class="val blue">¥@@H52@@/@@L52@@</div><div class="hint">近一年</div></div>
<div class="kpi"><div class="label">数据来源</div><div class="val blue" style="font-size:13px">akshare+指数</div><div class="hint">真实历史</div></div>
</div>
<h2>📈 月度走势 + 关键节点 (点击标记查看详情, 滚轮缩放)</h2>
<div class="chart-wrap" id="priceChart"></div>
<div class="hint">💡 点击黄色节点查看详情;滚轮缩放;面板 ← → 导航,Esc 关闭</div>
<h2>⚖️ 个股 vs @@BENCH@@ 归一化对比 (起点=100)</h2>
<div class="chart-wrap" id="compareChart" style="height:420px"></div>
<div class="card" style="font-size:13px;color:var(--text2);margin-top:-8px">📌 个股线在指数线上方=跑赢大盘(选股有效),下方=跑输(个股问题)。区分"系统性下跌"与"个股独立下跌"。</div>
<h2>📊 成交量 (近24月月均)</h2>
<div class="chart-wrap" id="volChart" style="height:280px"></div>
<h2>🗓️ 阶段时间线 (点击展开)</h2><div id="phases"></div>
<h2>📅 年度收益 (真实收盘价)</h2>
<div class="card"><table><thead><tr><th>年份</th><th>开盘</th><th>收盘</th><th>涨跌幅</th><th>关键事件</th></tr></thead><tbody id="annualBody"></tbody></table></div>
<h2>📉 重大回撤 + Alpha 分解</h2><div class="drawdown-grid" id="drawdowns"></div>
<h2>🏷️ 估值演变</h2><div class="card"><table><thead><tr><th>时期</th><th>估值逻辑</th><th>PE</th><th>说明</th></tr></thead><tbody id="valuationBody"></tbody></table></div>
<h2>🏰 护城河评估 (巴菲特六维)</h2><div class="card" id="moatBody"></div>
<h2>⭐ 三好框架</h2><div class="card" id="threeGoodBody"></div>
<h2>🔗 产业链与竞争格局</h2><div class="card" id="chainBody"></div>
<div class="disclaimer">⚠️ 价格为真实数据(akshare/yfinance),指数为真实历史,事件/机构观点为公开信息整理。仅供研究参考,不构成投资建议。<br>© @@CUTOFF@@ @@NAME@@ 深度分析</div>
<div class="panel" id="panel"><button class="panel-close" onclick="closePanel()">✕</button>
<div class="panel-date" id="pDate"></div><div class="panel-price" id="pPrice"></div><div class="panel-title" id="pTitle"></div><div class="panel-bg" id="pBg"></div>
<div class="panel-nav"><button onclick="navPanel(-1)">← 上一个</button><button onclick="navPanel(1)">下一个 →</button></div></div>
<script>
const PRICE_SERIES=@@SERIES@@,KEY_EVENTS=@@KE@@,PHASES=@@PHASES@@,ANNUAL=@@ANNUAL@@,DRAWDOWNS=@@DD@@,VALUATION=@@VAL@@,COMPARE=@@COMPARE@@,VOLUME=@@VOLUME@@,MOAT=@@MOAT@@,THREEGOOD=@@TG@@,TG_VERDICT=@@TGV@@,CHAIN=@@CHAIN@@;
const phasesEl=document.getElementById('phases');
PHASES.forEach(ph=>{const c=document.createElement('div');c.className='phase-card';const cl=(ph.change||'').startsWith('+')?'pos':'neg';c.innerHTML=`<div class="phase-head"><div class="phase-title">阶段${ph.id}: ${ph.name} <span class="badge">${ph.start} ~ ${ph.end}</span></div><div class="phase-change ${cl}">${ph.change||''}</div></div><div class="phase-body">¥${ph.startPrice} → ¥${ph.endPrice} | ${ph.driver||''}</div>`;c.onclick=()=>c.classList.toggle('open');phasesEl.appendChild(c);});
const aB=document.getElementById('annualBody');ANNUAL.forEach(a=>{const cl=(a.change||'').startsWith('+')?'pos':'neg';aB.innerHTML+=`<tr><td>${a.year}</td><td>¥${a.open}</td><td>¥${a.close}</td><td class="${cl}">${a.change||''}</td><td>${a.event||''}</td></tr>`;});
const dE=document.getElementById('drawdowns');
DRAWDOWNS.forEach(d=>{let tc='mixed',tt=d.type||'';if(tt.includes('系统性'))tc='sys';else if(tt.includes('个股'))tc='idio';const is=d.index_ret!==null&&d.index_ret!==undefined?`指数 ${d.index_ret}%`:'指数 N/A';const as=d.alpha!==null&&d.alpha!==undefined?`Alpha ${d.alpha}%`:'';dE.innerHTML+=`<div class="dd-card"><div class="depth">${d.depth}<span class="dd-type ${tc}">${tt}</span></div><div style="font-size:13px;margin:6px 0;color:var(--text2)">${d.cause||''}</div><div style="font-size:12px;color:var(--text2)">${d.peak} ¥${d.peakPrice} → ${d.trough} ¥${d.troughPrice}</div><div style="font-size:12px;margin-top:4px">个股 <b style="color:var(--red)">${d.stock_ret}%</b> | ${is} | <b style="color:${d.alpha<0?'var(--red)':'var(--green)'}">${as}</b></div></div>`;});
const vB=document.getElementById('valuationBody');VALUATION.forEach(v=>{vB.innerHTML+=`<tr><td>${v.p}</td><td>${v.l}</td><td style="color:var(--blue)">${v.pe}</td><td style="color:var(--text2)">${v.n}</td></tr>`;});
// 护城河
const moatB=document.getElementById('moatBody');
if(MOAT&&MOAT.length>0){const sc={强:'var(--green)',中:'var(--yellow)',弱:'var(--red)',无:'var(--text2)'};const tc={'加强':'var(--green)','稳定':'var(--text2)','削弱':'var(--red)'};let h='';MOAT.forEach(m=>{if(m.dim==='__summary__')return;const s=sc[m.strength]||'var(--text2)';const t=tc[m.trend]||'var(--text2)';h+=`<div style="background:var(--card2);border-radius:6px;padding:12px;margin-bottom:10px;border-left:3px solid ${s}"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px"><div style="font-weight:600;font-size:14px">${m.dim}</div><div><span style="background:${s};color:#0d1117;padding:2px 8px;border-radius:3px;font-size:12px;font-weight:600">${m.strength||'-'}</span>${m.trend?` <span style="color:${t};font-size:12px;margin-left:6px">趋势:${m.trend}</span>`:''}</div></div><div style="font-size:13px;color:var(--text2);margin-bottom:4px">📊 ${m.evidence||''}</div>${m.compare?`<div style="font-size:12px;color:var(--text2);margin-bottom:4px">⚔️ <b>同业对比:</b>${m.compare}</div>`:''}${m.valuation?`<div style="font-size:12px;color:var(--blue)">💡 <b>估值含义:</b>${m.valuation}</div>`:''}</div>`;});const sum=MOAT.find(m=>m.dim==='__summary__');if(sum&&sum.evidence)h+=`<div style="margin-top:8px;padding:10px;background:var(--card2);border-radius:4px;font-size:13px;border-left:3px solid var(--blue)">📌 <b>护城河综合判断:</b> ${sum.evidence}</div>`;moatB.innerHTML=h;}else{moatB.innerHTML='<div style="color:var(--text2)">无护城河数据</div>';}
// 三好
const tgB=document.getElementById('threeGoodBody');
if(THREEGOOD&&Object.keys(THREEGOOD).length>0){const rc={'好':'var(--green)','中':'var(--yellow)','差':'var(--red)'};const blk=(k,t,c)=>{const it=THREEGOOD[k];if(!it)return '';let s=`<div style="margin-bottom:14px;background:var(--card2);border-radius:6px;padding:12px;border-left:3px solid ${c}"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px"><div style="color:${c};font-weight:600;font-size:14px">${t}</div>`;if(it.rating)s+=`<span style="background:${rc[it.rating]||'var(--text2)'};color:#0d1117;padding:2px 10px;border-radius:3px;font-size:12px;font-weight:600">${it.rating}</span>`;s+=`</div>`;if(it.analysis)s+=`<div style="font-size:13px;color:var(--text2);margin-bottom:8px">${it.analysis}</div>`;if(it.data&&it.data.length>0){s+=`<table style="font-size:12px;margin-bottom:6px"><tbody>`;it.data.forEach(d=>{s+=`<tr><td style="color:var(--text2);padding:2px 8px 2px 0">${d[0]}</td><td style="color:var(--text);font-weight:600">${d[1]}</td></tr>`;});s+=`</tbody></table>`;}if(it.valuation)s+=`<div style="font-size:12px;color:${c}">💡 <b>估值含义:</b>${it.valuation}</div>`;s+=`</div>`;return s;};let h=blk('industry','🏭 好行业 (波特五力)','var(--blue)')+blk('company','🏢 好公司 (DuPont)','var(--green)')+blk('management','👤 好管理 (资本配置)','var(--yellow)');if(TG_VERDICT)h+=`<div style="margin-top:8px;padding:10px;background:var(--card2);border-radius:4px;font-size:13px;border-left:3px solid var(--blue)">⚖️ <b>综合判断:</b> ${TG_VERDICT}</div>`;tgB.innerHTML=h;}else{tgB.innerHTML='<div style="color:var(--text2)">无三好框架数据</div>';}
// 产业链
const chB=document.getElementById('chainBody');
if(CHAIN&&Object.keys(CHAIN).length>0){const blk=(k,t,c)=>{const it=CHAIN[k];if(!it)return '';const ct=typeof it==='string'?it:it.content;let s=`<div style="margin-bottom:12px;background:var(--card2);border-radius:6px;padding:12px;border-left:3px solid ${c}"><div style="color:${c};font-weight:600;margin-bottom:6px;font-size:14px">${t}</div>`;if(ct)s+=`<div style="font-size:13px;color:var(--text2);margin-bottom:6px">${ct}</div>`;if(typeof it==='object'){if(it.bargaining)s+=`<div style="font-size:12px;margin-bottom:3px">🤝 <b>议价权:</b><span style="color:var(--text2)">${it.bargaining}</span></div>`;if(it.risk)s+=`<div style="font-size:12px;margin-bottom:3px">⚠️ <b>风险点:</b><span style="color:var(--text2)">${it.risk}</span></div>`;if(it.valuation)s+=`<div style="font-size:12px;color:${c}">💡 <b>估值含义:</b>${it.valuation}</div>`;}s+=`</div>`;return s;};chB.innerHTML=blk('upstream','⬆️ 上游','var(--yellow)')+blk('midstream','🔹 中游','var(--blue)')+blk('downstream','⬇️ 下游','var(--green)')+blk('competition','⚔️ 竞争格局','var(--red)')||'<div style="color:var(--text2)">无产业链数据</div>';}else{chB.innerHTML='<div style="color:var(--text2)">无产业链数据</div>';}
// 价格图
const priceChart=echarts.init(document.getElementById('priceChart'),'dark');
priceChart.setOption({backgroundColor:'transparent',tooltip:{trigger:'axis',formatter:p=>{let s='';p.forEach(d=>{if(d.seriesType==='line')s+=`${d.axisValue}<br/>¥${d.data}`;});return s;}},grid:{left:60,right:30,top:30,bottom:60},xAxis:{type:'category',data:PRICE_SERIES.map(p=>p[0]),axisLabel:{color:'#8b949e',interval:Math.floor(PRICE_SERIES.length/12)}},yAxis:{type:'value',axisLabel:{color:'#8b949e',formatter:v=>'¥'+v},splitLine:{lineStyle:{color:'#21262d'}}},dataZoom:[{type:'inside'},{type:'slider',height:20,bottom:10}],series:[{type:'line',data:PRICE_SERIES.map(p=>p[1]),smooth:true,symbol:'none',lineStyle:{color:'#58a6ff',width:2},areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(88,166,255,0.35)'},{offset:1,color:'rgba(88,166,255,0.02)'}])}},{type:'scatter',data:KEY_EVENTS.map((e,i)=>({value:[e.date,e.price],eventIdx:i})),symbolSize:9,itemStyle:{color:'#d29922',borderColor:'#fff',borderWidth:1},emphasis:{symbolSize:14,itemStyle:{color:'#ffd700'}},tooltip:{formatter:p=>{const e=KEY_EVENTS[p.data.eventIdx];return `<b>${e.title}</b><br/>${e.date}<br/>¥${e.price}<br/><span style="color:#8b949e">点击查看详情</span>`;}},z:10}]});
priceChart.on('click',p=>{if(p.seriesType==='scatter'&&p.data&&p.data.eventIdx!==undefined)openPanel(p.data.eventIdx);});
// 对比图
if(COMPARE.length>0){const cmp=echarts.init(document.getElementById('compareChart'),'dark');cmp.setOption({backgroundColor:'transparent',tooltip:{trigger:'axis'},legend:{data:['@@NAME@@','@@BENCH@@(=100)'],textStyle:{color:'#e6edf3'},top:0},grid:{left:50,right:30,top:30,bottom:40},xAxis:{type:'category',data:COMPARE.map(c=>c.m),axisLabel:{color:'#8b949e',interval:Math.floor(COMPARE.length/8)}},yAxis:{type:'value',axisLabel:{color:'#8b949e'},splitLine:{lineStyle:{color:'#21262d'}}},series:[{name:'@@NAME@@',type:'line',data:COMPARE.map(c=>c.stock),smooth:true,symbol:'none',lineStyle:{color:'#58a6ff',width:2}},{name:'@@BENCH@@(=100)',type:'line',data:COMPARE.map(c=>c.index),smooth:true,symbol:'none',lineStyle:{color:'#8b949e',width:1.5,type:'dashed'}}]});}else{document.getElementById('compareChart').innerHTML='<div style="text-align:center;color:#8b949e;padding-top:40px">无指数对比数据</div>';}
// 成交量
if(VOLUME.length>0){const vc=echarts.init(document.getElementById('volChart'),'dark');vc.setOption({backgroundColor:'transparent',tooltip:{trigger:'axis'},grid:{left:60,right:30,top:20,bottom:30},xAxis:{type:'category',data:VOLUME.map(v=>v.m),axisLabel:{color:'#8b949e'}},yAxis:{type:'value',axisLabel:{color:'#8b949e',formatter:v=>v>1e8?(v/1e8).toFixed(1)+'亿':v>1e4?(v/1e4).toFixed(0)+'万':v},splitLine:{lineStyle:{color:'#21262d'}}},series:[{type:'bar',data:VOLUME.map(v=>v.v),itemStyle:{color:'#58a6ff',opacity:0.6}}]});}
let ci=0;const pn=document.getElementById('panel');
function openPanel(i){ci=i;const e=KEY_EVENTS[i];document.getElementById('pDate').textContent=e.date;document.getElementById('pPrice').textContent='¥'+e.price;document.getElementById('pTitle').textContent=e.title;document.getElementById('pBg').textContent=e.bg;pn.classList.add('open');}
function closePanel(){pn.classList.remove('open');}
function navPanel(d){openPanel((ci+d+KEY_EVENTS.length)%KEY_EVENTS.length);}
document.addEventListener('keydown',e=>{if(!pn.classList.contains('open'))return;if(e.key==='Escape')closePanel();if(e.key==='ArrowLeft')navPanel(-1);if(e.key==='ArrowRight')navPanel(1);});
window.addEventListener('resize',()=>{priceChart.resize();});
</script></body></html>'''

ytd_cls = "up" if (YTD and YTD.startswith('+')) else "down"
hd = {"CSS":CSS,"NAME":NAME,"CODE":CODE,"MARKET":MARKET,"CUTOFF":CUTOFF,"BENCH":BENCH,
    "ATH":ATH,"ATH_DATE":stats['ath_date'],"LATEST":LATEST,"LATEST_DATE":stats['latest_date'],
    "DD_ATH":DD_ATH,"YTD":YTD,"YTDCLS":ytd_cls,"H52":stats['high_52w'],"L52":stats['low_52w'],
    "MCOUNT":len(monthly),"FFDATE":meta.get('full_fetch_date',''),
    "SERIES":series_js,"KE":ke_js,"PHASES":phases_js,"ANNUAL":annual_js,"DD":dd_js,"VAL":val_js,
    "COMPARE":compare_js,"VOLUME":volume_js,"MOAT":moat_js,"TG":tg_js,"TGV":tg_verdict_js,"CHAIN":chain_js}
hh = HIST
for k,v in hd.items(): hh = hh.replace(f"@@{k}@@", str(v))
with open(os.path.join(OUT_DIR,"history-zh.html"),"w",encoding="utf-8") as f: f.write(hh)
print(f"✓ history-zh.html ({len(hh)} 字节) → {OUT_DIR}")

# ============ 展望仪表盘 ============
OUT = r'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>@@NAME@@ 未来展望仪表盘</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>@@CSS@@
.hero{background:linear-gradient(135deg,#1a2332,#161b22);border:1px solid var(--border);border-radius:10px;padding:24px;margin-bottom:20px}
.hero h1{margin-bottom:8px}.thesis{font-size:15px;margin:10px 0}
.hero-kpi{display:flex;gap:24px;flex-wrap:wrap;margin-top:14px}.hero-kpi div{font-size:13px}.hero-kpi .v{font-size:20px;font-weight:700;color:var(--blue);display:block}
.scenario-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:8px}
.sc{border-radius:8px;padding:14px;border:1px solid var(--border)}
.sc.bull{background:rgba(63,185,80,.08);border-color:rgba(63,185,80,.3)}.sc.base{background:rgba(88,166,255,.08);border-color:rgba(88,166,255,.3)}.sc.bear{background:rgba(248,81,73,.08);border-color:rgba(248,81,73,.3)}
.sc .name{font-weight:700;font-size:15px}.sc .target{font-size:22px;font-weight:700;margin:6px 0}
.floor-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.floor{background:var(--card2);border-radius:6px;padding:14px;border-top:3px solid var(--yellow)}
.floor .method{font-weight:600;color:var(--yellow);font-size:13px}.floor .range{font-size:18px;font-weight:700;margin:6px 0;color:var(--blue)}
.cat-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.cat-up{border-left:3px solid var(--green)}.cat-down{border-left:3px solid var(--red)}
.cat-item{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--border);font-size:13px}.stars{color:var(--yellow)}
.strat-row{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border)}.strat-range{min-width:110px;font-weight:600;color:var(--blue);font-size:13px}.strat-label{min-width:90px;font-size:12px;padding:2px 8px;border-radius:3px}
</style></head><body>
<div class="hero">
<h1>🔮 @@NAME@@ 未来展望仪表盘 <span class="real-badge">✓ 真实数据</span></h1>
<div class="sub">@@CODE@@ (@@MARKET@@) | 当前 ¥@@LATEST@@ (@@LATEST_DATE@@) | 预测 @@FC_START@@→@@FC_END@@</div>
<div class="thesis">📌 当前¥@@LATEST@@较ATH(¥@@ATH@@,@@ATH_DATE@@)回撤@@DD_ATH@@%。基准看至¥@@BASE_T@@(+@@BASE_CHG@@%),估值底部三重验证支撑。</div>
<div class="hero-kpi">
<div>基准目标<span class="v">¥@@BASE_T@@</span></div>
<div>乐观<span class="v" style="color:var(--green)">¥@@BULL_T@@</span></div>
<div>悲观<span class="v" style="color:var(--red)">¥@@BEAR_T@@</span></div>
<div>机构均值<span class="v">¥@@AVG@@</span></div></div></div>
<h2>🎯 三情景</h2>
<div class="scenario-grid">
<div class="sc bull"><div class="name">🟢 乐观</div><div class="target pos">¥@@BULL_T@@ (+@@BULL_CHG@@%)</div></div>
<div class="sc base"><div class="name">🔵 基准</div><div class="target" style="color:var(--blue)">¥@@BASE_T@@ (+@@BASE_CHG@@%)</div></div>
<div class="sc bear"><div class="name">🔴 悲观</div><div class="target neg">¥@@BEAR_T@@ (@@BEAR_CHG@@%)</div></div>
</div>
<h2>📊 三情景路径</h2><div class="chart-wrap" id="scenarioChart" style="height:400px"></div>
<h2>🛡️ 估值验证</h2><div class="floor-grid" id="floors"></div>
<h2>🏛️ 机构目标价 (均值¥@@AVG@@)</h2><div class="chart-wrap" id="targetChart" style="height:380px"></div>
<h2>⚡ 催化剂矩阵</h2><div class="cat-grid" id="catGrid"></div>
<h2>👁️ 关键观测节点</h2><div class="card"><table><thead><tr><th>时间</th><th>事件</th><th>看涨</th><th>看跌</th></tr></thead><tbody id="wpBody"></tbody></table></div>
<h2>📐 策略框架</h2><div class="card" id="stratBody"></div>
<div class="disclaimer">⚠️ 价格为真实数据,情景与目标价为分析估算,不构成投资建议。<br>© @@CUTOFF@@ @@NAME@@</div>
<script>
const bull=@@BULL@@,base=@@BASE@@,bear=@@BEAR@@,L=@@LATEST@@,labels=['@@FC_Q1@@','@@FC_Q2@@','@@FC_Q3@@','@@FC_Q4@@','@@FC_Q5@@','@@FC_Q6@@'];
const sC=echarts.init(document.getElementById('scenarioChart'),'dark');
sC.setOption({backgroundColor:'transparent',tooltip:{trigger:'axis'},legend:{data:['乐观','基准','悲观','当前价'],textStyle:{color:'#e6edf3'},top:0},grid:{left:50,right:30,top:30,bottom:30},xAxis:{type:'category',data:labels,axisLabel:{color:'#8b949e'}},yAxis:{type:'value',axisLabel:{color:'#8b949e',formatter:v=>'¥'+v},splitLine:{lineStyle:{color:'#21262d'}}},series:[{name:'当前价',type:'line',data:Array(6).fill(L),lineStyle:{color:'#8b949e',type:'dashed',width:1},symbol:'none'},{name:'乐观',type:'line',data:bull,smooth:true,lineStyle:{color:'#3fb950',width:2.5}},{name:'基准',type:'line',data:base,smooth:true,lineStyle:{color:'#58a6ff',width:2.5},areaStyle:{color:'rgba(88,166,255,0.1)'}},{name:'悲观',type:'line',data:bear,smooth:true,lineStyle:{color:'#f85149',width:2.5}}]});
const floors=@@FLOOR@@;const fE=document.getElementById('floors');
floors.forEach(f=>{fE.innerHTML+=`<div class="floor"><div class="method">${f.method}</div><div class="range">${f.range}</div><div style="font-size:11.5px;color:var(--text2)">${f.logic}</div></div>`;});
const targets=@@TARGETS@@;const tC=echarts.init(document.getElementById('targetChart'),'dark');
tC.setOption({backgroundColor:'transparent',tooltip:{trigger:'axis'},grid:{left:50,right:30,top:20,bottom:30},xAxis:{type:'category',data:targets.map(x=>x.inst),axisLabel:{color:'#8b949e',font:{size:10},rotate:30}},yAxis:{type:'value',axisLabel:{color:'#8b949e',formatter:v=>'¥'+v},splitLine:{lineStyle:{color:'#21262d'}}},series:[{type:'bar',data:targets.map(x=>({value:x.target,itemStyle:{color:x.target>=L?'#3fb950':'#f85149'}})),barWidth:'60%',markLine:{data:[{yAxis:L}],lineStyle:{color:'#d29922',type:'dashed'},label:{formatter:'当前¥'+L,color:'#d29922'}}}]});
const cats=@@CATS@@;const cG=document.getElementById('catGrid');
cG.innerHTML=`<div class="card cat-up"><h3 style="color:var(--green)">⬆️ 上行</h3>${(cats.upside||[]).map(c=>`<div class="cat-item"><span>${c.event}</span><span class="stars">${'★'.repeat(c.star||3)}</span></div>`).join('')}</div><div class="card cat-down"><h3 style="color:var(--red)">⬇️ 下行</h3>${(cats.downside||[]).map(c=>`<div class="cat-item"><span>${c.event}</span><span class="stars">${'★'.repeat(c.star||3)}</span></div>`).join('')}</div>`;
const wp=@@WP@@;const wB=document.getElementById('wpBody');(wp||[]).forEach(w=>{wB.innerHTML+=`<tr><td>${w.time}</td><td>${w.event}</td><td class="pos">${w.bull||''}</td><td class="neg">${w.bear||''}</td></tr>`;});
const strat=@@STRAT@@;const sB=document.getElementById('stratBody');(strat||[]).forEach(s=>{sB.innerHTML+=`<div class="strat-row"><div class="strat-range">${s.range}</div><div class="strat-label" style="background:#21262d;color:var(--text2)">${s.label}</div><div style="font-size:13px;color:var(--text2)">${s.meaning}</div></div>`;});
window.addEventListener('resize',()=>{sC.resize();tC.resize();});
</script></body></html>'''

od = {"CSS":CSS,"NAME":NAME,"CODE":CODE,"MARKET":MARKET,"CUTOFF":CUTOFF,"LATEST":LATEST,
    "LATEST_DATE":stats['latest_date'],"ATH":ATH,"ATH_DATE":stats['ath_date'],"DD_ATH":DD_ATH,
    "BASE_T":base_t,"BASE_CHG":base_chg,"BULL_T":bull_t,"BULL_CHG":bull_chg,
    "BEAR_T":bear_t,"BEAR_CHG":bear_chg,"AVG":avg_target,
    "FC_START":q_labels[0],"FC_END":q_labels[-1],
    "FC_Q1":q_labels[0],"FC_Q2":q_labels[1],"FC_Q3":q_labels[2],
    "FC_Q4":q_labels[3],"FC_Q5":q_labels[4],"FC_Q6":q_labels[5],
    "BULL":json.dumps([round(p,2) for p in bull_path]),
    "BASE":json.dumps([round(p,2) for p in base_path]),
    "BEAR":json.dumps([round(p,2) for p in bear_path]),
    "FLOOR":json.dumps(valuation_floor,ensure_ascii=False),
    "TARGETS":json.dumps([{"inst":t.get("inst",""),"target":t.get("target",0)} for t in targets],ensure_ascii=False),
    "CATS":json.dumps(catalysts,ensure_ascii=False),
    "WP":json.dumps(watchpoints,ensure_ascii=False),
    "STRAT":json.dumps(strategy,ensure_ascii=False)}
oh = OUT
for k,v in od.items(): oh = oh.replace(f"@@{k}@@", str(v))
with open(os.path.join(OUT_DIR,"outlook-zh.html"),"w",encoding="utf-8") as f: f.write(oh)
print(f"✓ outlook-zh.html ({len(oh)} 字节) → {OUT_DIR}")
print(f"\n✅ 仪表盘生成完成")
