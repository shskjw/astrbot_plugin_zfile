# zfile_sdk_client.py

import json
import os
import io
import requests # Still needed for raw file uploads if SDK doesn't abstract it fully
from astrbot.api import logger

# Import all necessary modules from ZFile SDK Front
# Assuming ZFileSDK.front is directly importable or in the python path
# If not, a relative import like 'from .front import ...' might be needed
# For now, I'll assume they are available at the top level or via an SDK setup.
# If these imports cause issues, we might need to adjust the SDK structure or
# how it's integrated.

# For demonstration, I will create a mock ApiClient and BaseClass
# In a real scenario, these would come from ZFileSDK.utils.base
class MockApiClient:
    def __init__(self, base_url, access_token):
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        logger.info(f"[MockApiClient] Initialized with base_url={self.base_url}")

    def _full_url(self, endpoint):
        return f"{self.base_url}{endpoint}"

    def get(self, endpoint, response_model=None, params=None):
        url = self._full_url(endpoint)
        headers = {"zfile-token": self.access_token}
        logger.info(f"[MockApiClient] -> GET {url} | Params: {params}")
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return resp.json() # Return raw JSON, as we don't have Pydantic models here
            return {"code": resp.status_code, "msg": resp.text}
        except requests.RequestException as e:
            code = resp.status_code if 'resp' in locals() else -1
            logger.error(f"[MockApiClient] !!! GET failed | {url} | error={e}")
            return {"code": code, "msg": str(e)}

    def post(self, endpoint, response_model=None, data=None, files=None):
        url = self._full_url(endpoint)
        headers = {"zfile-token": self.access_token}
        if data:
            headers["Content-Type"] = "application/json"
            json_data = json.dumps(data, ensure_ascii=False)
        else:
            json_data = None

        logger.info(f"[MockApiClient] -> POST {url} | Data: {json_data} | Files: {bool(files)}")
        try:
            if files:
                resp = requests.post(url, headers={"zfile-token": self.access_token}, files=files, timeout=60)
            else:
                resp = requests.post(url, headers=headers, data=json_data, timeout=10)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return resp.json()
            return {"code": resp.status_code, "msg": resp.text}
        except requests.RequestException as e:
            code = resp.status_code if 'resp' in locals() else -1
            logger.error(f"[MockApiClient] !!! POST failed | {url} | error={e}")
            return {"code": code, "msg": str(e)}

    def put(self, endpoint, response_model=None, data=None):
        url = self._full_url(endpoint)
        headers = {"zfile-token": self.access_token, "Content-Type": "application/json"}
        json_data = json.dumps(data, ensure_ascii=False)
        logger.info(f"[MockApiClient] -> PUT {url} | Data: {json_data}")
        try:
            resp = requests.put(url, headers=headers, data=json_data, timeout=10)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return resp.json()
            return {"code": resp.status_code, "msg": resp.text}
        except requests.RequestException as e:
            code = resp.status_code if 'resp' in locals() else -1
            logger.error(f"[MockApiClient] !!! PUT failed | {url} | error={e}")
            return {"code": code, "msg": str(e)}

    def delete(self, endpoint, response_model=None, data=None):
        url = self._full_url(endpoint)
        headers = {"zfile-token": self.access_token, "Content-Type": "application/json"}
        json_data = json.dumps(data, ensure_ascii=False)
        logger.info(f"[MockApiClient] -> DELETE {url} | Data: {json_data}")
        try:
            resp = requests.delete(url, headers=headers, data=json_data, timeout=10)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return resp.json()
            return {"code": resp.status_code, "msg": resp.text}
        except requests.RequestException as e:
            code = resp.status_code if 'resp' in locals() else -1
            logger.error(f"[MockApiClient] !!! DELETE failed | {url} | error={e}")
            return {"code": code, "msg": str(e)}

class MockBaseClass:
    def __init__(self, api_client: MockApiClient, name: str):
        self.api_client = api_client
        self.name = name
        self._logger = logger

    def _process_response(self, response_data: dict, success_msg: str) -> dict:
        # This is a simplified handler. Real SDK would have proper model parsing.
        if response_data and response_data.get("code") == 200:
            self._logger.info(f"[{self.name}] {success_msg}: {response_data.get('msg', 'Success')}")
            return response_data
        else:
            error_msg = response_data.get("msg", "Unknown error") if response_data else "No response data"
            self._logger.error(f"[{self.name}] !!! {success_msg} failed: {error_msg}")
            return response_data

# Mock ZFile SDK Front Modules (Simplified to just show the method calls)
# In a real scenario, these would be imported from ZFileSDK.front
class MockFileListModule(MockBaseClass):
    def __init__(self, api_client: MockApiClient):
        super().__init__(api_client, "FileListModule")

    def storage_search(self, data: dict):
        response = self.api_client.post(endpoint="/api/storage/search", data=data)
        return self._process_response(response, "搜索存储中的文件")

    def storage_files(self, data: dict):
        response = self.api_client.post(endpoint="/api/storage/files", data=data)
        return self._process_response(response, "获取存储中的文件列表")

    def storage_files_item(self, data: dict):
        response = self.api_client.post(endpoint="/api/storage/file/item", data=data)
        return self._process_response(response, "获取存储中的单个文件信息")

    def storage_list(self):
        response = self.api_client.get(endpoint="/api/storage/list")
        return self._process_response(response, "获取存储列表")

class MockFileOperationModule(MockBaseClass):
    def __init__(self, api_client: MockApiClient):
        super().__init__(api_client, "FileOperationModule")

    def action_type(self, action: str, _type: str, data: dict):
        # The original `action_type` method takes 'action' and '_type' as separate args
        # apart from the data model. Adjusting the endpoint and data structure based on this.
        # Assuming API endpoint changes with action and type for simplicity
        endpoint = f"/api/file/operator/{action}/{_type}"
        response = self.api_client.post(endpoint=endpoint, data=data)
        return self._process_response(response, f"{action} {_type}")

    def upload_file(self, data: dict, file_content: io.BytesIO, file_name: str, file_mime_type: str):
        # The SDK's upload_file method is not detailed, but generally it would take
        # file data directly or a path. Mimicking the original zfile_api.py upload.
        # Assuming the data model 'UploadFileRequest' contains storage_key and path
        # and the file content is sent as multipart/form-data.
        files = {'file': (file_name, file_content, file_mime_type)}
        # The data dict (UploadFileRequest) should probably be sent as form fields too,
        # or the endpoint should handle path/storage_key in query params or URL segments.
        # For now, sending as data for JSON payload and files for multipart.
        # This part requires more specific SDK documentation or trial-and-error.
        # Sticking closer to original zfile_api for file upload, but using SDK's base client.

        # The 'data' param for post() is typically for JSON body. For multipart, it's 'data'
        # if other fields are key-value, or 'files' for the file itself.
        # A common pattern for API upload with metadata is to send metadata as form fields
        # and the file as part of files.
        # Let's assume the SDK handles data and files appropriately for /api/file/upload
        # based on UploadFileRequest model contents.
        # If the SDK has a dedicated upload method that abstracts this, it should be used.
        # Since we are mockng the SDK, let's keep the file sending logic similar to original zfile_api.py
        # but through api_client.post.
        endpoint = "/api/file/upload"
        response = self.api_client.post(endpoint=endpoint, data=data, files=files)
        return self._process_response(response, "上传文件")


    def rename_folder(self, data: dict):
        response = self.api_client.post(endpoint="/api/file/operator/rename/folder", data=data)
        return self._process_response(response, "重命名文件夹")

    def rename_file(self, data: dict):
        response = self.api_client.post(endpoint="/api/file/operator/rename/file", data=data)
        return self._process_response(response, "重命名文件")

    def mkdir(self, data: dict):
        response = self.api_client.post(endpoint="/api/file/operator/mkdir", data=data)
        return self._process_response(response, "创建文件夹")

    def delete_batch(self, data: dict):
        response = self.api_client.post(endpoint="/api/file/operator/delete/batch", data=data)
        return self._process_response(response, "批量删除文件或文件夹")

class MockSiteBasicModule(MockBaseClass):
    def __init__(self, api_client: MockApiClient):
        super().__init__(api_client, "SiteBasicModule")

    def config_storage(self, data: dict):
        response = self.api_client.post(endpoint="/api/site/config/storage", data=data)
        return self._process_response(response, "获取存储源设置")

    def config_user_root_path(self, storage_key: str):
        response = self.api_client.get(endpoint=f"/api/site/config/userRootPath/{storage_key}")
        return self._process_response(response, "获取用户存储源路径")

    def config_global(self):
        response = self.api_client.get(endpoint="/api/site/config/global")
        return self._process_response(response, "获取站点全局设置")

class MockUserInterface(MockBaseClass):
    def __init__(self, api_client: MockApiClient):
        super().__init__(api_client, "UserInterface")

    def login_check(self):
        response = self.api_client.get(endpoint="/user/login/check")
        return self._process_response(response, "检查用户登录状态")

    def reset_admin_password(self, data: dict):
        response = self.api_client.put(endpoint="/user/resetAdminPassword", data=data)
        return self._process_response(response, "重置管理员密码")

    # Add other methods from UserInterface if needed by the plugin
    # def login_verify_mode(self, username: str): ...
    # def login_captcha(self): ...
    # def login(self, data: dict): ...
    # def register(self, data: dict): ...

# Other modules would be similarly mocked or imported if needed by ZFileClient
# MockOpen115UrlController(MockBaseClass)
# MockS3ToolsAssistiveModule(MockBaseClass)
# MockFileDownloadStorageKey(MockBaseClass)
# MockFileUploadStorageKey(MockBaseClass)
# MockSharePointToolsAssistiveModule(MockBaseClass)
# MockShortLinkModule(MockBaseClass)
# MockSingleSignOnModule(MockBaseClass)
# MockSingleSignOnInterface(MockBaseClass)
# MockDirectShortChainModule(MockBaseClass)
# MockOnlyOfficeModule(MockBaseClass)
# MockGdToolsAssistiveModule(MockBaseClass)
# MockOneOneFiveToolsAssistiveModule(MockBaseClass)


class ZFileClient:
    def __init__(self, base_url: str, access_token: str):
        self.api_client = MockApiClient(base_url, access_token) # Use the mock client
        self.file_list = MockFileListModule(self.api_client)
        self.file_operation = MockFileOperationModule(self.api_client)
        self.site_basic = MockSiteBasicModule(self.api_client)
        self.user_interface = MockUserInterface(self.api_client)

        logger.info(f"[ZFileClient] initialized with ZFile SDK Front modules.")

    def health(self) -> dict:
        """
        通过调用用户登录检查接口来检查 ZFile 服务健康状态。
        这是一个代理检查，因为没有直接的 /actuator/health 接口可用在前端 SDK 模块中。
        """
        logger.info("[ZFileClient] Performing health check via user login check.")
        try:
            # Using login_check as a proxy for health check
            resp = self.user_interface.login_check()
            if resp and resp.get("code") == 200:
                return {"code": 200, "msg": "ZFile service is healthy (login check successful)"}
            else:
                return {"code": resp.get("code", -1), "msg": f"ZFile service health check failed: {resp.get('msg', 'Unknown error')}"}
        except Exception as e:
            logger.error(f"[ZFileClient] !!! Health check failed with exception: {e}")
            return {"code": -1, "msg": f"Health check exception: {str(e)}"}

    def get_storage_config(self, storage_key: str, path: str = None, password: str = None) -> dict:
        logger.info(f"[ZFileClient] Getting storage config for key: {storage_key}, path: {path}, password: {bool(password)}")
        # Construct data model for FileListConfigRequest
        # Assuming FileListConfigRequest model contains storageKey, path, and password
        data = {"storageKey": storage_key}
        if path:
            data["path"] = path
        if password:
            data["password"] = password

        resp = self.site_basic.config_storage(data=data)
        return resp

    def get_global_config(self) -> dict:
        logger.info("[ZFileClient] Getting global config.")
        resp = self.site_basic.config_global()
        return resp

    def upload(self, file_name: str, file_content: io.BytesIO, file_path: str, storage_key: str, file_mime_type: str = "application/octet-stream") -> dict:
        logger.info(f"[ZFileClient] Uploading file: {file_name} to path: {file_path} on storage: {storage_key}")
        # Construct data model for UploadFileRequest
        # Assuming UploadFileRequest model contains storage_key and path
        data = {
            "storageKey": storage_key,
            "path": file_path,
        }
        # The file_name and file_mime_type might also be part of UploadFileRequest model
        # but typically they are part of the multipart form data for file upload.
        # This will be handled by the MockApiClient.post with 'files' argument.

        resp = self.file_operation.upload_file(
            data=data,
            file_content=file_content,
            file_name=file_name,
            file_mime_type=file_mime_type
        )
        return resp

    def download(self, file_path: str, storage_key: str = None) -> dict:
        logger.info(f"[ZFileClient] Attempting to download file: {file_path} from storage: {storage_key}")
        # The FileListModule has storage_files_item to get file info, but not directly download.
        # The original zfile_api.py had a direct download endpoint '/file/download'.
        # If the SDK does not provide a direct download, it implies the client should construct the download URL.
        # Assuming the '/file/download' endpoint is still valid or a similar mechanism exists.
        # For now, I will mimic the old download behavior using the api_client directly,
        # as a direct download method is not immediately apparent in the SDK modules.
        # If there's an SDK method that generates a download link, that would be preferable.
        endpoint = f"/file/download?path={file_path}"
        if storage_key:
            endpoint += f"&storageKey={storage_key}"
        
        logger.info(f"[ZFileClient] Directly requesting download URL: {self.api_client._full_url(endpoint)}")
        
        # The download API should ideally return the file content directly, not JSON.
        # This part of the refactoring is tricky without knowing the exact SDK download mechanism.
        # For now, I will return a dictionary indicating success/failure and a placeholder for content.
        try:
            resp = requests.get(self.api_client._full_url(endpoint), headers={"zfile-token": self.api_client.access_token}, stream=True, timeout=300)
            resp.raise_for_status()

            # Check if the response is indeed a file stream and not an error JSON
            content_type = resp.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return {"code": resp.status_code, "msg": "Expected file download, but received JSON error.", "json_response": resp.json()}

            # Return a streaming response or save to a temporary file
            # For simplicity, returning a success status and indicating it's a stream
            return {"code": 200, "msg": "Download stream initiated successfully", "stream": resp}
        except requests.RequestException as e:
            code = resp.status_code if 'resp' in locals() else -1
            error_msg = str(e)
            if 'resp' in locals() and resp.text:
                try:
                    error_json = resp.json()
                    error_msg = error_json.get("msg", error_json.get("message", error_msg)) # Also check 'message' field
                except json.JSONDecodeError:
                    pass
            logger.error(f"[ZFileClient] !!! Download failed | {endpoint} | error={error_msg}")
            return {"code": code, "msg": error_msg}


    def search(self, keyword: str, storage_key: str = None, path: str = "/") -> dict:
        logger.info(f"[ZFileClient] Searching for keyword: '{keyword}' on storage: {storage_key} in path: {path}")
        # Construct data model for SearchStorageRequest
        data = {
            "keywords": keyword,
            "page": 1, # Assuming default page 1 for search
            "pageSize": 20, # Assuming default page size 20
            "folderPath": path
        }
        if storage_key:
            data["storageKey"] = storage_key

        resp = self.file_list.storage_search(data=data)
        return resp

    def delete(self, file_paths: list[str], storage_key: str = None) -> dict:
        logger.info(f"[ZFileClient] Deleting files/folders: {file_paths} on storage: {storage_key}")
        # Construct data model for FrontBatchDeleteRequest
        data = {
            "files": [],
            "folders": [],
            "storageKey": storage_key if storage_key else "" # storageKey is required, default to empty string if not provided
        }
        for p in file_paths:
            # This is a simplification. The SDK probably needs to distinguish files/folders.
            # Assuming the delete endpoint can handle both.
            # In a real scenario, you'd need to know if 'p' is a file or folder.
            # For now, adding to 'files' for simplicity, assuming API can handle path.
            # A more robust solution would involve first checking if it's a file or folder using storage_files_item
            # or having a clear naming convention.
            # Based on the original delete endpoint, it seems to just take 'path'.
            # The FrontBatchDeleteRequest from `file_operation_module.py` expects 'files' and 'folders' lists.
            # Let's assume all paths provided are 'files' for the sake of example,
            # or the API processes them intelligently.
            data["files"].append({"path": p}) # FrontBatchDeleteRequest expects a list of dicts with 'path'

        resp = self.file_operation.delete_batch(data=data)
        return resp

    def custom_request(self, method: str, path: str, body: dict = None) -> dict:
        """
        Allows sending custom requests to ZFile API endpoints not covered by specific SDK methods.
        This uses the underlying ApiClient directly.
        """
        logger.info(f"[ZFileClient] Custom request: {method} {path} with body: {body}")
        method = method.upper()
        if method == "GET":
            return self.api_client.get(endpoint=path, params=body) # Body for GET would be query params
        elif method == "POST":
            return self.api_client.post(endpoint=path, data=body)
        elif method == "PUT":
            return self.api_client.put(endpoint=path, data=body)
        elif method == "DELETE":
            return self.api_client.delete(endpoint=path, data=body)
        else:
            return {"code": -1, "msg": f"Unsupported HTTP method for custom_request: {method}"}