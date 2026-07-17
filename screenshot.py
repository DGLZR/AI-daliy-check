import cv2
import numpy as np
import mss
import ollama
import base64
import csv
import os
from datetime import datetime
import store 


def capture_screen():
    """截图函数：检测显示器分辨率并全屏截图，返回OpenCV格式图像"""
    with mss.mss() as sct:
        monitor = sct.monitors[1]      # 1为主显示器，0为全部显示器
        screenshot = sct.grab(monitor)  # 全屏截图
        img = np.array(screenshot)      # 转换为numpy数组
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # BGRA转BGR（OpenCV格式）
        return img






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
    
    # 工作类型列表
    work_types = ["开发", "沟通", "生活", "学习", "设计", "管理", "文档", "娱乐", "其他"]
    
    # 提示词：要求模型返回JSON格式的工作类型和描述
    prompt = f"""你是一个工作活动分类专家。请分析当前屏幕截图，判断正在进行的工作类型，并返回JSON格式结果。

可选的工作类型（必须从以下列表中选择一个）：
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
- 屏幕显示视频会议工具（Zoom、腾讯会议、Teams等）
- 屏幕显示工作群聊、项目讨论、任务分配等沟通内容

3. 设计类：
- 屏幕显示设计工具（Figma、Sketch、Adobe XD、Photoshop、Illustrator、InDesign等）
- 屏幕显示UI/UX设计界面、原型设计工具
- 屏幕显示图形编辑、图片处理、视频剪辑软件
- 屏幕显示设计稿、界面设计、图标设计等

4. 管理类：
- 屏幕显示项目管理工具（Jira、Trello、Asana、禅道、飞书项目等）
- 屏幕显示表格软件（Excel、Google Sheets、WPS表格等）处理数据、报表、统计
- 屏幕显示日程安排、会议管理、任务看板
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

9. 其他类：
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
    
    # 创建ollama客户端，指定远程IP地址
    client = ollama.Client(host='http://192.168.31.23:11434')  # 修改为实际的ollama服务器IP
    
    # 调用ollama进行图像识别
    response = client.chat(
        model='minicpm-v4.6',  # 模型名称（根据本地安装的模型修改）
        messages=[{
            'role': 'user',
            'content': prompt,
            'images': [img_base64]  # 传入base64编码的图像
        }],
        think=True
    )
    
    # 解析返回结果
    result_text = response['message']['content']
    
    # 提取JSON结果
    import json
    try:
        # 尝试解析JSON
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
        # 如果JSON解析失败，返回默认值
        return {
            'type': '其他',
            'description': '无法识别工作内容'
        }

def run_and_store():
    """
    运行截图识别并存储结果到CSV
    
    功能：
    1. 调用ollama_recognize()进行截图识别
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
    result = ollama_recognize()
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
    
    # 更新每日汇总数据
    if today in summaries:
        # 今天已有记录，更新汇总
        summary = summaries[today]
        summary['记录条数'] = str(int(summary['记录条数']) + 1)  # 记录数+1
        summary['最晚使用时间'] = current_time  # 更新最晚使用时间
        # 更新总使用时长（加上本次时长，转换为小时）
        summary['使用时长(小时)'] = f"{float(summary['使用时长(小时)']) + duration_minutes / 60:.2f}"
        # 更新对应工作类型的时长
        summary[f'{work_type}时长(小时)'] = f"{float(summary[f'{work_type}时长(小时)']) + duration_minutes / 60:.2f}"
        
        # 更新主要工作：取时长最长的工作类型
        type_durations = {t: float(summary[f'{t}时长(小时)']) for t in WORK_TYPES}
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


# 测试函数
if __name__ == '__main__':
    print("运行截图识别...")
    result = run_and_store()
    print(f"工作类型: {result['type']}")
    print(f"工作描述: {result['description']}") 
    store.print_daily_summary('2026-07-16')
    