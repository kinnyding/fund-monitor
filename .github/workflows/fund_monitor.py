import requests
import json
from datetime import datetime

# ==============================================
# 🚨 只改这2个地方！其他代码绝对不要动！
# ==============================================
# 1. 你的基金代码（多个用逗号分隔，放在[]里，比如 ['000001','001481']）
FUND_CODES = ['007818','017470','017471','021075','020274','019875','025857','016874','013841','017992','011036','006105','018147','001467','000218','021190','012895','161226']
# 2. 你的Server酱SendKey（从https://sct.ftqq.com复制的完整密钥）
SENDKEY = "SCT335868TgnsxWmSspSDMnVkHCvfB6YzV"
# ==============================================

# 稳定可用的天天基金接口（不会失效，已做完整异常处理）
def get_fund_data(fund_code):
    url = f"https://fundgz.1234567.com.cn/js/{fund_code}.js"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        # 发送请求，超时10秒避免卡死
        response = requests.get(url, headers=headers, timeout=10)
        # 处理接口返回的特殊格式（jsonpgz(...)）
        text = response.text.strip()
        if not text:
            print(f"基金{fund_code}返回空数据")
            return None
        # 去掉前后缀，转为标准JSON
        json_str = text.replace("jsonpgz(", "").rstrip(");")
        data = json.loads(json_str)
        # 提取关键数据
        return {
            "code": fund_code,
            "name": data.get("name", "未知基金"),
            "estimate_nav": data.get("gsz", "--"),
            "estimate_change_rate": data.get("gszzl", "--"),
            "update_time": data.get("gztime", "--")
        }
    except Exception as e:
        print(f"获取基金{fund_code}数据失败: {str(e)}")
        return None

# 微信推送（Server酱）
def push_wechat(title, content):
    if not SENDKEY or SENDKEY == "你的SendKey在这里":
        print("未配置SendKey，跳过微信推送")
        return
    url = f"https://sctapi.ftqq.com/{SENDKEY}.send"
    data = {
        "title": title,
        "desp": content
    }
    try:
        requests.post(url, data=data, timeout=10)
        print("微信推送成功")
    except Exception as e:
        print(f"微信推送失败: {str(e)}")

# 主函数
def main():
    print("🚀 开始执行基金监控任务...")
    fund_list = []
    # 遍历所有基金代码，获取数据
    for code in FUND_CODES:
        fund_info = get_fund_data(code)
        if fund_info:
            fund_list.append(fund_info)
    
    # 如果没有获取到任何数据，推送异常提醒
    if not fund_list:
        push_wechat("⚠️ 基金监控异常", "未获取到任何基金数据，请检查代码配置")
        return
    
    # 拼接推送内容
    push_content = "📊 基金实时估值更新\n\n"
    for fund in fund_list:
        # 判断涨跌，加表情
        rate = float(fund["estimate_change_rate"]) if fund["estimate_change_rate"] != "--" else 0
        emoji = "📈" if rate >= 0 else "📉"
        push_content += f"{emoji} {fund['name']} ({fund['code']})\n"
        push_content += f"估算净值: {fund['estimate_nav']}\n"
        push_content += f"估算涨跌幅: {fund['estimate_change_rate']}%\n"
        push_content += f"更新时间: {fund['update_time']}\n\n"
    
    # 推送微信提醒
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    push_wechat(f"基金监控 {now}", push_content)
    print("✅ 基金监控任务执行完成！")

if __name__ == "__main__":
    main()
