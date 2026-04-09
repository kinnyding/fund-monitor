# 基金监控核心脚本（小白零错误版）
import requests
import pandas as pd
import json
import time
from datetime import datetime

# -------------------------- 只改这3个地方！其他绝对不要动！ --------------------------
# 1. 你的基金代码（多个用逗号分隔，比如 '000001,000002'）
FUND_CODES = '007818,017470,017471,021075,020274,019875","025857,016874,013841,017992,011036,006105,018147,001467,000218,021190,012895,161226'
# 2. 你的持仓份额（没有就填0，不影响监控）
HOLD_SHARES='799.04,7319.67,9895.6,13068,6223.83,3425.39,1510.35,2367.77,2020.83,2343.86,9389.38,2189.37,575.71,4932.91,2335.26,2261.25,29560.8,101.73'
# 3. 你的Server酱SendKey（从https://sct.ftqq.com复制的那一串）
SENDKEY = 'SCT335868TYRNLiY7FEdkaJzToYohUKgwc'
# -----------------------------------------------------------------------------------

# 基金数据API（稳定可用）
API_URL = 'https://fund.eastmoney.com/api/qt/summary/getfundsummarybypage?fundcodes={}&appversion=6.7.9&deviceid=abc123&version=6.7.9'
# Server酱推送API
PUSH_URL = f'https://sctapi.ftqq.com/{SENDKEY}.send'

# 获取基金数据
def get_fund_data(fund_codes):
    url = API_URL.format(fund_codes)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None
    data = response.json()
    return data['data']['list']

# 推送微信提醒
def push_wechat(title, content):
    data = {
        'text': title,
        'desp': content
    }
    requests.post(PUSH_URL, data=data)

# 生成网页看板
def generate_html(fund_list):
    html_content = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>基金监控看板</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        h1 { text-align: center; color: #333; }
        .fund-card { background: white; border-radius: 8px; padding: 20px; margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .fund-name { font-size: 1.2em; font-weight: bold; color: #222; }
        .fund-info { display: flex; justify-content: space-between; margin-top: 10px; }
        .rise { color: #f43f3f; font-weight: bold; }
        .fall { color: #00b578; font-weight: bold; }
        .update-time { text-align: center; color: #666; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>📊 基金实时监控看板</h1>
'''
    for fund in fund_list:
        fund_name = fund['name']
        fund_code = fund['code']
        nav = fund['nav']
        change = fund['change']
        change_rate = fund['change_rate']
        # 判断涨跌
        if float(change_rate) >= 0:
            rise_fall_class = 'rise'
            rise_fall_icon = '📈'
        else:
            rise_fall_class = 'fall'
            rise_fall_icon = '📉'
        # 计算收益
        if HOLD_SHARES > 0:
            profit = round(float(change) * HOLD_SHARES, 2)
            profit_text = f'持仓收益: {profit} 元'
        else:
            profit_text = '未持仓'
        # 拼接卡片
        html_content += f'''
        <div class="fund-card">
            <div class="fund-name">{rise_fall_icon} {fund_name} ({fund_code})</div>
            <div class="fund-info">
                <div>最新净值: {nav}</div>
                <div class="{rise_fall_class}">涨跌幅: {change_rate}%</div>
                <div class="{rise_fall_class}">涨跌额: {change} 元</div>
                <div>{profit_text}</div>
            </div>
        </div>
'''
    # 加更新时间
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html_content += f'<div class="update-time">最后更新时间: {now}</div></body></html>'
    # 保存html文件
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

# 主函数
def main():
    print("开始获取基金数据...")
    # 获取基金数据
    fund_list = get_fund_data(FUND_CODES)
    if not fund_list:
        print("获取数据失败！")
        push_wechat("基金监控报错", "获取基金数据失败，请检查网络或基金代码")
        return
    # 生成网页看板
    generate_html(fund_list)
    print("网页看板生成成功！")
    # 检查涨跌，推送提醒
    for fund in fund_list:
        change_rate = float(fund['change_rate'])
        # 涨跌超过2%推送提醒（可以自己改阈值，比如1%就改成1）
        if abs(change_rate) >= 2:
            title = f"⚠️ {fund['name']} 涨跌超2%！"
            content = f"""
基金代码: {fund['code']}
基金名称: {fund['name']}
最新净值: {fund['nav']}
涨跌幅: {fund['change_rate']}%
涨跌额: {fund['change']} 元
更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            push_wechat(title, content)
            print(f"已推送{fund['name']}涨跌提醒")
    print("监控任务完成！")

if __name__ == '__main__':
    main()
