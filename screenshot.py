import cv2
import numpy as np
import mss
import ollama
import base64
import csv
import os
import json
from datetime import datetime
import store
# ==================== 配置变量 ====================

# GLM API配置
GLM_API_KEY = "e0f50530805f4ed0af556c4040d99eb3.DkyxdRgrogMYAWqs"  # 用户需要填写自己的API Key
GLM_MODEL = "glm-4.6v-flash"

# Ollama配置
_custom_ollama_host = None
_custom_ollama_model = None

# 是否使用GLM
_use_glm = False

# 测试模式（启用后保存截图）
_test_mode = False


def set_test_mode(enabled):
    """设置测试模式"""
    global _test_mode
    _test_mode = enabled
    if enabled:
        # 创建photo文件夹
        import sys
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        photo_dir = os.path.join(base_dir, 'data', 'photo')
        os.makedirs(photo_dir, exist_ok=True)


def is_test_mode():
    """获取测试模式状态"""
    return _test_mode


def save_screenshot(img, record_id):
    """保存截图到photo文件夹"""
    if not _test_mode:
        return
    
    import sys
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    photo_dir = os.path.join(base_dir, 'data', 'photo')
    os.makedirs(photo_dir, exist_ok=True)
    
    # 生成文件名: ID_日期_时间.png
    now = datetime.now()
    filename = f"{record_id}_{now.strftime('%Y%m%d')}_{now.strftime('%H%M%S')}.png"
    filepath = os.path.join(photo_dir, filename)
    
    # 保存图片
    cv2.imwrite(filepath, img)
    print(f"[测试模式] 截图已保存: {filename}")


def set_use_glm(use_glm):
    """设置是否使用GLM"""
    global _use_glm
    _use_glm = use_glm


def is_using_glm():
    """获取是否使用GLM"""
    return _use_glm


def set_glm_api_key(api_key):
    """设置GLM API Key"""
    global GLM_API_KEY
    GLM_API_KEY = api_key


def get_glm_api_key():
    """获取GLM API Key"""
    return GLM_API_KEY


def set_ollama_config(host, model):
    """设置Ollama配置"""
    global _custom_ollama_host, _custom_ollama_model
    _custom_ollama_host = host
    _custom_ollama_model = model


def get_ollama_config():
    """获取Ollama配置"""
    return _custom_ollama_host, _custom_ollama_model


# ==================== 截图函数 ====================

def capture_screen():
    """截图函数：检测显示器分辨率并全屏截图，返回OpenCV格式图像"""
    with mss.mss() as sct:
        monitor = sct.monitors[1]      # 1为主显示器，0为全部显示器
        screenshot = sct.grab(monitor)  # 全屏截图
        img = np.array(screenshot)      # 转换为numpy数组
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # BGRA转BGR（OpenCV格式）
        return img


# ==================== 提示词 ====================

def get_prompt():
    """获取提示词和工作类型列表"""
    # 工作类型列表
    work_types = ["开发", "沟通", "生活", "学习", "设计", "管理", "文档", "娱乐", "产品", "会议", "运维", "测试", "数据分析", "其他"]
    
    # 提示词：要求模型返回JSON格式的工作类型和描述
    prompt = f"""你是一个工作活动分类专家。请分析当前屏幕截图，判断正在进行的工作类型，并返回JSON格式结果。

可选的工作类型（必须从以下列表中选择一个，不能选择其他）：
{', '.join(work_types)}

分析规则：

1. 开发类：
- 屏幕显示代码编辑器（VS Code、PyCharm、IntelliJ、Sublime、Notepad++等）
- 屏幕显示IDE界面（Eclipse、Xcode、Android Studio等）
- 屏幕显示终端/命令行（CMD、PowerShell、Terminal、iTerm2等）
- 屏幕显示编程相关网站（GitHub、GitLab、Stack Overflow、官方文档、API文档等）
- 屏幕显示调试工具、性能分析工具、数据库管理工具
- 屏幕显示代码仓库、版本控制界面、CI/CD界面

2. 沟通类：
- 屏幕显示聊天工具（微信、飞书、钉钉、Slack、Telegram、QQ、企业微信等）正在处理工作沟通
- 屏幕显示邮件客户端（Outlook、Foxmail等）处理工作邮件
- 屏幕显示工作群聊、项目讨论、任务分配等沟通内容

3. 设计类：
- 屏幕显示设计工具（Figma、Sketch、Adobe XD、Photoshop、Illustrator、InDesign等）
- 屏幕显示UI/UX设计界面、原型设计工具
- 屏幕显示图形编辑、图片处理、视频剪辑软件
- 屏幕显示设计稿、界面设计、图标设计等

4. 管理类：
- 屏幕显示项目管理工具（Jira、Trello、Asana、禅道、飞书项目等）
- 屏幕显示表格软件（Excel、Google Sheets、WPS表格等）处理数据、报表、统计
- 屏幕显示日程安排、任务看板
- 屏幕显示OA系统、审批流程、工作汇报

5. 文档类：
- 屏幕显示Word、WPS文字、Google Docs等文档编辑
- 屏幕显示PPT、Keynote、演示文稿制作
- 屏幕显示PDF阅读器、文档查看
- 屏幕显示笔记软件（Notion、Obsidian、OneNote等）记录工作内容

6. 学习类：
- 屏幕显示在线课程平台（Coursera、Udemy、B站学习区、慕课网等）
- 屏幕显示技术教程、编程学习网站
- 屏幕显示文档学习、技术文章、博客阅读
- 屏幕显示电子书阅读器、学习资料

7. 生活类：
- 屏幕显示私人聊天（与朋友、家人的非工作沟通）
- 屏幕显示购物网站（淘宝、京东、拼多多等）
- 屏幕显示生活服务（外卖、打车、银行、支付宝等）
- 屏幕显示社交媒体（朋友圈、微博、抖音等非娱乐内容）

8. 娱乐类：
- 屏幕显示视频播放器观看电影、电视剧、动漫、综艺节目
- 屏幕显示游戏界面、游戏平台（Steam、Epic、PS、Xbox等）
- 屏幕显示直播平台观看娱乐直播
- 屏幕显示音乐播放器、音乐平台
- 屏幕显示短视频平台（抖音、快手、B站娱乐区等）

9. 产品类：
- 屏幕显示产品需求文档（PRD）、产品原型工具（Axure、墨刀等）
- 屏幕显示产品规划、路线图、用户故事
- 屏幕显示竞品分析、市场调研文档
- 屏幕显示用户反馈、数据分析报告
- 屏幕显示产品设计评审、需求评审界面

10. 会议类：
- 屏幕显示视频会议软件（Zoom、腾讯会议、飞书会议、Teams等）正在进行会议
- 屏幕显示会议纪要、会议记录文档
- 屏幕显示日历中的会议安排、会议邀请
- 屏幕显示在线白板、协作工具（Miro、飞书白板等）

11. 运维类：
- 屏幕显示服务器管理工具（SSH终端、宝塔、cPanel等）
- 屏幕显示云服务平台（阿里云、腾讯云、AWS等）
- 屏幕显示监控系统（Grafana、Prometheus、Zabbix等）
- 屏幕显示容器管理（Docker、Kubernetes）
- 屏幕显示日志分析、告警系统
- 屏幕显示网络配置、域名管理

12. 测试类：
- 屏幕显示测试工具（Postman、JMeter、Selenium等）
- 屏幕显示测试用例管理、测试报告
- 屏幕显示Bug跟踪系统（Jira、禅道等）
- 屏幕显示自动化测试脚本、测试框架
- 屏幕显示性能测试、压力测试界面

13. 数据分析类：
- 屏幕显示数据分析工具（Python/R数据分析、Jupyter Notebook等）
- 屏幕显示BI工具（Tableau、Power BI、FineBI等）
- 屏幕显示SQL查询界面、数据库管理工具
- 屏幕显示数据可视化图表、仪表盘
- 屏幕显示Excel数据透视表、数据处理
- 屏幕显示数据报表、统计分析文档

14. 其他类：
- 无法明确判断的情况
- 系统设置、文件管理器、计算器等工具
- 浏览器空白页、搜索引擎首页

description撰写规则：
核心目标：
1. 尽可能记录有日报价值的工作内容。
2. 保留工作主题、任务名称、项目方向、需求内容、技术问题、交付物、进展、待办。
3. 保护隐私：不记录私人聊天细节，不记录联系人身份，不记录账号、密钥、完整链接等敏感信息。
4. 不要因为隐私保护而把所有内容都写成空泛描述。只需要脱敏"身份信息"和"敏感字段"，工作任务本身要尽量保留。

应该记录什么：
1. 当前正在做的具体工作任务。
2. 当前正在阅读、编辑、核对、调试、整理、沟通的内容主题。
3. 当前任务属于哪个工作方向。
4. 能用于日报的具体进展。
5. 如果是在聊天工具里处理工作，要提取"工作事项"和"任务含义"，但不要复述聊天原文。

不应该记录什么：
1. 不要描述桌面壁纸、系统状态栏、时间、电量、天气、Dock、任务栏等无关信息。
2. 不要输出联系人昵称、群名、备注名、头像文字、账号名。
3. 不要逐字复述聊天消息。
4. 不要输出私人聊天细节。
5. 不要输出手机号、邮箱、身份证、银行卡、地址、验证码、密码、Token、API Key、Cookie。

聊天界面处理：
如果截图中出现微信、飞书、钉钉、Slack、Telegram、邮件、私信、群聊等沟通界面：
允许输出：沟通的工作主题、任务方向、可识别出的工作需求/待办/结论/进展、文件或链接的大致用途。
以及娱乐和生活等与工作无关的也要重点输出，详细介绍做了什么事情或者玩了什么好玩的。
禁止输出：联系人是谁、群名是什么、对方原话、聊天消息逐字内容、完整链接/账号/手机号/邮箱/订单号/密钥等。

示例：
- 聊天内容："做一个 ios 的原生 app 原型" -> "正在整理或沟通 iOS 原生 App 原型设计相关任务。"
- 聊天内容："做海龟策略回测" -> "正在处理量化交易策略回测相关任务。"
- 聊天内容："@某人: 某某仓库/web-design" -> "正在通过沟通工具同步一个 Web 设计或前端页面相关的代码/设计任务。"
- 私人闲聊、家庭、朋友、情感、生活琐事 -> "当前包含私人沟通内容，具体内容已脱敏，不纳入日报。"

必须脱敏的内容：
1. 具体人员身份。
2. 具体群名、客户名、公司内部名称。
3. 完整链接、账号、仓库完整路径。
4. 密钥、Token、验证码、密码。
5. 私人聊天原文。
6. 敏感业务数据明细。

输出格式要求：
请严格按照以下JSON格式输出，不要输出其他内容：
{{"type": "工作类型", "description": "根据以上规则撰写的日报内容描述"}}

注意：
- type必须是上述列表中的一个
- description用中文描述，根据以上规则撰写
- 不要输出敏感信息（账号、密码、链接等）
- 只输出JSON，不要有其他文字"""
    
    return prompt, work_types


# ==================== GLM识别函数 ====================

def glm_recognize():
    """调用GLM API识别截图内容，返回工作类型和描述"""
    import tempfile
    from zhipuai import ZhipuAI as ZhipuAiClient
    
    # 截图
    img = capture_screen()
    
    # 压缩图像，减少API传输大小（限制最大宽度为1024）
    max_width = 99999
    if img.shape[1] > max_width:
        ratio = max_width / img.shape[1]
        img = cv2.resize(img, (max_width, int(img.shape[0] * ratio)))
    
    # 保存图片到临时文件，然后读取（确保格式正确）
    temp_path = os.path.join(tempfile.gettempdir(), 'screen_capture.png')
    #cv2.imshow("c",img)
    #cv2.waitKey(0)
    cv2.imwrite(temp_path, img)
    
    # 读取临时文件并转换为base64
    with open(temp_path, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode("utf-8")
    
    # 删除临时文件
    os.remove(temp_path)
    
    # 获取提示词和工作类型
    prompt, work_types = get_prompt()
    
    # 创建GLM客户端
    client = ZhipuAiClient(api_key=GLM_API_KEY)
    
    # 调用GLM API进行图像识别
    response = client.chat.completions.create(
        model=GLM_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": img_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        thinking={
            "type": "enabled"
        }
    )
    
    # 解析返回结果
    result_text = response.choices[0].message.content
    #print(f"[GLM原始返回] {result_text}")
    
    # 提取JSON结果（处理markdown代码块格式）
    try:
        # 如果返回内容包含markdown代码块，提取其中的JSON
        import re
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析（可能没有代码块标记）
            json_str = result_text.strip()
        
        result = json.loads(json_str)
        work_type = result.get('type', '其他')
        description = result.get('description', '')
        
        # 验证工作类型是否有效
        if work_type not in work_types:
            work_type = '其他'
        
        return {
            'type': work_type,
            'description': description
        }
    except json.JSONDecodeError as e:
        print(f"[GLM解析失败] {e}")
        return {
            'type': '其他',
            'description': '无法识别工作内容'
        }


# ==================== Ollama识别函数 ====================

def ollama_recognize():
    """调用ollama识别截图内容，返回工作类型和描述"""
    # 截图
    img = capture_screen()
    
    # 压缩图像，减少显存占用（限制最大宽度为1024）
    max_width = 99999
    if img.shape[1] > max_width:
        ratio = max_width / img.shape[1]
        img = cv2.resize(img, (max_width, int(img.shape[0] * ratio)))
    # 转换为base64编码（ollama需要base64格式的图像）
    _, buffer = cv2.imencode('.png', img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    # 获取提示词和工作类型
    prompt, work_types = get_prompt()
    
    # 创建ollama客户端，指定远程IP地址
    client = ollama.Client(host=_custom_ollama_host or 'http://192.168.31.23:11434')
    
    # 调用ollama进行图像识别
    response = client.chat(
        model=_custom_ollama_model or 'minicpm-v4.6',
        messages=[{
            'role': 'user',
            'content': prompt,
            'images': [img_base64]
        }],
        think=True,
        keep_alive='1h'
    )
    
    # 解析返回结果
    result_text = response['message']['content']
    
    # 提取JSON结果
    try:
        result = json.loads(result_text)
        work_type = result.get('type', '其他')
        description = result.get('description', '')
        
        # 验证工作类型是否有效
        if work_type not in work_types:
            work_type = '其他'
        
        return {
            'type': work_type,
            'description': description
        }
    except json.JSONDecodeError:
        return {
            'type': '其他',
            'description': '无法识别工作内容'
        }


# ==================== 统一识别接口 ====================

def recognize():
    """统一识别接口，根据配置选择使用GLM或Ollama"""
    if _use_glm:
        return glm_recognize()
    else:
        return ollama_recognize()


# ==================== 测试连接 ====================

def test_glm_connection():
    """测试GLM连接"""
    try:
        from zhipuai import ZhipuAI as ZhipuAiClient
        client = ZhipuAiClient(api_key=GLM_API_KEY)
        response = client.chat.completions.create(
            model=GLM_MODEL,
            messages=[{"role": "user", "content": "你好"}]
        )
        return True, "GLM连接成功"
    except Exception as e:
        return False, f"GLM连接失败: {str(e)}"


def test_ollama_connection():
    """测试Ollama连接"""
    try:
        host = _custom_ollama_host or 'http://192.168.31.23:11434'
        model = _custom_ollama_model or 'minicpm-v4.6'
        client = ollama.Client(host=host)
        response = client.chat(
            model=model,
            messages=[{"role": "user", "content": "你好"}]
        )
        return True, "Ollama连接成功"
    except Exception as e:
        return False, f"Ollama连接失败: {str(e)}"


# ==================== 存储函数 ====================

def run_and_store():
    """
    运行截图识别并存储结果到CSV
    
    功能：
    1. 调用recognize()进行截图识别
    2. 计算与上一条记录的时间间隔（即上一条记录的持续时长）
    3. 将新记录添加到records.csv
    4. 更新daily_summary.csv中的汇总数据
    
    参数：无
    返回值：字典，包含识别结果 {'type': '工作类型', 'description': '工作描述'}
    """
    from store import init_db, read_summary, read_records, write_summary, write_records, get_next_id, WORK_TYPES
    
    # 初始化数据库（确保文件夹和CSV文件存在）
    init_db()
    
    # 获取当前系统时间
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')      # 格式：2025-01-15
    current_time = now.strftime('%H:%M:%S')  # 格式：09:30:00
    
    # 调用截图识别函数，获取工作类型和描述
    result = recognize()
    work_type = result['type']          # 工作类型，如"开发"、"沟通"
    description = result['description'] # 工作描述，如"正在编写Python代码"
    
    # 读取现有数据
    summaries = read_summary()  # 所有日期的汇总数据
    records = read_records()    # 所有记录
    
    # 计算上一条记录的持续时长
    duration_minutes = 0  # 默认为0分钟
    # 筛选出今天的记录
    today_records = [r for r in records if r['日期'] == today]
    
    if today_records:
        # 获取今天最后一条记录
        last_record = today_records[-1]
        # 解析上一条记录的时间
        last_time = datetime.strptime(f"{today} {last_record['时间']}", '%Y-%m-%d %H:%M:%S')
        # 解析当前时间
        current_dt = datetime.strptime(f"{today} {current_time}", '%Y-%m-%d %H:%M:%S')
        # 计算时间差（转换为分钟）
        duration_minutes = (current_dt - last_time).total_seconds() / 60
        
        # 更新上一条记录的持续时长
        last_record['持续时长(分钟)'] = f'{duration_minutes:.1f}'
    
    # 创建新记录
    new_id = get_next_id(records)  # 获取新ID
    new_record = {
        'ID': str(new_id),
        '日期': today,
        '时间': current_time,
        '工作类型': work_type,
        '工作描述': description,
        '持续时长(分钟)': '0'  # 新记录的时长初始为0，下次记录时更新
    }
    records.append(new_record)  # 添加到记录列表
    
    # 测试模式：保存截图
    if _test_mode:
        img = capture_screen()
        save_screenshot(img, new_id)
    
    # 更新每日汇总数据
    if today in summaries:
        # 今天已有记录，更新汇总
        summary = summaries[today]
        summary['记录条数'] = str(int(summary['记录条数']) + 1)  # 记录数+1
        summary['最晚使用时间'] = current_time  # 更新最晚使用时间
        # 更新总使用时长（加上本次时长，转换为小时）
        summary['使用时长(小时)'] = f"{float(summary.get('使用时长(小时)', '0')) + duration_minutes / 60:.2f}"
        # 更新对应工作类型的时长（使用get方法避免KeyError）
        summary[f'{work_type}时长(小时)'] = f"{float(summary.get(f'{work_type}时长(小时)', '0')) + duration_minutes / 60:.2f}"
        
        # 更新主要工作：取时长最长的工作类型
        type_durations = {t: float(summary.get(f'{t}时长(小时)', '0')) for t in WORK_TYPES}
        summary['主要工作'] = max(type_durations, key=type_durations.get)
        
        # 更新当前小时的记录条数
        current_hour = now.strftime('%H')  # 获取当前小时（00-23）
        hour_key = f'{current_hour}:00记录数'
        summary[hour_key] = str(int(summary.get(hour_key, '0')) + 1)
    else:
        # 今天第一条记录，创建新的汇总
        summary = {
            '日期': today,
            '记录条数': '1',
            '使用时长(小时)': '0',  # 第一条记录时长为0
            '主要工作': work_type,
            '最早使用时间': current_time,
            '最晚使用时间': current_time
        }
        # 初始化所有工作类型的时长为0
        for t in WORK_TYPES:
            summary[f'{t}时长(小时)'] = '0'
        # 初始化每个小时的记录数为0
        for h in range(24):
            summary[f'{h:02d}:00记录数'] = '0'
        # 设置当前小时的记录数为1
        current_hour = now.strftime('%H')
        summary[f'{current_hour}:00记录数'] = '1'
        summaries[today] = summary
    
    # 将更新后的数据写入CSV文件
    write_summary(summaries)
    write_records(records)
    
    # 打印记录信息
    print(f"已记录: [{work_type}] {description}")
    
    return result


def run_and_store_with_interval(interval_minutes):
    """
    定时监控模式的截图识别并存储结果
    
    与 run_and_store() 的区别：
    - 本函数用于定时监控模式
    - 每条记录的持续时长固定为监控间隔时长，而不是距离上次记录的实际时间间隔
    - 确保每次监控记录的时长统计准确
    
    参数：
        interval_minutes: 监控间隔时长（分钟），如 5、10、15 等
    
    返回值：字典，包含识别结果 {'type': '工作类型', 'description': '工作描述'}
    """
    from store import init_db, read_summary, read_records, write_summary, write_records, get_next_id, WORK_TYPES
    
    # 初始化数据库（确保文件夹和CSV文件存在）
    init_db()
    
    # 获取当前系统时间
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')      # 格式：2025-01-15
    current_time = now.strftime('%H:%M:%S')  # 格式：09:30:00
    
    # 调用截图识别函数，获取工作类型和描述
    result = recognize()
    work_type = result['type']          # 工作类型，如"开发"、"沟通"
    description = result['description'] # 工作描述，如"正在编写Python代码"
    
    # 读取现有数据
    summaries = read_summary()  # 所有日期的汇总数据
    records = read_records()    # 所有记录
    
    # 使用固定的监控间隔时长作为本次记录的持续时长
    duration_minutes = interval_minutes
    
    # 创建新记录
    new_id = get_next_id(records)  # 获取新ID
    new_record = {
        'ID': str(new_id),
        '日期': today,
        '时间': current_time,
        '工作类型': work_type,
        '工作描述': description,
        '持续时长(分钟)': f'{duration_minutes:.1f}'  # 固定为监控间隔时长
    }
    records.append(new_record)  # 添加到记录列表
    
    # 测试模式：保存截图
    if _test_mode:
        img = capture_screen()
        save_screenshot(img, new_id)
    
    # 更新每日汇总数据
    if today in summaries:
        # 今天已有记录，更新汇总
        summary = summaries[today]
        summary['记录条数'] = str(int(summary['记录条数']) + 1)  # 记录数+1
        summary['最晚使用时间'] = current_time  # 更新最晚使用时间
        # 更新总使用时长（加上本次时长，转换为小时）
        summary['使用时长(小时)'] = f"{float(summary.get('使用时长(小时)', '0')) + duration_minutes / 60:.2f}"
        # 更新对应工作类型的时长（使用get方法避免KeyError）
        summary[f'{work_type}时长(小时)'] = f"{float(summary.get(f'{work_type}时长(小时)', '0')) + duration_minutes / 60:.2f}"
        
        # 更新主要工作：取时长最长的工作类型
        type_durations = {t: float(summary.get(f'{t}时长(小时)', '0')) for t in WORK_TYPES}
        summary['主要工作'] = max(type_durations, key=type_durations.get)
        
        # 更新当前小时的记录条数
        current_hour = now.strftime('%H')  # 获取当前小时（00-23）
        hour_key = f'{current_hour}:00记录数'
        summary[hour_key] = str(int(summary.get(hour_key, '0')) + 1)
    else:
        # 今天第一条记录，创建新的汇总
        summary = {
            '日期': today,
            '记录条数': '1',
            '使用时长(小时)': f'{duration_minutes / 60:.2f}',  # 第一条记录使用监控间隔时长
            '主要工作': work_type,
            '最早使用时间': current_time,
            '最晚使用时间': current_time
        }
        # 初始化所有工作类型的时长为0
        for t in WORK_TYPES:
            summary[f'{t}时长(小时)'] = '0'
        # 设置当前工作类型的时长
        summary[f'{work_type}时长(小时)'] = f'{duration_minutes / 60:.2f}'
        # 初始化每个小时的记录数为0
        for h in range(24):
            summary[f'{h:02d}:00记录数'] = '0'
        # 设置当前小时的记录数为1
        current_hour = now.strftime('%H')
        summary[f'{current_hour}:00记录数'] = '1'
        summaries[today] = summary
    
    # 将更新后的数据写入CSV文件
    write_summary(summaries)
    write_records(records)
    
    # 打印记录信息
    print(f"[定时监控] 已记录: [{work_type}] {description} (间隔: {interval_minutes}分钟)")
    
    return result


# ==================== 统计函数 ====================

def get_today_stats():
    """
    获取今日工作统计信息
    
    返回值：字典，包含以下信息
    - record_count: 今日记录条数
    - duration_hours: 今日使用时长（小时）
    - main_work: 最长时间的工作类型
    - hour_data: 每小时记录数列表（长度24）
    - first_time: 最早使用时间
    - last_time: 最晚使用时间
    - time_range: 使用时间段描述
    """
    from store import read_summary, WORK_TYPES
    
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    
    summaries = read_summary()
    summary = summaries.get(today, None)
    
    if summary:
        record_count = int(summary.get('记录条数', '0'))
        duration_hours = float(summary.get('使用时长(小时)', '0'))
        main_work = summary.get('主要工作', '暂无')
        first_time = summary.get('最早使用时间', '--:--')
        last_time = summary.get('最晚使用时间', '--:--')
        
        # 获取每小时记录数
        hour_data = []
        for h in range(24):
            count = int(summary.get(f'{h:02d}:00记录数', '0') or '0')
            hour_data.append(count)
        
        # 生成时间段描述
        if first_time != '--:--' and last_time != '--:--':
            time_range = f"从{first_time[:5]}到{last_time[:5]}持续保持状态"
        else:
            time_range = "暂无记录"
        
        return {
            'record_count': record_count,
            'duration_hours': duration_hours,
            'main_work': main_work,
            'hour_data': hour_data,
            'first_time': first_time,
            'last_time': last_time,
            'time_range': time_range
        }
    else:
        return {
            'record_count': 0,
            'duration_hours': 0,
            'main_work': '暂无',
            'hour_data': [0] * 24,
            'first_time': '--:--',
            'last_time': '--:--',
            'time_range': '暂无记录'
        }


def get_monitor_info():
    """
    获取显示器信息
    
    返回值：列表，每个元素包含显示器信息
    - name: 显示器名称
    - resolution: 分辨率
    - scale: 缩放率
    - refresh_rate: 帧率
    """
    import mss
    
    monitors = []
    with mss.mss() as sct:
        for i, monitor in enumerate(sct.monitors):
            if i == 0:  # 跳过虚拟显示器（所有显示器的边界框）
                continue
            width = monitor['width']
            height = monitor['height']
            monitors.append({
                'name': f'显示器 {i}',
                'resolution': f'{width} x {height}',
                'scale': '100%',  # mss无法直接获取缩放率
                'refresh_rate': '60 Hz'  # mss无法直接获取帧率
            })
    
    # 尝试使用Windows API获取更详细的信息
    try:
        import ctypes
        user32 = ctypes.windll.user32
        # 获取显示器数量
        monitor_count = user32.GetSystemMetrics(80)  # SM_CMONITORS
        if monitor_count > 0 and len(monitors) == 0:
            # 如果mss没有获取到，使用系统信息
            for i in range(monitor_count):
                monitors.append({
                    'name': f'显示器 {i + 1}',
                    'resolution': '未知',
                    'scale': '未知',
                    'refresh_rate': '未知'
                })
    except:
        pass
    
    return monitors if monitors else [{'name': '主显示器', 'resolution': '未知', 'scale': '未知', 'refresh_rate': '未知'}]


# ==================== 定时监控 ====================

# 全局变量：监控定时器引用（防止被垃圾回收）
_monitor_timer = None
_monitor_workers = []


def start_monitor(interval_minutes, ollama_host=None, callback=None):
    """
    启动定时监控（多线程版本）
    
    功能：
    1. 按照指定间隔定时执行截图分析
    2. 点击开始后，等待第一个间隔结束后才开始第一次截图
    3. 每次截图记录的时长固定为监控间隔时长
    4. 支持自定义 ollama 服务器地址
    5. 使用多线程执行，不阻塞UI
    
    参数：
        interval_minutes: 监控间隔时长（分钟）
        ollama_host: ollama 服务器地址，默认使用 ollama_recognize 中的配置
        callback: 回调函数，每次截图分析完成后调用，参数为识别结果字典
    
    返回值：无
    """
    global _monitor_timer, _monitor_workers
    from PyQt5.QtCore import QTimer, QThread, pyqtSignal
    
    # 初始化工作线程列表（保持引用防止被垃圾回收）
    if '_monitor_workers' not in globals():
        _monitor_workers = []
    
    # 如果设置了自定义 ollama 地址，更新全局配置
    if ollama_host:
        set_ollama_config(ollama_host, _custom_ollama_model)
    
    # 将分钟转换为毫秒
    interval_ms = interval_minutes * 60 * 1000
    
    # 定义工作线程类
    class MonitorWorker(QThread):
        """监控工作线程"""
        finished = pyqtSignal(dict)
        error = pyqtSignal(str)
        
        def __init__(self, interval):
            super().__init__()
            self.interval = interval
        
        def run(self):
            try:
                result = run_and_store_with_interval(self.interval)
                self.finished.emit(result)
            except Exception as e:
                self.error.emit(str(e))
    
    # 定义定时执行的任务
    def monitor_task():
        """定时监控任务 - 在后台线程执行"""
        # 清理已完成的线程
        _monitor_workers[:] = [w for w in _monitor_workers if w.isRunning()]
        
        # 创建并启动工作线程
        worker = MonitorWorker(interval_minutes)
        
        # 连接信号
        worker.finished.connect(lambda result: callback(result, None) if callback else None)
        worker.error.connect(lambda err: callback(None, err) if callback else None)
        
        # 保持引用防止被垃圾回收
        _monitor_workers.append(worker)
        
        # 启动线程
        worker.start()
    
    # 创建定时器
    _monitor_timer = QTimer()
    _monitor_timer.timeout.connect(monitor_task)
    _monitor_timer.start(interval_ms)  # 启动定时器，第一个间隔后才开始第一次截图
    
    print(f"[定时监控] 已启动，间隔 {interval_minutes} 分钟")


def stop_monitor():
    """
    停止定时监控
    
    功能：停止正在运行的定时监控
    
    参数：无
    返回值：无
    """
    global _monitor_timer, _monitor_workers
    
    if _monitor_timer is not None:
        _monitor_timer.stop()
        _monitor_timer = None
        print("[定时监控] 已停止")
    else:
        print("[定时监控] 未在运行")


# ==================== 测试函数 ====================

if __name__ == '__main__':
    print("运行截图识别...")
    result = run_and_store()
    print(f"工作类型: {result['type']}")
    print(f"工作描述: {result['description']}")
    
    print("\n今日统计:")
    stats = get_today_stats()
    print(f"  记录条数: {stats['record_count']}")
    print(f"  使用时长: {stats['duration_hours']:.2f} 小时")
    print(f"  主要工作: {stats['main_work']}")
    print(f"  时间段: {stats['time_range']}")
    
    print("\n显示器信息:")
    monitors = get_monitor_info()
    for m in monitors:
        print(f"  {m['name']}: {m['resolution']}, {m['scale']}, {m['refresh_rate']}")
