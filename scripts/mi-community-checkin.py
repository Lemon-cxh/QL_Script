# cron:0 12 * * *
# new Env("小米社区签到")
import os
import requests
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('mi_community_checkin')

# 常量定义
API_CHECKIN_URL = "https://api.vip.miui.com/mtop/planet/vip/member/addCommunityGrowUpPointByActionV2"
WX_REFERER = "https://servicewechat.com/wx240a4a764023c444/7/page-frame.html"
WX_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090b19)XWEB/13639"

def get_checkin_params_from_env():
    """
    从环境变量获取签到所需的参数
    
    Returns:
        tuple: (service_token, miui_vip_ph, user_id, phone)
        
    Raises:
        ValueError: 环境变量未设置时抛出
    """
    service_token = os.getenv("mi_community_service_token")
    miui_vip_ph = os.getenv("mi_community_miui_vip_ph")
    user_id = os.getenv("mi_community_user_id")
    phone = os.getenv("mi_community_phone")
    
    if not all([service_token, miui_vip_ph, user_id, phone]):
        missing_vars = []
        if not service_token:
            missing_vars.append("mi_community_service_token")
        if not miui_vip_ph:
            missing_vars.append("mi_community_miui_vip_ph")
        if not user_id:
            missing_vars.append("mi_community_user_id")
        if not phone:
            missing_vars.append("mi_community_phone")
        
        raise ValueError(f"环境变量中缺少以下参数：{', '.join(missing_vars)}，请先运行登录脚本获取token。")
    
    return service_token, miui_vip_ph, user_id, phone


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
        content = f"{phone} 签到失败：参数错误或登录信息失效，请重新运行登录脚本。"
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
        # 获取环境变量中的签到参数
        service_token, miui_vip_ph, user_id, phone = get_checkin_params_from_env()
        
        # 执行签到
        checkin_response = perform_checkin(miui_vip_ph, service_token, user_id)
        process_checkin_result(phone, checkin_response)
        
    except Exception as e:
        error_msg = f"签到过程中发生错误: {e}"
        logger.error(error_msg)
        
        # 发送错误通知
        try:
            QLAPI.systemNotify({"title": "小米社区签到", "content": error_msg})
        except Exception:
            pass  # 忽略通知失败的错误


if __name__ == "__main__":
    main()