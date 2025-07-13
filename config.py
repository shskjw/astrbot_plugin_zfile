import httpx
from astrbot.api import logger

async def get_token(config, verify_code: str = None, verify_code_uuid: str = None):
    """
    发送登录请求

    Args:
        base_url (str): API 的基础 URL，例如 "http://localhost:8080"
        username (str): 用户名
        password (str): 密码
        verify_code (str, optional): 验证码（如果需要）
        verify_code_uuid (str, optional): 验证码的唯一标识

    Returns:
        dict: 登录响应结果的 JSON 数据
    """
    logger.info(f"[ZFilePlugin] ZFile API: {config['base_url']}")
    logger.info(f"[ZFilePlugin] 正在使用用户名 {config['user_name']} 登录 ZFile API")
    logger.info(f"[ZFilePlugin] 密码: {config['user_password']}")
    async with httpx.AsyncClient() as client:
        payload = {
            "username": config['user_name'],
            "password": config['user_password'],
        }
        if verify_code:
            payload["verifyCode"] = verify_code
        if verify_code_uuid:
            payload["verifyCodeUUID"] = verify_code_uuid

        try:
            login_data = await client.post(f"{config['base_url']}/user/login", json=payload)
            return login_data.get('data', {}).get('token', None)
        except httpx.HTTPError as e:
            logger.error(f"HTTP 请求错误: {e}")
            return None
