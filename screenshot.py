import cv2
import numpy as np
import mss
import ollama
import base64


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
    max_width = 1024
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
1. 如果屏幕显示代码编辑器、IDE、终端、命令行、编程相关网站 -> "开发"
2. 如果屏幕显示聊天工具（微信、飞书、钉钉等）正在处理工作沟通 -> "沟通"
3. 如果屏幕显示私人聊天、购物、游戏、视频等生活娱乐内容 -> "生活" 或 "娱乐"
4. 如果屏幕显示在线课程、教程、文档学习、技术文章 -> "学习"
5. 如果屏幕显示设计工具（Figma、PS、Sketch等）或UI/UX相关内容 -> "设计"
6. 如果屏幕显示项目管理工具、表格、日程安排、会议 -> "管理"
7. 如果屏幕显示Word、Excel、PPT、PDF等文档编辑 -> "文档"
8. 如果无法明确判断 -> "其他"

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
        }]
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

# 测试函数
if __name__ == '__main__':
    result = ollama_recognize()
    print(f"工作类型: {result['type']}")
    print(f"工作描述: {result['description']}") 