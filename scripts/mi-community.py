import os
import requests
import json


#变量名mi_community_cookie为cookie在https://account.xiaomi.com/pass/sns/wxapp/v2/tokenLogin接口中
#变量名mi_community_user_info为用户信息在https://account.xiaomi.com/pass/sns/wxapp/v2/code接口的cookie中

def get_cookies_from_env():
    mi_community_cookie = os.getenv("mi_community_cookie")
    if not mi_community_cookie:
        raise ValueError("环境变量中未找到mi_community_cookie，请确保已正确设置环境变量。")
    return mi_community_cookie

    
def get_user_info_from_env():
    mi_community_user_info = os.getenv("mi_community_user_info")
    if not mi_community_user_info:
        raise ValueError("环境变量中未找到mi_community_user_info，请确保已正确设置环境变量。")
    return mi_community_user_info

def get_login_data(cookie, userInfo):
    """
    发送登录请求，获取签到所需的参数
    """
    url = "https://account.xiaomi.com/pass/sns/wxapp/v2/tokenLogin"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://servicewechat.com/wx240a4a764023c444/7/page-frame.html",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090b19)XWEB/13639",
        "Accept-Encoding": "gzip, deflate, br"
    }
    data = {
        "appid": "wx240a4a764023c444",
        "sid": "miui_vip",
        "authType": "0",
        "callback": ""
    }
    cookies = {
        "wxSToken": '8Rt3UyqDam/tVvIHcU4NGQVqsuOpCvc944ddPN7yNB1KJMMUwEDadTPUKmtEadGdWMFg9qj51hG/wb7TDWfcQZ++Klo2Gjig8zlPiYuxrTMAnNzVvGVwOyCBT4ESrA9dDD0Xus03fQU+ok1T51CUnvWASiy3U9cWGwatr2kHR8zEO1aLVQV/1pZdqf8ivaTj',
        "userInfo": userInfo
    }
    response = requests.post(url, headers=headers, cookies=cookies, data=data)
    responseData = response.json()
    print(f"登录接口响应：{responseData}")
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"登录请求失败，状态码：{response.status_code}")

def checkin(miui_vip_ph, serviceToken, userId):
    """
    执行签到操作
    """
    url = "https://api.vip.miui.com/mtop/planet/vip/member/addCommunityGrowUpPointByActionV2"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090b19)XWEB/13639",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded",
        "xweb_xhr": "1",
        "Origin": "https://servicewechat.com",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://servicewechat.com/wx240a4a764023c444/7/page-frame.html",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }
    cookies = {
        "serviceToken": serviceToken,
        "miui_vip_ph": miui_vip_ph,
        "userId": str(userId)
    }
    params = {"miui_vip_ph": miui_vip_ph}
    data = {"action": "WECHAT_CHECKIN_TASK"}
    
    response = requests.post(url, headers=headers, cookies=cookies, params=params, data=data)
    print(f"签到接口响应：{response}")
    return response.json()

def handle_checkin_result(phone, result):
    """
    处理签到结果并输出通知
    """
    data = {"title": "小米社区签到", "content": ""}
    if result.get("status") == 200:
        print(f"{phone} 签到成功！")
        data["content"] = f"{phone} 签到成功！"
    elif result.get("status") == -1 and result.get("message") == "加分失败":
        print(f"{phone} 签到失败：今天已经签到过了。")
        data["content"] = f"{phone} 签到失败：今天已经签到过了。"
    elif result.get("code") == 401:
        print(f"{phone} 签到失败：参数错误或登录信息失效。")
        data["content"] = f"{phone} 签到失败：参数错误或登录信息失效。"
    else:
        print(f"{phone} 签到失败：未知错误。返回结果：{result}")
        data["content"] = f"{phone} 签到失败：未知错误。返回结果：{result}"

    QLAPI.systemNotify(data)

def main():
    try:
        
        # 获取环境变量中的cookie
        cookie = get_cookies_from_env()
        userInfo = get_user_info_from_env()
        login_data = get_login_data(cookie, userInfo)
        miui_vip_ph = login_data["miui_vip_ph"]
        serviceToken = login_data["serviceToken"]
        userId = login_data["passportProfile"]["userId"]
        phone = login_data["passportProfile"]["phone"]  # 获取 phone 值
            
        # 执行签到
        checkin_response = checkin(miui_vip_ph, serviceToken, userId)
        handle_checkin_result(phone, checkin_response)
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()