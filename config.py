import httpx
from astrbot.api import logger
from urllib.parse import urlparse

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
            base_url = urlparse(config['zfile_base_url'])
            login = client.post(f"{base_url}/user/login", json=payload)
            logger.info(f"[ZFilePlugin] 登录请求响应: {login.status_code} - {login.text}")
            return login.get('data', {}).get('token')
        except httpx.HTTPError as e:
            logger.error(f"HTTP 请求错误: {e}")
            return None