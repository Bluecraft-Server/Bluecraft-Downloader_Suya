import ctypes
import json
import os
import shutil
import sys
import tempfile
import threading
import zipfile
from tkinter import messagebox

import requests

Suya_Updater_Version = "1.0.2.9"


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


if os.name == 'nt':
    if not is_admin():
        # 如果当前没有管理员权限，则重新启动脚本并请求管理员权限
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()


def show_message(partner, partner_en):
    """
    定义一个显示消息框的函数
    """
    messagebox.showinfo("提示 / Tip",
                        f"更新已开始，在更新完成后，Suya Downloader将会自动启动，请等待自动重启，本次更新类型为{partner}。\n"
                        "The update has been started, after the update is finished, Suya Downloader will open "
                        f"automatically, please wait for the automatic reboot, the type of this update is {partner_en}")


# 当前工作目录
current_dir = os.getcwd()

# 指定路径
settings_path = os.path.join("./Settings")
global_config_path = os.path.join("./Settings", "global_config.json")
default_api_setting_path = os.path.join(".", "default_api_setting.json")

# 确保设置的文件夹存在
if not os.path.exists(settings_path):
    os.makedirs(settings_path)


def merge_jsons(default_json, file_path):
    """
    合并两个 JSON 对象，优先使用文件中的数据。
    :param default_json: 默认的 JSON 字典
    :param file_path: 文件路径
    :return: 合并后的 JSON 字典
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            loaded_json = json.load(file)
            # 使用文件中的数据覆盖默认值
            return {**default_json, **loaded_json}
    except FileNotFoundError:
        # 如果文件不存在，直接返回默认值
        return default_json
    except Exception as e:
        # 如果发生其他错误，打印错误信息并返回默认值
        print(f"Error loading JSON from {file_path}: {e}")
        return default_json


def get_config():
    default_api_config = {
        "server_api_url": "https://Bluecraft-Server.github.io/API/Python_Downloader_API/Get_API.json"
    }
    try:
        default_global_config = merge_jsons(default_api_config, default_api_setting_path)
    except:
        try:
            default_global_config = default_api_config
            with open(default_api_setting_path, 'w', encoding='utf-8') as file:
                json.dump(default_api_config, file, indent=4)
                print("成功写入初始API参数")
        except:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()
    try:
        api_content = requests.get(default_global_config["server_api_url"]).json()
    except:
        api_content = default_api_config
    try:
        default_global_config = merge_jsons(default_global_config, api_content)
    except:
        print("出现异常：" + str(Exception))
    final_global_config = merge_jsons(default_global_config, global_config_path)
    ### 此处代码将于1.0.3.0删除
    if final_global_config[
        "api_url"] == "https://Bluecraft-Server.github.io/API/Python_Downloader_API/Check_Version.json":
        final_global_config["api_url"] = "https://api.suya.blue-millennium.fun/Check_Version.json"
        print("检测到旧API地址，已自动更新为最新API地址")
    if final_global_config["api_url"] == "https://api.suya.blue-millennium.fun/Check_Version.json":
        final_global_config["api_url"] = "https://api.suya.blue-millennium.fun/Suya_Update_API.json"
    ### 此处代码将于1.0.3.0删除
    with open(global_config_path, 'w', encoding='utf-8') as file:
        json.dump(final_global_config, file, indent=4)
    return final_global_config


global_json = get_config()
api_url = global_json['api_url']

# 创建或覆盖版本文件
global_json['Updater_Version'] = Suya_Updater_Version
with open(global_config_path, 'w', encoding='utf-8') as file:
    json.dump(global_json, file, ensure_ascii=False, indent=4)


def del_Resources():
    folder_path = './Resources-Downloader'
    try:
        shutil.rmtree(folder_path)
        print(f"'{folder_path}' 文件夹已成功删除。")
    except FileNotFoundError:
        print(f"'{folder_path}' 文件夹未找到。")
    except Exception as e:
        print(f"删除 '{folder_path}' 文件夹时发生错误: {e}")


def fetch_update_info():
    if os.name == 'nt':
        """从API获取版本信息和下载链接"""
        try:
            try:
                Update_Partner = global_json['Update_Partner']
            except:
                global_json['Updater_Partner'] = "Full"
                with open(global_config_path, 'w', encoding='utf-8') as f:
                    json.dump(global_json, f, ensure_ascii=False, indent=4)
                Update_Partner = "Full"
            try:
                Count = global_json['Pull_Resources_Count']
                print("尝试拉取次数：" + str(Count))
            except:
                Count = 1
            if Count >= 3:
                Update_Partner = "Full"
            json_str = requests.get(api_url).text.strip()
            data = json.loads(json_str)
            if Update_Partner == "Full":
                downloader_update_url = data['url_downloader']
                version = data['version_downloader']
                partner = "完整更新模式"
                partner_en = "FULL UPDATE MODE"
                message_thread = threading.Thread(target=show_message, args=(partner, partner_en,))
                # 启动线程
                message_thread.start()
                return version, downloader_update_url, Update_Partner
            elif Update_Partner == "Resources":
                downloader_update_url = data['url_resource']
                partner = "重新拉取资源文件模式"
                partner_en = "RESOURCES PULL MODE"
                message_thread = threading.Thread(target=show_message, args=(partner, partner_en,))
                # 启动线程
                message_thread.start()
                return None, downloader_update_url, Update_Partner
            else:
                print("传入参数错误")
                return None, None, None
        except requests.RequestException as e:
            print(f"请求错误: {e}")
            return None, None, None


def download_and_install(downloader_update_url, update_partner_inner):
    """下载ZIP文件并覆盖安装，完成后运行Launcher"""
    try:
        response = requests.get(downloader_update_url, stream=True)
        response.raise_for_status()
        # 定义临时目录和临时文件
        temp_dir = tempfile.mkdtemp()
        temp_zip_file = os.path.join(temp_dir, "temp.zip")
        # 将响应内容写入临时文件
        with open(temp_zip_file, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        del_Resources()
        if update_partner_inner == "Resources":
            # 构建完整的目录路径，基于当前工作目录
            pull_dir = os.path.join(current_dir, "Resources-Downloader")
            # 确保"Resource"目录存在，如果不存在则创建
            if not os.path.exists(pull_dir):
                print(f"Resources目录不存在，将进行重新创建")
                os.makedirs(pull_dir, exist_ok=True)
        else:
            pull_dir = current_dir
        # 创建ZipFile对象，从临时文件中读取
        with zipfile.ZipFile(temp_zip_file) as zip_file:
            # 解压到目标目录
            for member in zip_file.namelist():
                # 避免路径遍历攻击
                member_path = os.path.abspath(os.path.join(pull_dir, member))
                if not member_path.startswith(pull_dir):
                    raise Exception("Zip file contains invalid path.")
                if member.endswith('/'):
                    os.makedirs(member_path, exist_ok=True)
                else:
                    with open(member_path, 'wb') as f:
                        f.write(zip_file.read(member))

        # 清理临时ZIP文件
        os.remove(temp_zip_file)

        global_json['Pull_Resources_Count'] = 0
        with open(global_config_path, 'w', encoding='utf-8') as file:
            json.dump(global_json, file, ensure_ascii=False, indent=4)
        print("更新安装完成")

        # 确保Launcher.exe存在于当前目录下再尝试运行
        if os.name == 'nt':
            launcher_path = os.path.join(current_dir, 'Launcher.exe')
        else:
            launcher_path = os.path.join(current_dir, 'Launcher')
        if os.path.isfile(launcher_path):
            import subprocess
            subprocess.Popen([launcher_path])
            print("Launcher已启动。")
        else:
            print("Launcher未找到。")
    except Exception as e:
        print(f"下载或解压错误: {e}")


def Update_Launcher():
    version, downloader_update_url, Update_partner = fetch_update_info()
    if version and downloader_update_url:
        print(f"发现新版本: {version}，开始下载...")
        download_and_install(downloader_update_url, Update_partner)
    elif downloader_update_url:
        print("正在重新拉取Resources")
        download_and_install(downloader_update_url, Update_partner)
    else:
        print("没有找到新版本的信息。")


if __name__ == "__main__":
    Update_Launcher()
