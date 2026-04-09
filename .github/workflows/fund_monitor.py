import requests
import json
import time
import os
from datetime import datetime

# ====================== 【核心配置】 ======================
# 1. 在这里改成你要监控的基金代码
FUND_CODES = ["007818", "017470", "017471", "021075","020274","019875","025857","016874","013841","017992","011036","006105","018147","001467","000218", "021190","012895","161226", ]

# 2. 持仓信息：成本、份额，没有持仓就不动
HOLDING = {
    "007818": {"cost": 3.0029, "shares": 799.04},
    "017470": {"cost": 2.1859, "shares": 7319.67},
    "017471": {"cost": 2.0211, "shares": 9895.6},
    "021075": {"cost": 1.9896, "shares": 13068},
    "020274": {"cost": 1.6067, "shares": 6223.83},
    "019875": {"cost": 2.0436, "shares": 3425.39},
    "025857": {"cost": 1.3242, "shares": 1510.35},
    "016874": {"cost": 1.4782, "shares": 2367.77},
    "013841": {"cost": 1.7320, "shares": 2020.83},
    "017992": {"cost": 1.7066, "shares": 2343.86},
    "011036": {"cost": 1.4910, "shares": 9389.38},
    "006105": {"cost": 1.3703, "shares": 2189.37},
    "018147": {"cost": 1.7370, "shares": 575.71},
    "001467": {"cost": 2.4326, "shares": 4932.91},
    "000218": {"cost": 3.9617, "shares": 2335.26},
    "021190": {"cost": 1.3267, "shares": 2261.25},
    "012895": {"cost": 1.0487, "shares": 29560.8},
    "161226": {"cost": 2.9490, "shares": 101.73},
}

# 预警阈值
FALL_THRESHOLD = -1.5
RISE_THRESHOLD = 3.0
DRAWDOWN_THRESHOLD = 2.0

# 3. 这里替换成你刚才复制的 Server酱 SendKey
SERVER_SENDKEY = "SCT335868TYRNLiY7FEdkaJzToYohUKgwc"

DATA_DIR = "data"
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
# ==========================================================

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def ensure_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def get_fund_base(fund_code):
    try:
        url = f"https://fundgz.1234567.com.cn/js/{fund_code}.js?rt={int(time.time())}"
        resp = requests.get(url, headers=HEADERS, timeout=8)
        txt = resp.text.strip().replace("jsonpgz(", "").rstrip(");")
        d = json.loads(txt)
        return {
            "code": fund_code,
            "name": d.get("name", ""),
            "gz": float(d.get("gsz", 0)),
            "gz_time": d.get("gztime", ""),
            "change": float(d.get("gszzl", 0)),
            "dwjz": float(d.get("dwjz", 0)),
        }
    except Exception as e:
        return {"code": fund_code, "error": str(e)}

def get_fund_capital(fund_code):
    try:
        url = f"https://fund.eastmoney.com/api/FundNetServers/FundInfoNew?callback=jQuery&fundCode={fund_code}"
        resp = requests.get(url, headers=HEADERS, timeout=8)
        txt = resp.text.strip()
        txt = txt[txt.find("({")+1 : txt.rfind("})")+1]
        d = json.loads(txt)
        main_net = float(d.get("ZJLJE", 0))
        return {
            "main_net": round(main_net, 2),
            "style": "净流入" if main_net > 0 else "净流出"
        }
    except:
        return {"main_net": 0, "style": "获取失败"}

def get_top_stocks(fund_code):
    return ["贵州茅台", "宁德时代", "招商银行", "中国平安", "隆基绿能"]

def calc_profit(f):
    code = f["code"]
    if code not in HOLDING:
        return {"profit": 0, "profit_rate": 0, "hold": False}
    cost = HOLDING[code]["cost"]
    shares = HOLDING[code]["shares"]
    gz = f["gz"]
    profit = round((gz - cost) * shares, 2)
    profit_rate = round((gz / cost - 1) * 100, 2)
    return {"profit": profit, "profit_rate": profit_rate, "hold": True}

def calc_drawdown(history, code):
    try:
        values = []
        for h in history[-6:]:
            for f in h["funds"]:
                if f["code"] == code and "gz" in f:
                    values.append(f["gz"])
        if len(values) < 2:
            return 0
        max_val = max(values)
        latest = values[-1]
        dd = round((max_val - latest) / max_val * 100, 2)
        return dd
    except:
        return 0

def send_wechat(content):
    if not SERVER_SENDKEY or "这里粘贴你的SendKey" in SERVER_SENDKEY:
        print("未配置Server酱，跳过推送")
        return
    try:
        payload = {"title": "基金监控预警", "desp": content}
        url = f"https://sctapi.ftqq.com/{SERVER_SENDKEY}.send"
        requests.post(url, json=payload, timeout=10)
        print("微信推送成功")
    except Exception as e:
        print("微信推送失败", e)

def save_history(items):
    ensure_dir()
    now = datetime.now().strftime("%m-%d %H:%M")
    record = {"time": now, "funds": items}
    data = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try: data = json.load(f)
            except: data = []
    data.append(record)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data[-60:], f, ensure_ascii=False, indent=2)
    return data

def main():
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try: history = json.load(f)
            except: history = []

    fund_list = []
    alert = ["【基金实时监控预警】\n"]
    has_alert = False

    for code in FUND_CODES:
        base = get_fund_base(code)
        if "error" in base:
            fund_list.append(base)
            continue

        flow = get_fund_capital(code)
        stocks = get_top_stocks(code)
        profit = calc_profit(base)
        dd = calc_drawdown(history, code)

        base["flow"] = flow
        base["stocks"] = stocks
        base["profit"] = profit
        base["drawdown"] = dd
        fund_list.append(base)

        chg = base["change"]
        name = base["name"]
        if chg <= FALL_THRESHOLD:
            alert.append(f"⚠️ {name} 跌幅 {chg:.2f}%")
            has_alert = True
        if chg >= RISE_THRESHOLD:
            alert.append(f"📈 {name} 涨幅 {chg:.2f}%")
            has_alert = True
        if dd >= DRAWDOWN_THRESHOLD:
            alert.append(f"〽️ {name} 近期回撤 {dd:.2f}%")
            has_alert = True

    print("===== 基金实时监控 =====")
    for f in fund_list:
        if "error" in f:
            print(f"{f['code']} 获取失败")
            continue
        print(f"{f['code']}{f['name']:8}|估值{f['gz']:.3f}|涨跌{f['change']:5.2f}%|收益{f['profit']['profit']:6.0f}元|回撤{f['drawdown']:.2f}%")

    save_history(fund_list)
    if has_alert:
        send_wechat("\n".join(alert))

if __name__ == "__main__":
    main()
