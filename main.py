import io
import os
import typing

import requests
from ZfileSDK.utils.models import DeleteItem, BatchGenerateLinkRequest
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

from ZfileSDK.utils import ApiClient
from ZfileSDK.front import *
from ZfileSDK.admin import *
from astrbot.core.message.components import Reply, File, Image, Video, BaseMessageComponent


@register("zfile_plugin", "溜溜球", "基于 ZFile API 的文件管理插件", "0.1.0")
class ZFilePlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.context = context

        self.zf = ApiClient(config['zfile_base_url'], config['access_token'])

        logger.info(f"[ZFilePlugin] ZFile base URL loaded: {config['zfile_base_url']}")

        self.admins = config['admins']
        self.perm = config['permissions']

    async def initialize(self):
        user_interface = UserInterface(self.zf)
        check = user_interface.login_check()
        logger.info("ZFile 插件就绪：" + check.data.to_str())
        return check.data.is_login

    @staticmethod
    def _uid(evt: AstrMessageEvent):
        uid = None
        if hasattr(evt, 'get_user_id'):
            try:
                uid = evt.get_user_id()
            except Exception:
                pass
        if uid is None and hasattr(evt, 'user_id'):
            uid = evt.user_id
        return uid

    def _check_admin(self, uid: int) -> bool:
        return uid in self.admins

    def _check_permission(self, uid: int, permission_type: str, admin_only_check: str) -> bool:
        if self._check_admin(uid):
            return True
        if not self.perm.get(f"{permission_type}_enabled", False):
            return False
        if self.perm.get(f"{admin_only_check}", False):
            return False
        return True

    @staticmethod
    def _human_readable_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


@filter.command("文件列表")
async def cmd_ls(self, event: AstrMessageEvent):
    uid = self._uid(event)
    if not self._check_permission(uid, "search", "search_admin_only"):
        yield event.plain_result("你没有权限执行文件列表或搜索操作。")
        return

    parts = event.message_str.strip().split(maxsplit=2)
    storage_key = None
    path = "/"

    if len(parts) > 1:
        storage_key = parts[1].strip()
    if len(parts) > 2:
        path = parts[2].strip()

    logger.info(f"[ZFilePlugin] LS command: storage_key={storage_key}, path={path}")
    if not storage_key:
        yield event.plain_result("错误：请提供存储源key。例如：文件列表 1 / 或 文件列表 your_storage_key /path")
        return

    try:
        file_list_module = FileListModule(self.zf)
        files = file_list_module.storage_files(
            storage_key=storage_key,
            path=path
        )

        # 检查 files 是否有效以及是否包含有效的 data 和 files
        if files and files.data and hasattr(files.data, 'files'):
            files_list = files.data.files
            if not files_list:
                yield event.plain_result(f"路径 '{path}' 下没有内容。")
                return

            response_lines = [f"文件列表（{storage_key}:{path}）："]
            for item in files_list:
                name = item.name
                _type = item.type
                size = item.size
                if _type == "FOLDER":
                    response_lines.append(f"📁 {name}/")
                else:
                    readable_size = self._human_readable_size(size)
                    response_lines.append(f"📄 {name} ({readable_size})")
            yield event.plain_result("\n".join(response_lines))
        else:
            yield event.plain_result(f"无法获取路径 '{path}' 下的文件列表，请检查配置或API连接。")
    except Exception as e:
        logger.error(f"[ZFilePlugin] Error in LS command: {e}", exc_info=True)
        yield event.plain_result(f"执行文件列表命令时发生错误：{e}")


@filter.command("上传文件")
async def cmd_upload(self, event: AstrMessageEvent):
    uid = self._uid(event)
    if not self._check_permission(uid, "upload", "upload_admin_only"):
        yield event.plain_result("你没有权限执行上传操作。")
        return

    parts = event.message_str.strip().split(maxsplit=3)
    if len(parts) == 3:
        storage_key = parts[1].strip()
        remote_path = parts[2].strip()
        file_name = remote_path.split("/")[-1]
    else:
        yield event.plain_result(
            "上传命令格式：上传文件 [storageKey] [remotePath(可选)]。例如：上传文件 local /path/to/upload。请确保同时附带文件。"
        )
        return

    message_obj = event.message_obj
    file_message: BaseMessageComponent = message_obj.message[0]
    if file_message.type != "Reply":
        yield event.plain_result("请引用你要上传的文件")
        return
    else:
        file_message: Reply
        replay_chain = file_message.chain
        replay_message = replay_chain[0]
        if replay_message.type in ["File", "Image", "Video"]:
            replay_message: typing.Optional[File, Image, Video]
            file_url = replay_message.url
            file_data = requests.get(file_url).content
        else:
            yield event.plain_result("请引用你要上传的文件")
            return

    file_size = len(file_data)

    logger.info(f"[ZFilePlugin] 准备上传 {file_name} 到 {storage_key}:{remote_path}")

    try:
        file_module = FileOperationModule(self.zf)
        file_module.upload_file(
            storage_key=storage_key,
            path=remote_path,
            name=file_name,
            size=file_size,
        )

        file_upload_model = FileUploadStorageKey(self.zf)
        response = file_upload_model.upload_proxy(
            storage_key=storage_key,
            path=remote_path,
            filestream=file_data,
            filename=file_name,
        )
        uploaded_files_info = f"✅ 文件 '{file_name}' 上传成功: {response.msg}"
    except Exception as e:
        logger.error(f"[ZFilePlugin] 上传文件 '{file_name}' 出错：{e}", exc_info=True)
        uploaded_files_info = f"❌ 文件 '{file_name}' 上传失败：{e}"

    yield event.plain_result(uploaded_files_info)


@filter.command("下载文件")
async def cmd_download(self, event: AstrMessageEvent):
    uid = self._uid(event)
    if not self._check_permission(uid, "download", "download_admin_only"):
        yield event.plain_result("你没有权限执行下载操作。")
        return

    parts = event.message_str.strip().split(maxsplit=1)
    if len(parts) < 2:
        yield event.plain_result(
            "下载命令格式：下载文件 [storageKey:]path/to/file。例如：下载文件 local:/folder/myfile.txt")
        return

    full_path_with_storage = parts[1].strip()
    storage_key = None
    file_path = full_path_with_storage

    if ":" in full_path_with_storage:
        try:
            storage_key, file_path = full_path_with_storage.split(":", 1)
        except ValueError:
            yield event.plain_result("路径格式错误。请使用 storageKey:/path/to/file 或 /path/to/file")
            return

    logger.info(f"[ZFilePlugin] 下载文件: storage_key={storage_key}, file_path={file_path}")

    try:
        file_list_module = FileListModule(self.zf)
        file = file_list_module.storage_files_item(
            storage_key=storage_key,
            path=file_path
        )

        downloaded_file_name = os.path.basename(file_path)

        file_content_bytes = requests.get(file.data.url).content

        if file_content_bytes:
            yield event.file_result(file_content_bytes, downloaded_file_name)
            yield event.plain_result(f"✅ 文件 '{downloaded_file_name}' 下载成功！")
        else:
            yield event.plain_result(f"❌ 文件 '{downloaded_file_name}' 下载失败：文件内容为空。")
    except Exception as e:
        logger.error(f"[ZFilePlugin] 下载文件时出错：{e}", exc_info=True)
        yield event.plain_result(f"处理下载文件时发生错误：{e}")


@filter.command("生成短链")
async def cmd_generate_short_link(self, event: AstrMessageEvent):
    # 移除权限和文件大小限制，所有人均可调用
    parts = event.message_str.strip().split(maxsplit=1)
    if len(parts) < 2:
        yield event.plain_result(
            "生成短链命令格式：生成短链 [storageKey:]path/to/file。例如：生成短链 local:/folder/myfile.txt")
        return

    full_path_with_storage = parts[1].strip()
    storage_key = None
    file_path = full_path_with_storage

    if ":" in full_path_with_storage:
        try:
            storage_key, file_path = full_path_with_storage.split(":", 1)
        except ValueError:
            yield event.plain_result("路径格式错误。请使用 storageKey:/path/to/file 或 /path/to/file")
            return

    try:
        direct_short_chain_module = DirectShortChainModule(self.zf)
        response = direct_short_chain_module.short_link_batch_generate(
            storage_key=storage_key,
            paths=[file_path],
            expire_time=86400,
        )
        if not response.msg == "ok":
            yield event.plain_result(f"生成短链失败：{response.msg}")
            return

        short_link_url = response.data[0].address
        yield event.plain_result(f"✅ 文件短链生成成功：{short_link_url}")
    except Exception as e:
        yield event.plain_result(f"生成短链时出错：{e}")


@filter.command("搜索")
async def cmd_search(self, event: AstrMessageEvent):
    uid = self._uid(event)
    if not self._check_permission(uid, "search", "search_admin_only"):
        yield event.plain_result("你没有权限执行搜索操作。")
        return

    parts = event.message_str.strip().split(maxsplit=3)
    if len(parts) < 2:
        yield event.plain_result(
            "搜索命令格式：搜索 [关键词] [storageKey(可选)] [路径(可选)]。例如：搜索 document local /")
        return

    keyword = parts[1].strip()
    storage_key = None
    path = "/"

    if len(parts) > 2:
        storage_key = parts[2].strip()
    if len(parts) > 3:
        path = parts[3].strip()

    logger.info(f"[ZFilePlugin] 搜索命令: keyword='{keyword}', storage_key={storage_key}, path={path}")

    file_list_module = FileListModule(self.zf)
    try:
        files = file_list_module.storage_search(
            storage_key=storage_key,
            search_keyword=keyword,
            search_mode="search_all",
            path=path,
        )

        file_items = files.data
        if not file_items:
            yield event.plain_result(f"没有找到与 '{keyword}' 匹配的内容。")
            return

        response_lines = [f"搜索结果（关键词：'{keyword}'）："]
        for item in file_items:
            name = item.name
            _type = item.type
            path = item.path
            size = item.size
            readable_size = self._human_readable_size(size) if _type != "FOLDER" else ""

            if _type == "FOLDER":
                response_lines.append(f"📁 {name}/ ({path})")
            else:
                response_lines.append(f"📄 {name} ({readable_size}) ({path})")
        yield event.plain_result("\n".join(response_lines))
    except Exception as e:
        logger.error(f"[ZFilePlugin] 搜索时出错：{e}", exc_info=True)
        yield event.plain_result(f"搜索失败：{e}")


@filter.command("删除")
async def cmd_delete(self, event: AstrMessageEvent):
    uid = self._uid(event)
    if not self._check_permission(uid, "delete", "delete_admin_only"):
        yield event.plain_result("你没有权限执行删除操作。")
        return

    parts = event.message_str.strip().split(maxsplit=2)
    if len(parts) < 2:
        yield event.plain_result("删除命令格式：删除 [storageKey:]path1,[storageKey:]path2,...")
        yield event.plain_result("例如：删除 local:/folder/file1.txt,local:/folder/subfolder")
        return

    full_paths_str = parts[1].strip()
    paths_to_delete = [p.strip() for p in full_paths_str.split(',')]

    results = []
    delete_items_by_storage = {}
    file_list_module = FileListModule(self.zf)
    file_operation_module = FileOperationModule(self.zf)

    for full_path_with_storage in paths_to_delete:
        storage_key = None
        item_path = full_path_with_storage
        if ":" in full_path_with_storage:
            try:
                storage_key, item_path = full_path_with_storage.split(":", 1)
            except ValueError:
                results.append(f"❌ 路径格式错误 '{full_path_with_storage}'。跳过。")
                continue

        logger.info(f"[ZFilePlugin] 准备删除: storage_key={storage_key}, item_path={item_path}")
        try:
            file_info_response = file_list_module.storage_files_item(
                storage_key=storage_key,
                path=item_path
            )
            if file_info_response.code != "0":
                results.append(f"❌ 获取 '{full_path_with_storage}' 信息失败：{file_info_response.msg}")
                continue

            file_data = file_info_response.data
            if storage_key not in delete_items_by_storage:
                delete_items_by_storage[storage_key] = []
            delete_items_by_storage[storage_key].append(DeleteItem(
                path=file_data.path,
                name=file_data.name,
                type=file_data.type,
            ))
        except Exception as e:
            results.append(f"❌ 准备删除 '{full_path_with_storage}' 时发生错误：{e}")
            logger.error(f"[ZFilePlugin] 删除准备失败 {full_path_with_storage}: {e}", exc_info=True)

    for storage_key, items in delete_items_by_storage.items():
        try:
            res = file_operation_module.delete_batch(
                storage_key=storage_key,
                delete_items=items,
            )
            if res.code == "0":
                results.append(f"✅ 从存储源 '{storage_key}' 删除了 {len(items)} 个项目。")
            else:
                results.append(f"❌ 从存储源 '{storage_key}' 删除失败：{res.msg}")
        except Exception as e:
            results.append(f"❌ 执行删除时发生错误：{e}")
            logger.error(f"[ZFilePlugin] 删除执行失败 {storage_key}：{e}", exc_info=True)

    yield event.plain_result("\n".join(results))


@filter.command("获取存储源列表")
async def cmd_storage_list(self, event: AstrMessageEvent):
    uid = self._uid(event)
    if not self._check_admin(uid):
        yield event.plain_result("仅管理员可查询存储源列表。")
        return

    storage_model = StorageSourceModuleBasic(self.zf)
    try:
        res = storage_model.storage_list()
        if res.code == "0":
            res_list_str = "\n".join([_.to_json() for _ in res.data])
            yield event.plain_result(f"存储源列表：\n{res_list_str}")
        else:
            yield event.plain_result(f"获取存储源列表失败：{res.msg}")
    except Exception as e:
        logger.error(f"[ZFilePlugin] 获取存储源列表失败：{e}", exc_info=True)
        yield event.plain_result(f"获取存储源列表时发生错误：{e}")


@filter.command("获取存储源设置")
async def cmd_storage_config(self, event: AstrMessageEvent):
    uid = self._uid(event)
    if not self._check_admin(uid):
        yield event.plain_result("仅管理员可查询存储源设置。")
        return

    parts = event.message_str.strip().split(maxsplit=1)
    if len(parts) < 2:
        yield event.plain_result("格式：获取存储源设置 [storageID]，例如：获取存储源设置 1")
        return

    storage_id_str = parts[1].strip()
    try:
        storage_id = int(storage_id_str)
    except ValueError:
        yield event.plain_result("存储源ID必须为数字，例如：获取存储源设置 1")
        return

    storage_model = StorageSourceModuleBasic(self.zf)
    try:
        res = storage_model.storage_item(storage_id=storage_id)
        if res.code == "0":
            yield event.plain_result(f"存储源设置：\n{res.data.to_json()}")
        else:
            yield event.plain_result(f"获取存储源设置失败：{res.msg}")
    except Exception as e:
        logger.error(f"[ZFilePlugin] 获取存储源设置失败：{e}", exc_info=True)
        yield event.plain_result(f"获取存储源设置时发生错误：{e}")


@filter.command("获取全局设置")
async def cmd_global_config(self, event: AstrMessageEvent):
    uid = self._uid(event)
    if not self._check_admin(uid):
        yield event.plain_result("仅管理员可查询全局设置。")
        return

    site_model = SiteBasicModule(self.zf)
    try:
        res = site_model.config_global()
        if res.code == "0":
            yield event.plain_result(f"全局设置：\n{res.data.to_json()}")
        else:
            yield event.plain_result(f"获取全局设置失败：{res.msg}")
    except Exception as e:
        logger.error(f"[ZFilePlugin] 获取全局设置失败：{e}", exc_info=True)
        yield event.plain_result(f"获取全局设置时发生错误：{e}")
