import httpx
from astrbot.api import logger

def get_token(config, verify_code: str = None, verify_code_uuid: str = None):
    """
    发送登录请求

    Args:
        config (dict): 配置字典，包含 base_url、user_name、user_password 等信息
        verify_code (str, optional): 验证码（如果需要）
        verify_code_uuid (str, optional): 验证码的唯一标识

    Returns:
        str: 访问令牌（access_token）
    """
    logger.info(f"[ZFilePlugin] ZFile API: {config['base_url']}")
    logger.info(f"[ZFilePlugin] 正在使用用户名 {config['user_name']} 登录 ZFile API")
    logger.info(f"[ZFilePlugin] 密码: {config['user_password']}")
    with httpx.Client() as client:
        payload = {
            "username": config['user_name'],
            "password": config['user_password'],
        }
        if verify_code:
            payload["verifyCode"] = verify_code
        if verify_code_uuid:
            payload["verifyCodeUUID"] = verify_code_uuid

        try:
            response = client.post(f"{config['base_url']}/user/login", json=payload)
            response.raise_for_status()  # 检查 HTTP 状态码是否为 200 系列
            login_result = response.json()
            return login_result.get('data', {}).get('token')
        except httpx.HTTPError as e:
            logger.error(f"HTTP 请求错误: {e}")
            return None