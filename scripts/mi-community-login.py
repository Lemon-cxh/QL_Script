# cron:0 0 0/2 * *
# new Env("小米社区登录")
import os
import requests
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('mi_community_login')

# 常量定义
API_LOGIN_URL = "https://account.xiaomi.com/pass/sns/wxapp/v2/tokenLogin"
WX_APP_ID = "wx240a4a764023c444"
WX_REFERER = "https://servicewechat.com/wx240a4a764023c444/7/page-frame.html"
WX_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090b19)XWEB/13639"

def get_token_from_env():
    """
    从环境变量获取小米社区token
    
    Returns:
        str: 小米社区token值
        
    Raises:
        ValueError: 环境变量未设置时抛出
    """
    mi_community_token = os.getenv("mi_community_token")
    if not mi_community_token:
        raise ValueError("环境变量中未找到mi_community_token，请确保已正确设置环境变量。")
    return mi_community_token

    
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


def get_login_data(token, user_info):
    """
    发送登录请求，获取签到所需的参数
    
    Args:
        token: 小米社区token
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
        "wxSToken": token,
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


def update_env_tokens(login_data):
    """
    更新环境变量中的token信息
    
    Args:
        login_data: 登录响应数据
    """
    try:
        miui_vip_ph = login_data["miui_vip_ph"]
        service_token = login_data["serviceToken"]
        user_id = login_data["passportProfile"]["userId"]
        phone = login_data["passportProfile"]["phone"]
        
        # 更新环境变量
        QLAPI.updateEnv({
            "mi_community_service_token": service_token,
            "mi_community_miui_vip_ph": miui_vip_ph,
            "mi_community_user_id": str(user_id),
            "mi_community_phone": phone
        })
        
        logger.info(f"用户 {phone} 的token已更新到环境变量")
        
        # 发送成功通知
        QLAPI.systemNotify({
            "title": "小米社区登录",
            "content": f"用户 {phone} 登录成功，token已更新"
        })
        
    except KeyError as e:
        error_msg = f"登录响应数据缺少必要字段：{e}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"更新环境变量失败：{e}"
        logger.error(error_msg)
        raise


def main():
    """
    主函数，执行小米社区登录保持token流程
    """
    try:
        # 获取环境变量中的凭证
        token = get_token_from_env()
        user_info = get_user_info_from_env()
        
        # 登录获取新的token
        login_data = get_login_data(token, user_info)
        
        # 更新环境变量中的token信息
        update_env_tokens(login_data)
        
    except Exception as e:
        error_msg = f"登录保持token过程中发生错误: {e}"
        logger.error(error_msg)
        
        # 发送错误通知
        try:
            QLAPI.systemNotify({"title": "小米社区登录", "content": error_msg})
        except Exception:
            pass  # 忽略通知失败的错误


if __name__ == "__main__":
    main()