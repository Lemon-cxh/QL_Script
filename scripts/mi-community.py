import os
import requests
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('mi_community')

# 常量定义
API_LOGIN_URL = "https://account.xiaomi.com/pass/sns/wxapp/v2/tokenLogin"
API_CHECKIN_URL = "https://api.vip.miui.com/mtop/planet/vip/member/addCommunityGrowUpPointByActionV2"
WX_APP_ID = "wx240a4a764023c444"
WX_REFERER = "https://servicewechat.com/wx240a4a764023c444/7/page-frame.html"
WX_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090b19)XWEB/13639"
WX_TOKEN = '8Rt3UyqDam/tVvIHcU4NGQVqsuOpCvc944ddPN7yNB1KJMMUwEDadTPUKmtEadGdWMFg9qj51hG/wb7TDWfcQZ++Klo2Gjig8zlPiYuxrTMAnNzVvGVwOyCBT4ESrA9dDD0Xus03fQU+ok1T51CUnvWASiy3U9cWGwatr2kHR8zEO1aLVQV/1pZdqf8ivaTj'


def get_cookie_from_env():
    """
    从环境变量获取小米社区cookie
    
    Returns:
        str: 小米社区cookie值
        
    Raises:
        ValueError: 环境变量未设置时抛出
    """
    mi_community_cookie = os.getenv("mi_community_cookie")
    if not mi_community_cookie:
        raise ValueError("环境变量中未找到mi_community_cookie，请确保已正确设置环境变量。")
    return mi_community_cookie

    
def get_user_info_from_env():
    """
    从环境变量获取小米社区用户信息
    
    Returns:
        str: 小米社区用户信息
        
    Raises:
        ValueError: 环境变量未设置时抛出
    """
    mi_community_user_info = os.getenv("mi_community_user_info")
    if not mi_community_user_info:
        raise ValueError("环境变量中未找到mi_community_user_info，请确保已正确设置环境变量。")
    return mi_community_user_info


def get_login_data(cookie, user_info):
    """
    发送登录请求，获取签到所需的参数
    
    Args:
        cookie: 小米社区cookie
        user_info: 小米社区用户信息
        
    Returns:
        dict: 登录响应数据，包含签到所需的token和用户信息
        
    Raises:
        Exception: 请求失败时抛出
    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": WX_REFERER,
        "User-Agent": WX_USER_AGENT,
        "Accept-Encoding": "gzip, deflate, br"
    }
    data = {
        "appid": WX_APP_ID,
        "sid": "miui_vip",
        "authType": "0",
        "callback": ""
    }
    cookies = {
        "wxSToken": WX_TOKEN,
        "userInfo": user_info
    }
    
    try:
        response = requests.post(API_LOGIN_URL, headers=headers, cookies=cookies, data=data)
        response_data = response.json()
        logger.info(f"登录接口响应：{response_data}")
        
        if response.status_code == 200:
            return response_data
        else:
            raise Exception(f"登录请求失败，状态码：{response.status_code}")
    except requests.RequestException as e:
        logger.error(f"登录请求异常：{e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"登录响应解析失败：{e}")
        raise ValueError("登录响应格式错误")


def perform_checkin(miui_vip_ph, service_token, user_id):
    """
    执行签到操作
    
    Args:
        miui_vip_ph: 小米社区VIP标识
        service_token: 服务令牌
        user_id: 用户ID
        
    Returns:
        dict: 签到响应数据
        
    Raises:
        Exception: 请求失败时抛出
    """
    headers = {
        "User-Agent": WX_USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded",
        "xweb_xhr": "1",
        "Origin": "https://servicewechat.com",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": WX_REFERER,
        "Accept-Language": "zh-CN,zh;q=0.9"
    }
    cookies = {
        "serviceToken": service_token,
        "miui_vip_ph": miui_vip_ph,
        "userId": str(user_id)
    }
    params = {"miui_vip_ph": miui_vip_ph}
    data = {"action": "WECHAT_CHECKIN_TASK"}
    
    try:
        response = requests.post(API_CHECKIN_URL, headers=headers, cookies=cookies, params=params, data=data)
        logger.info(f"签到接口响应：{response}")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"签到请求异常：{e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"签到响应解析失败：{e}")
        raise ValueError("签到响应格式错误")


def process_checkin_result(phone, result):
    """
    处理签到结果并输出通知
    
    Args:
        phone: 用户手机号
        result: 签到API返回的结果
        
    Returns:
        dict: 通知内容
    """
    notification = {"title": "小米社区签到", "content": ""}
    status = result.get("status")
    message = result.get("message", "")
    code = result.get("code")
    
    if status == 200:
        title = result.get("entity", {}).get("title", "")
        content = f"{phone} 签到成功！{title}"
    elif status == -1 and message == "加分失败":
        content = f"{phone} 签到失败：今天已经签到过了。{message}"
    elif code == 401:
        content = f"{phone} 签到失败：参数错误或登录信息失效。"
    else:
        content = f"{phone} 签到失败：{message}。返回结果：{result}"
    
    logger.info(content)
    notification["content"] = content
    
    # 发送系统通知
    try:
        QLAPI.systemNotify(notification)
    except Exception as e:
        logger.error(f"发送通知失败: {e}")
    
    return notification


def main():
    """
    主函数，执行小米社区签到流程
    """
    try:
        # 获取环境变量中的凭证
        cookie = get_cookie_from_env()
        user_info = get_user_info_from_env()
        
        # 登录获取签到所需参数
        login_data = get_login_data(cookie, user_info)
        miui_vip_ph = login_data["miui_vip_ph"]
        service_token = login_data["serviceToken"]
        user_id = login_data["passportProfile"]["userId"]
        phone = login_data["passportProfile"]["phone"]
            
        # 执行签到
        checkin_response = perform_checkin(miui_vip_ph, service_token, user_id)
        process_checkin_result(phone, checkin_response)
    except Exception as e:
        error_msg = f"执行过程中发生错误: {e}"
        logger.error(error_msg)
        
        # 发送错误通知
        try:
            QLAPI.systemNotify({"title": "小米社区签到", "content": error_msg})
        except Exception:
            pass  # 忽略通知失败的错误


if __name__ == "__main__":
    main()