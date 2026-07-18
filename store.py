"""
工作日报助手 - 数据存储模块

功能说明：
1. 使用CSV文件存储工作数据，方便直接用Excel查看
2. 记录每日截图分析次数、使用时长、主要工作等汇总信息
3. 记录每一条截图分析的详细数据
4. 支持按日期查询汇总和记录

文件结构：
- data/daily_summary.csv: 每日工作汇总数据
- data/records.csv: 每条截图分析记录
"""

import csv
import os
from datetime import datetime
import time

# ==================== 配置常量 ====================

# 数据库文件夹路径：在当前脚本所在目录下的data文件夹
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# 每日汇总CSV文件路径
SUMMARY_FILE = os.path.join(DB_DIR, 'daily_summary.csv')

# 每条记录CSV文件路径
RECORDS_FILE = os.path.join(DB_DIR, 'records.csv')

# 工作类型列表，与screenshot.py中定义的类型保持一致
WORK_TYPES = ["开发", "沟通", "生活", "学习", "设计", "管理", "文档", "娱乐", "其他"]


# ==================== 初始化函数 ====================

def init_db():
    """
    初始化数据库
    
    功能：
    1. 检查data文件夹是否存在，不存在则创建
    2. 检查daily_summary.csv是否存在，不存在则创建并写入表头
    3. 检查records.csv是否存在，不存在则创建并写入表头
    
    参数：无
    返回值：无
    """
    # 创建data文件夹（如果不存在）
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        print(f"已创建data文件夹: {DB_DIR}")
    
    # 创建每日汇总CSV文件（如果不存在）
    if not os.path.exists(SUMMARY_FILE):
        # 定义汇总表的列名
        headers = ['日期', '记录条数', '使用时长(小时)', '主要工作', '最早使用时间', '最晚使用时间']
        # 为每种工作类型添加时长列
        headers += [f'{t}时长(小时)' for t in WORK_TYPES]
        # 为每个小时添加记录条数列（00:00-23:00）
        headers += [f'{h:02d}:00记录数' for h in range(24)]
        
        # 使用utf-8-sig编码确保Excel打开中文不乱码
        with open(SUMMARY_FILE, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)  # 写入表头
        print(f"已创建汇总文件: {SUMMARY_FILE}")
    
    # 创建记录CSV文件（如果不存在）
    if not os.path.exists(RECORDS_FILE):
        # 定义记录表的列名
        headers = ['ID', '日期', '时间', '工作类型', '工作描述', '持续时长(分钟)']
        
        with open(RECORDS_FILE, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)  # 写入表头
        print(f"已创建记录文件: {RECORDS_FILE}")


# ==================== 读取函数 ====================

def read_summary():
    """
    读取每日汇总数据
    
    功能：从daily_summary.csv读取所有日期的汇总数据
    
    参数：无
    返回值：字典，key为日期字符串，value为该日期的汇总数据字典
           例如：{'2025-01-15': {'日期': '2025-01-15', '记录条数': '5', ...}}
    """
    # 如果文件不存在，返回空字典
    if not os.path.exists(SUMMARY_FILE):
        return {}
    
    summaries = {}
    # 使用DictReader读取，每行会自动转换为字典
    with open(SUMMARY_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 以日期为key存储，方便按日期查找
            summaries[row['日期']] = row
    return summaries


def read_records():
    """
    读取所有记录
    
    功能：从records.csv读取所有截图分析记录
    
    参数：无
    返回值：列表，每个元素是一条记录的字典
           例如：[{'ID': '1', '日期': '2025-01-15', '时间': '09:30:00', ...}]
    """
    # 如果文件不存在，返回空列表
    if not os.path.exists(RECORDS_FILE):
        return []
    
    records = []
    with open(RECORDS_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records


# ==================== 写入函数 ====================

def write_summary(summaries):
    """
    写入每日汇总数据
    
    功能：将汇总数据字典写入daily_summary.csv（覆盖写入）
    
    参数：
        summaries: 字典，key为日期，value为汇总数据字典
    返回值：无
    """
    # 定义表头
    headers = ['日期', '记录条数', '使用时长(小时)', '主要工作', '最早使用时间', '最晚使用时间']
    headers += [f'{t}时长(小时)' for t in WORK_TYPES]
    # 为每个小时添加记录条数列（00:00-23:00）
    headers += [f'{h:02d}:00记录数' for h in range(24)]
    
    # 覆盖写入整个文件
    with open(SUMMARY_FILE, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()  # 写入表头
        # 按日期排序写入，保持文件有序
        for date in sorted(summaries.keys()):
            writer.writerow(summaries[date])


def write_records(records):
    """
    写入记录数据
    
    功能：将记录列表写入records.csv（覆盖写入）
    
    参数：
        records: 列表，每个元素是一条记录的字典
    返回值：无
    """
    # 定义表头
    headers = ['ID', '日期', '时间', '工作类型', '工作描述', '持续时长(分钟)']
    
    # 覆盖写入整个文件
    with open(RECORDS_FILE, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()  # 写入表头
        for record in records:
            writer.writerow(record)


# ==================== 辅助函数 ====================

def get_next_id(records):
    """
    获取下一条记录的ID
    
    功能：计算新记录应该使用的ID号（自增）
    
    参数：
        records: 当前所有记录的列表
    返回值：整数，下一个可用的ID
    """
    # 如果没有记录，从1开始
    if not records:
        return 1
    # 找到现有最大ID，加1
    return max(int(r['ID']) for r in records) + 1


# ==================== 查询函数 ====================

def get_daily_summary(date=None):
    """
    获取某天的汇总数据
    
    功能：查询指定日期的工作汇总信息
    
    参数：
        date: 日期字符串，格式为'YYYY-MM-DD'，默认为今天
    返回值：
        如果该日期有数据，返回字典包含汇总信息
        如果该日期无数据，返回None
    """
    # 默认查询今天
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # 读取所有汇总数据
    summaries = read_summary()
    # 返回指定日期的数据，不存在则返回None
    return summaries.get(date, None)


def get_daily_records(date=None):
    """
    获取某天的所有记录
    
    功能：查询指定日期的所有截图分析记录
    
    参数：
        date: 日期字符串，格式为'YYYY-MM-DD'，默认为今天
    返回值：
        列表，包含该日期的所有记录字典
    """
    # 默认查询今天
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # 读取所有记录
    records = read_records()
    # 筛选出指定日期的记录
    return [r for r in records if r['日期'] == date]


def print_today_summary():
    """
    打印今日工作汇总
    
    功能：在控制台打印今日的工作汇总和记录详情，便于快速查看
    
    参数：无
    返回值：无（直接打印到控制台）
    """
    # 打印汇总标题
    print("\n" + "="*50)
    print("今日工作汇总")
    print("="*50)
    
    # 获取今日汇总数据
    summary = get_daily_summary()
    if summary:
        # 打印各项汇总信息
        print(f"日期: {summary['日期']}")
        print(f"截图分析次数: {summary['记录条数']}")
        print(f"使用时长: {summary['使用时长(小时)']} 小时")
        print(f"主要工作: {summary['主要工作']}")
        print(f"最早使用: {summary['最早使用时间']}")
        print(f"最晚使用: {summary['最晚使用时间']}")
        
        # 打印各工作类型的时长（只显示有记录的类型）
        print("\n各类工作时长:")
        for t in WORK_TYPES:
            hours = float(summary[f'{t}时长(小时)'])
            if hours > 0:  # 只显示时长大于0的类型
                print(f"  {t}: {hours:.2f} 小时")
        
        # 打印每小时记录数（只显示有记录的小时）
        print("\n每小时记录数:")
        for h in range(24):
            count = int(summary.get(f'{h:02d}:00记录数', '0'))
            if count > 0:  # 只显示记录数大于0的小时
                print(f"  {h:02d}:00 - {count} 条")
    else:
        print("今日暂无记录")
    
    # 打印记录详情标题
    print("\n" + "-"*50)
    print("今日记录详情")
    print("-"*50)
    
    # 获取今日所有记录
    records = get_daily_records()
    if records:
        # 打印每条记录的时间、类型和描述
        for r in records:
            print(f"[{r['时间']}] {r['工作类型']}: {r['工作描述']}")
    else:
        print("暂无记录")
    
    print("="*50)


def print_daily_summary(date=None):
    """
    打印指定日期的工作汇总
    
    功能：在控制台打印指定日期的工作汇总和记录详情，便于查看历史数据
    
    参数：
        date: 日期字符串，格式为'YYYY-MM-DD'，默认为今天
              例如：'2025-01-15' 表示2025年1月15日
    返回值：无（直接打印到控制台）
    
    使用示例：
        print_daily_summary()           # 打印今天的汇总
        print_daily_summary('2025-01-15')  # 打印2025年1月15日的汇总
    """
    # 默认查询今天
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # 打印汇总标题
    print("\n" + "="*50)
    print(f"{date} 工作汇总")
    print("="*50)
    
    # 获取指定日期的汇总数据
    summary = get_daily_summary(date)
    if summary:
        # 打印各项汇总信息
        print(f"日期: {summary['日期']}")
        print(f"截图分析次数: {summary['记录条数']}")
        print(f"使用时长: {summary['使用时长(小时)']} 小时")
        print(f"主要工作: {summary['主要工作']}")
        print(f"最早使用: {summary['最早使用时间']}")
        print(f"最晚使用: {summary['最晚使用时间']}")
        
        # 打印各工作类型的时长（只显示有记录的类型）
        print("\n各类工作时长:")
        for t in WORK_TYPES:
            hours = float(summary[f'{t}时长(小时)'])
            if hours > 0:  # 只显示时长大于0的类型
                print(f"  {t}: {hours:.2f} 小时")
        
        # 打印每小时记录数（只显示有记录的小时）
        print("\n每小时记录数:")
        for h in range(24):
            # 获取当前小时的记录数，如果为空则默认为'0'
            hour_count = summary.get(f'{h:02d}:00记录数', '0') or '0'
            count = int(hour_count)
            if count > 0:  # 只显示记录数大于0的小时
                print(f"  {h:02d}:00 - {count} 条")
    else:
        print(f"{date} 暂无记录")
    
    # 打印记录详情标题
    print("\n" + "-"*50)
    print(f"{date} 记录详情")
    print("-"*50)
    
    # 获取指定日期的所有记录
    records = get_daily_records(date)
    if records:
        # 打印每条记录的时间、类型和描述
        for r in records:
            print(f"[{r['时间']}] {r['工作类型']}: {r['工作描述']}")
    else:
        print("暂无记录")
    
    print("="*50)


# ==================== 主程序入口 ====================

if __name__ == '__main__':
    from screenshot import run_and_store
    
    time.sleep(1)
    # 初始化数据库
    init_db()
    
    # 测试：运行一次截图识别并存储
    print("运行截图识别...")
    result = run_and_store()
    print(f"识别结果: {result}")
    
    # 打印今日汇总
    print_today_summary()
