import requests
import json
from datetime import datetime

# ====================== 只改这里 ======================
FUND_CODES = ['007818,017470,017471,021075,020274,019875,025857,016874,013841,017992,011036,006105,018147,001467,000218,021190,012895,161226']  # 换成你的基金代码，多个就加逗号
SENDKEY = "SCT335868TgnsxWmSspSDMnVkHCvfB6YzV"
# ======================================================

def get_fund_info(fund_code):
    url = f"https://fundgz.1234567.com.cn/js/{fund_code}.js"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        text = r.text.replace("jsonpgz(", "").replace(");", "")
        data = json.loads(text)
        return {
            "code": fund_code,
            "name": data.get("name", ""),
            "gsz": data.get("gsz", ""),
            "gszzl": data.get("gszzl", ""),
            "gztime": data.get("gztime", "")
        }
    except Exception as e:
        print(f"获取 {fund_code} 失败: {e}")
        return None

def send_wechat(title, content):
    if not SENDKEY:
        print("未配置SendKey，不推送")
        return
    url = f"https://sctapi.ftqq.com/{SENDKEY}.send"
    data = {
        "title": title,
        "desp": content
    }
    try:
        requests.post(url, data=data, timeout=10)
        print("微信推送成功")
    except:
        print("微信推送失败")

def main():
    print("开始获取基金实时估值...")
    fund_list = []
    for code in FUND_CODES:
        info = get_fund_info(code)
        if info:
            fund_list.append(info)

    if not fund_list:
        send_wechat("基金监控异常", "未获取到任何基金数据")
        return

    # 拼接推送内容
    msg = ""
    for f in fund_list:
        msg += f"基金：{f['name']} ({f['code']})\n"
        msg += f"估算净值：{f['gsz']}\n"
        msg += f"估算涨跌幅：{f['gszzl']}%\n"
        msg += f"更新时间：{f['gztime']}\n\n"

    now = datetime.now().strftime("%m-%d %H:%M")
    send_wechat(f"基金实时估值 {now}", msg)
    print("执行完成")

if __name__ == "__main__":
    main()
