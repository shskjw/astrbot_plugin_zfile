# 导入核心客户端
from ZfileSDK.utils.api_client import ApiClient
from ZfileSDK.front import FileListModule, UserInterface
import json


# 使用上下文管理器自动处理登录和注销
with open('config.json', 'r') as f:
    config = json.loads(f.read())


with ApiClient(base_url=config["zfile_base_url"], token=config["access_token"]) as client:
    # client.login(username="740424462", password="MCmm431322")
    file_list_module = FileListModule(client)
    # files = file_list_module.storage_files(
    #     storage_key="1",
    #     path="2",
    #     password=None
    # )
    #
    # # print(files)
    # # print(files.data.files)
    # for file in files.data.files:
    #     print(f"文件名: {file.name}")
    #     print(f"文件路径: {file.path}")
    #     print(f"文件类型: {file.type}")
    #     print("---------------")
    user_interface = UserInterface(client)
    print(user_interface.login_check())
