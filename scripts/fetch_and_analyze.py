# -*- coding: utf-8 -*-
"""
stock-analysis v3 — 数据抓取 + 分析(支持增量)
================================================
用法:
  首次:    python fetch_and_analyze.py <代码> <公司名> <截止日>
  增量:    python fetch_and_analyze.py <代码> <公司名> <截止日> --incremental
  强制全量: python fetch_and_analyze.py <代码> <公司名> <截止日> --force

代码前缀: sh600690/sz000001(A股) | hk06690(港股) | usAAPL(美股)
输出: analyses/<公司>-<代码>/ 下的 data.json + daily_full.csv
"""
import sys, os, json, re, argparse
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import get_stock_dir, safe_name
import markdown_parser as mp

# ============ 参数 ============
ap = argparse.ArgumentParser()
ap.add_argument("code")
ap.add_argument("name")
ap.add_argument("cutoff")
ap.add_argument("--stock-dir", help="股票分析目录(默认 analyses/<name>-<code>/)")
ap.add_argument("--incremental", action="store_true", help="增量拉取(只拉新增数据)")
ap.add_argument("--force", action="store_true", help="强制全量重拉(校正前复权)")
args = ap.parse_args()

RAW_CODE = args.code.strip()
NAME = args.name
CUTOFF = args.cutoff
STOCK_DIR = args.stock_dir or get_stock_dir(RAW_CODE, NAME)
os.makedirs(STOCK_DIR, exist_ok=True)

m_a = re.match(r'^(sh|sz)(\d{6})$', RAW_CODE, re.I)
m_hk = re.match(r'^hk(\d{4,5})$', RAW_CODE, re.I)
m_us = re.match(r'^us([A-Z.]+)$', RAW_CODE, re.I)
if m_a:
    market, prefix, code, symbol_ak = "A股", m_a.group(1).lower(), m_a.group(2), f"{m_a.group(1).lower()}{m_a.group(2)}"
    bench_name, bench_ak = "沪深300", "sh000300"
elif m_hk:
    market, code, symbol_ak = "港股", m_hk.group(1), m_hk.group(1)
    bench_name, bench_ak = "恒生指数", "HSI"
elif m_us:
    market, ticker = "美股", m_us.group(1)
    bench_name = "标普500"
else:
    print(f"无法识别代码: {RAW_CODE}"); sys.exit(1)

CSV_FILE = os.path.join(STOCK_DIR, "daily_full.csv")
DATA_FILE = os.path.join(STOCK_DIR, "data.json")

print("=" * 60)
print(f"{NAME} ({RAW_CODE}) | {market} | 基准:{bench_name} | 截止:{CUTOFF}")
print(f"目录: {STOCK_DIR}")
if args.incremental: print("模式: 增量")
elif args.force: print("模式: 强制全量")
else: print("模式: 全量(首次)")
print("=" * 60)

# ============ 增量检测 ============
existing_df = None
full_fetch_date = CUTOFF
do_full = True

if os.path.exists(DATA_FILE):
    old_data = json.load(open(DATA_FILE, encoding="utf-8"))
    full_fetch_date = old_data.get("meta", {}).get("full_fetch_date", CUTOFF)

# 6个月提醒
if os.path.exists(DATA_FILE) and not args.force:
    from datetime import datetime, timedelta
    try:
        ffdate = datetime.strptime(full_fetch_date, "%Y-%m-%d")
        if datetime.now() - ffdate > timedelta(days=180):
            print(f"\n⚠️  上次全量拉取于 {full_fetch_date},距今超6个月。")
            print("   前复权价格可能因分红送转而偏移,建议加 --force 全量重拉。")
            print("   (继续增量模式,本次仅追加新数据)\n")
    except: pass

if args.incremental and os.path.exists(CSV_FILE) and not args.force:
    existing_df = pd.read_csv(CSV_FILE, parse_dates=['date'])
    last_date = existing_df['date'].max()
    cutoff_dt = pd.to_datetime(CUTOFF)
    if last_date >= cutoff_dt:
        print(f"[RAG] 数据已覆盖截止日(最后:{last_date.date()}),跳过拉取,复用现有数据")
        do_full = False
        df = existing_df.copy()
    else:
        print(f"[RAG] 增量拉取: {last_date.date()} → {CUTOFF}")
        do_full = False
        fetch_start = (last_date + pd.Timedelta(days=1)).strftime("%Y%m%d")
else:
    if args.force:
        print("[强制] 全量重拉(校正前复权)")
        full_fetch_date = CUTOFF

# ============ 拉取函数 ============
def fetch_a(symbol, start=None):
    import akshare as ak
    if start:
        return ak.stock_zh_a_daily(symbol=symbol, start_date=start, end_date=CUTOFF.replace("-",""), adjust="qfq")
    return ak.stock_zh_a_daily(symbol=symbol, adjust="qfq")

def fetch_hk(symbol, start=None):
    import akshare as ak
    if start:
        return ak.stock_hk_daily(symbol=symbol, adjust="qfq")
    return ak.stock_hk_daily(symbol=symbol, adjust="qfq")

def fetch_us(ticker):
    import yfinance as yf
    d = yf.Ticker(ticker).history(period="max", auto_adjust=True)
    return d.reset_index().rename(columns={'Date':'date','Open':'open','High':'high','Low':'low','Close':'close','Volume':'volume'})

def fetch_index():
    """拉取基准指数"""
    try:
        import akshare as ak
        if market == "A股":
            b = ak.stock_zh_index_daily(symbol=bench_ak)
        elif market == "港股":
            b = ak.stock_hk_index_daily_sina(symbol=bench_ak)
        else:
            return None
        b['date'] = pd.to_datetime(b['date'])
        b['close'] = b['close'].astype(float)
        return b[['date','close']].sort_values('date').reset_index(drop=True)
    except Exception as e:
        print(f"  指数拉取失败: {e}")
        return None

# ============ 执行拉取 ============
if not do_full and existing_df is not None and 'df' in dir():
    pass  # 已复用
else:
    new_df = None
    try:
        if market == "A股":
            print(f"[A股] akshare 拉取 {symbol_ak}...")
            new_df = fetch_a(symbol_ak, fetch_start if not do_full else None)
        elif market == "港股":
            print(f"[港股] akshare 拉取 {symbol_ak}...")
            new_df = fetch_hk(symbol_ak)
            hk_latest = float(new_df['close'].iloc[-1])
        elif market == "美股":
            print(f"[美股] yfinance 拉取 {ticker}...")
            new_df = fetch_us(ticker)
    except Exception as e:
        print(f"  拉取失败: {e}")
        if existing_df is not None:
            print("  回退到现有数据")
            df = existing_df.copy()
            new_df = None
        else:
            sys.exit(1)

    if new_df is not None and len(new_df) > 0:
        new_df['date'] = pd.to_datetime(new_df['date'])
        for c in ['open','high','low','close']:
            if c in new_df.columns: new_df[c] = new_df[c].astype(float)
        if 'volume' not in new_df.columns: new_df['volume'] = 0.0
        new_df['volume'] = new_df['volume'].astype(float)
        if existing_df is not None and not do_full:
            df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['date'], keep='last').sort_values('date').reset_index(drop=True)
            added = len(df) - len(existing_df)
            print(f"  合并完成: 新增 {added} 条, 总计 {len(df)} 条")
        else:
            df = new_df.sort_values('date').reset_index(drop=True)
            print(f"  成功: {len(df)} 条, {df['date'].iloc[0].strftime('%Y-%m-%d')} ~ {df['date'].iloc[-1].strftime('%Y-%m-%d')}")

df = df.sort_values('date').reset_index(drop=True)
df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')

# ============ 基准指数 ============
print(f"\n[基准指数] {bench_name}...")
bench_df = fetch_index()
if bench_df is not None:
    print(f"  成功: {len(bench_df)} 条")
elif market == "美股":
    try:
        import yfinance as yf
        bench_df = yf.Ticker("^GSPC").history(period="max", auto_adjust=True).reset_index()
        bench_df = bench_df.rename(columns={'Date':'date','Close':'close'})[['date','close']]
        bench_df['date'] = pd.to_datetime(bench_df['date'])
        print(f"  yfinance: {len(bench_df)} 条")
    except Exception as e:
        print(f"  失败: {e}")

# ============ 月线 ============
df['month'] = df['date'].dt.to_period('M')
monthly = df.groupby('month').last().reset_index()
monthly['month'] = monthly['month'].astype(str)
monthly_json = [{"m": r['month'], "p": round(float(r['close']),2)} for _,r in monthly.iterrows()]

# ============ 统计(日线) ============
prices = df['close']
ath = float(prices.max()); ath_date = df.loc[prices.idxmax(),'date'].strftime('%Y-%m-%d')
atl = float(prices.min()); atl_date = df.loc[prices.idxmin(),'date'].strftime('%Y-%m-%d')
latest_row = df.iloc[-1]
latest = float(latest_row['close']); latest_date = latest_row['date'].strftime('%Y-%m-%d')
ly = df.tail(252)
high_52w = float(ly['high'].max()); low_52w = float(ly['low'].min())
dd_ath = round((latest/ath-1)*100, 1)

print(f"\n=== 真实统计 ===")
print(f"  ATH: {round(ath,2)}  {ath_date}")
print(f"  最新: {round(latest,2)}  {latest_date}")
print(f"  较ATH: {dd_ath}%")

# ============ 年度收益 ============
df['year'] = df['date'].dt.year
yr = df.groupby('year').agg(open=('open','first'), close=('close','last'))
yr['chg'] = ((yr['close']/yr['close'].shift(1)-1)*100).round(1)

# 保留旧的 annual.event(混合字段)
old_events = {}
if os.path.exists(DATA_FILE):
    old_data = json.load(open(DATA_FILE, encoding="utf-8"))
    for a in old_data.get("annual", []):
        old_events[a.get("year")] = a.get("event", "")

annual = []
for y in yr.index:
    r = yr.loc[y]
    annual.append({
        "year": int(y), "open": round(float(r['open']),2), "close": round(float(r['close']),2),
        "change": f"{r['chg']:+.1f}%" if pd.notna(r['chg']) else "N/A",
        "event": old_events.get(int(y), "")  # 保留旧 event
    })

# ============ 回撤 + Alpha 分解(混合:数据重算,cause保留) ============
running_max = df['close'].cummax()
df['dd'] = df['close']/running_max - 1
dd_raw = []
in_dd=False; pi=0; ti=0; md=0
for i in range(len(df)):
    if df['dd'].iloc[i] > -0.3:
        if in_dd and md < -0.4:
            dd_raw.append((df['date'].iloc[pi],df['close'].iloc[pi],df['date'].iloc[ti],df['close'].iloc[ti],md))
        in_dd=False; md=0
    else:
        if not in_dd:
            in_dd=True; pi=i-1; md=df['dd'].iloc[i]; ti=i
        elif df['dd'].iloc[i]<md:
            md=df['dd'].iloc[i]; ti=i
if in_dd and md<-0.4:
    dd_raw.append((df['date'].iloc[pi],df['close'].iloc[pi],df['date'].iloc[ti],df['close'].iloc[ti],md))
dd_raw.sort(key=lambda x: x[4])

# 保留旧 drawdowns 的 cause/type(混合字段)
old_dd_cause = {}
if os.path.exists(DATA_FILE):
    old_data = json.load(open(DATA_FILE, encoding="utf-8"))
    for d in old_data.get("drawdowns", []):
        key = f"{d.get('peak')}-{d.get('trough')}"
        old_dd_cause[key] = {"cause": d.get("cause",""), "type": d.get("type","")}

def index_return(s, e):
    if bench_df is None: return None
    seg = bench_df[(bench_df['date']>=s)&(bench_df['date']<=e)]
    if len(seg)<2: return None
    return round((seg['close'].iloc[-1]/seg['close'].iloc[0]-1)*100, 1)

drawdowns = []
for pk_d,pk_p,tr_d,tr_p,md in dd_raw[:5]:
    sr = round((tr_p/pk_p-1)*100,1)
    ir = index_return(pk_d, tr_d)
    alpha = round(sr-ir,1) if ir is not None else None
    if alpha is not None:
        t = "个股/板块(显著跑输指数)" if alpha<-8 else ("个股抗跌(跑赢指数)" if alpha>8 else "系统性(基本同步指数)")
    else:
        t = "早期无指数对照"
    key = f"{pk_d.strftime('%Y-%m')}-{tr_d.strftime('%Y-%m')}"
    old = old_dd_cause.get(key, {})
    # 优先用旧的人工 cause,否则用自动 type
    cause = old.get("cause") or t
    drawdowns.append({
        "peak": pk_d.strftime('%Y-%m'), "peakPrice": round(float(pk_p),2),
        "trough": tr_d.strftime('%Y-%m'), "troughPrice": round(float(tr_p),2),
        "depth": f"{round(md*100,1)}%", "stock_ret": sr, "index_ret": ir, "alpha": alpha,
        "type": t, "cause": cause
    })

# 写 drawdowns.md(混合字段保护)
mp.write_md(os.path.join(STOCK_DIR, "drawdowns.md"), {
    "type": "drawdowns", "stock": RAW_CODE, "updated": CUTOFF,
    "items": drawdowns,
    "summary": "回撤 Alpha 分解:区分系统性(同步指数)与个股(跑输指数)回撤"
}, "# 回撤分析\n\n每个回撤含个股 vs 指数同期表现,Alpha 为超额收益。")

# ============ 个股 vs 指数对比 ============
compare_series = []
if bench_df is not None:
    bench_df['month'] = bench_df['date'].dt.to_period('M')
    bm = bench_df.groupby('month').last().reset_index()
    bm['month'] = bm['month'].astype(str)
    common = max(monthly['month'].iloc[0], bm['month'].iloc[0])
    sm = monthly[monthly['month']>=common].reset_index(drop=True).tail(50)
    bm_map = dict(zip(bm['month'], bm['close']))
    if len(sm)>1:
        s0 = sm['close'].iloc[0]
        b0_list = [bm_map.get(m) for m in sm['month']]
        b0 = next((x for x in b0_list if x), None)
        if b0:
            for _,r in sm.iterrows():
                b = bm_map.get(r['month'])
                if b:
                    compare_series.append({"m":r['month'],"stock":round(float(r['close'])/s0*100,2),"index":round(float(b)/b0*100,2)})

# ============ 成交量 ============
df_vol = df.tail(504).copy()
df_vol['month'] = df_vol['date'].dt.to_period('M')
vm = df_vol.groupby('month')['volume'].mean().reset_index()
vm['month'] = vm['month'].astype(str)
volume_json = [{"m":r['month'],"v":round(float(r['volume']),0)} for _,r in vm.tail(24).iterrows()]

# ============ price_lookup ============
def price_at(ym):
    row = monthly[monthly['month']==ym]
    if len(row)>0: return round(float(row['close'].iloc[0]),2)
    target = pd.to_datetime(ym+"-01")
    idx = (monthly['date']-target).abs().idxmin()
    return round(float(monthly['close'].iloc[idx]),2)
price_lookup = {ym: price_at(ym) for ym in sorted(set(m['m'][:7] for m in monthly_json))}

# ============ 真实性自检 ============
checks = [
    ("日期一致性", f"数据年={latest_date[:4]} vs 截止年={CUTOFF[:4]}", latest_date[:4]==CUTOFF[:4] or int(latest_date[:4])==int(CUTOFF[:4])),
    ("ATH来源", f"程序计算={round(ath,2)}@{ath_date}", True),
    ("数据量", f"{len(df)}条日线", len(df)>200),
    ("指数数据", f"{bench_name} {len(bench_df) if bench_df is not None else 0}条", bench_df is not None and len(bench_df)>100),
]
print(f"\n=== 自检 ===")
for n,d,ok in checks: print(f"  [{'✓' if ok else '✗'}] {n}: {d}")

# ============ 写 data.json ============
result = {
    "meta": {"name":NAME,"code":RAW_CODE,"market":market,"cutoff":CUTOFF,"benchmark":bench_name,
             "full_fetch_date":full_fetch_date,"source":"akshare/yfinance",
             "daily_count":len(df),"monthly_count":len(monthly_json)},
    "stats": {"ath":round(ath,2),"ath_date":ath_date,"atl":round(atl,2),"atl_date":atl_date,
              "latest":round(latest,2),"latest_date":latest_date,
              "high_52w":round(high_52w,2),"low_52w":round(low_52w,2),"dd_from_ath":dd_ath},
    "monthly": monthly_json,
    "annual": annual,
    "compare_series": compare_series,
    "volume": volume_json,
    "price_lookup": price_lookup,
    "self_check": [{"name":n,"detail":d,"ok":ok} for n,d,ok in checks],
}
with open(DATA_FILE,"w",encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\n✅ 输出: {DATA_FILE}")
print(f"   日线: {CSV_FILE}")

# ============ 创建空的 .md 骨架(仅当不存在时,保护人工内容) ============
skeletons = {
    "events.md": {"type":"events","stock":RAW_CODE,"updated":CUTOFF,"items":[]},
    "phases.md": {"type":"phases","stock":RAW_CODE,"updated":CUTOFF,"items":[]},
    "forecast/scenarios.md": {"type":"scenarios","stock":RAW_CODE,"updated":CUTOFF,"scenarios":{}},
    "forecast/valuation.md": {"type":"valuation","stock":RAW_CODE,"updated":CUTOFF,"items":[],"evolution":[]},
    "forecast/catalysts.md": {"type":"catalysts","stock":RAW_CODE,"updated":CUTOFF,"catalysts":{"upside":[],"downside":[]}},
    "forecast/watchpoints.md": {"type":"watchpoints","stock":RAW_CODE,"updated":CUTOFF,"items":[],"strategy":[]},
    "fundamentals/moat.md": {"type":"moat","stock":RAW_CODE,"updated":CUTOFF,"items":[]},
    "fundamentals/three-good.md": {"type":"three-good","stock":RAW_CODE,"updated":CUTOFF,"three_good":{},"verdict":""},
    "fundamentals/chain.md": {"type":"chain","stock":RAW_CODE,"updated":CUTOFF,"chain":{}},
}
for rel, fm in skeletons.items():
    fp = os.path.join(STOCK_DIR, rel)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    if not os.path.exists(fp):
        mp.write_md(fp, fm, f"# {fm['type']}\n\n(待 AI agent 填写)")
        print(f"   创建骨架: {rel}")

# ============ commit 提示 ============
print(f"\n📝 建议 commit:")
print(f'   git add analyses/{safe_name(NAME)}-{RAW_CODE}/')
if do_full:
    print(f'   git commit -m "{NAME} 首次全量分析 ({CUTOFF})"')
else:
    print(f'   git commit -m "{NAME} 增量更新至 {CUTOFF}"')
