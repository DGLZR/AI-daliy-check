"""
工作日报助手 - Fluent Design 主程序

使用 PyQt-Fluent-Widgets 库实现现代化界面
支持响应式布局，随窗口大小自动调整
支持系统DPI缩放检测和手动调整
"""

import sys
import os
import platform
import sys; sys.setrecursionlimit(sys.getrecursionlimit() * 5)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCALE_FACTOR = 1.0


def load_scale_setting():
    try:
        config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'config.txt')
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('scale_factor='):
                        return float(line.strip().split('=')[1])
    except:
        pass
    return None


def get_system_dpi_scale():
    try:
        if platform.system() == 'Windows':
            import ctypes
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
                hdc = ctypes.windll.user32.GetDC(0)
                dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
                ctypes.windll.user32.ReleaseDC(0, hdc)
                scale = dpi / 96.0
                return round(scale * 4) / 4
            except:
                return 1.0
        else:
            return 1.0
    except:
        return 1.0


def main():
    global SCALE_FACTOR
    
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QPoint
    from PyQt5.QtGui import QFont, QColor, QPixmap, QPainter, QPainterPath, QBrush, QPen, QIcon
    
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    system_scale = get_system_dpi_scale()
    saved_scale = load_scale_setting()
    SCALE_FACTOR = saved_scale if saved_scale else system_scale
    
    base_font_size = max(9, int(12 / SCALE_FACTOR))
    app.setFont(QFont("Microsoft YaHei", base_font_size))
    
    from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                                 QLabel, QFrame, QScrollArea, QCheckBox,
                                 QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
                                 QSizePolicy, QPushButton, QTableWidget, QTableWidgetItem,
                                 QLineEdit, QDateEdit, QComboBox, QApplication,
                                 QMessageBox, QSystemTrayIcon, QMenu, QAction, QDialog,
                                 QTextEdit)
    from PyQt5.QtCore import Qt, QSize, QTimer, QDate, QPropertyAnimation, QEasingCurve, QDateTime, QThread, pyqtSignal
    from PyQt5.QtGui import QFont, QColor, QPixmap, QPainter, QPainterPath, QBrush, QPen, QIcon
    from qfluentwidgets import (FluentWindow, NavigationItemPosition, StrongBodyLabel,
                                TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel,
                                PrimaryPushButton, TransparentPushButton, PillPushButton,
                                SimpleCardWidget, HeaderCardWidget, TableWidget,
                                FluentIcon, ComboBox, CalendarPicker, SearchLineEdit,
                                InfoBar, InfoBarPosition, ToolButton, FluentIconBase)
    from store import init_db, get_daily_summary, get_daily_records, read_records
    from screenshot import run_and_store, get_today_stats, get_monitor_info, start_monitor, stop_monitor, set_use_glm, set_ollama_config, test_glm_connection, test_ollama_connection, set_test_mode, is_test_mode
    from datetime import datetime, timedelta

    # ==================== 工具函数 ====================
    
    def create_circle_avatar(image_path, size=60):
        """创建圆形头像"""
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            pixmap = QPixmap(size, size)
            pixmap.fill(QColor("#E3F2FD"))
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QPen(QColor("#1976D2"), 2))
            painter.setBrush(QBrush(QColor("#BBDEFB")))
            painter.drawEllipse(2, 2, size - 4, size - 4)
            painter.setPen(QColor("#1976D2"))
            painter.setFont(QFont("Microsoft YaHei", size // 3))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "👤")
            painter.end()
        
        pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        
        rounded = QPixmap(size, size)
        rounded.fill(Qt.transparent)
        
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#4CAF50"), 3))
        painter.setBrush(QBrush(pixmap))
        painter.drawEllipse(2, 2, size - 4, size - 4)
        painter.end()
        
        return rounded

    # ==================== 自定义组件 ====================
    
    class StatCard(SimpleCardWidget):
        """统计卡片组件 - 紧凑型"""
        def __init__(self, title, value, icon=None, parent=None):
            super().__init__(parent)
            self.setMinimumSize(120, 70)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(10)
            shadow.setXOffset(0)
            shadow.setYOffset(2)
            shadow.setColor(QColor(0, 0, 0, 20))
            self.setGraphicsEffect(shadow)
            
            layout = QHBoxLayout(self)
            layout.setSpacing(8)
            layout.setContentsMargins(10, 8, 10, 8)
            
            if icon:
                iconLabel = QLabel(self)
                iconLabel.setFixedSize(28, 28)
                iconLabel.setAlignment(Qt.AlignCenter)
                iconLabel.setStyleSheet("""
                    background-color: #E3F2FD;
                    border-radius: 14px;
                    font-size: 13px;
                """)
                iconLabel.setText(icon)
                layout.addWidget(iconLabel)
            
            textLayout = QVBoxLayout()
            textLayout.setSpacing(2)
            
            self.titleLabel = BodyLabel(title, self)
            self.titleLabel.setStyleSheet("color: #888888; font-size: 9px;")
            
            self.valueLabel = TitleLabel(value, self)
            self.valueLabel.setStyleSheet("color: #1a1a1a; font-size: 15px; font-weight: bold;")
            
            textLayout.addWidget(self.titleLabel)
            textLayout.addWidget(self.valueLabel)
            layout.addLayout(textLayout)
        
        def updateValue(self, value):
            self.valueLabel.setText(value)

    class SectionTitle(QWidget):
        """章节标题"""
        def __init__(self, title, parent=None):
            super().__init__(parent)
            layout = QHBoxLayout(self)
            layout.setContentsMargins(0, 5, 0, 3)
            
            self.label = StrongBodyLabel(title, self)
            self.label.setStyleSheet("color: #333333; font-size: 11px; font-weight: bold;")
            layout.addWidget(self.label)
            layout.addStretch()

    # ==================== 今日工作页面 ====================
    
    class TodayWorkPage(QWidget):
        """今日工作页面"""
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setObjectName("todayWorkPage")
            self.cards = []  # 存储卡片用于动画
            
            # 主滚动区域
            scrollLayout = QVBoxLayout(self)
            scrollLayout.setContentsMargins(0, 0, 0, 0)
            scrollLayout.setSpacing(0)
            
            scrollArea = QScrollArea()
            scrollArea.setWidgetResizable(True)
            scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scrollArea.setStyleSheet("QScrollArea { border: none; background-color: #F5F5F5; }")
            
            contentWidget = QWidget()
            contentWidget.setStyleSheet("background-color: #F5F5F5; border: none;")
            layout = QVBoxLayout(contentWidget)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)
            
            # ========== 头部信息区域 ==========
            headerCard = QFrame()
            headerCard.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 12px;
                    border: none;
                }
            """)
            self.cards.append(headerCard)
            
            headerLayout = QHBoxLayout(headerCard)
            headerLayout.setContentsMargins(20, 20, 20, 20)
            headerLayout.setSpacing(15)
            
            # 圆形头像
            avatarPath = r"C:\Users\20057\Desktop\frog.jpg"
            avatarPixmap = create_circle_avatar(avatarPath, 60)
            avatarLabel = QLabel()
            avatarLabel.setPixmap(avatarPixmap)
            avatarLabel.setFixedSize(60, 60)
            avatarLabel.setStyleSheet("border: none;")
            headerLayout.addWidget(avatarLabel)
            
            # 右侧文字信息
            infoLayout = QVBoxLayout()
            infoLayout.setSpacing(6)
            
            mainTitle = QLabel("告别加班写周报")
            mainTitle.setStyleSheet("font-size: 20px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            infoLayout.addWidget(mainTitle)
            
            subTitle = QLabel("一周工作内容自动汇总，AI帮你梳理亮点，周五准时下班。")
            subTitle.setStyleSheet("font-size: 12px; color: #888888; border: none; background: transparent;")
            subTitle.setWordWrap(True)
            infoLayout.addWidget(subTitle)
            
            # 标签行
            tagsLayout = QHBoxLayout()
            tagsLayout.setSpacing(10)
            
            tags = [
                ("🔒", "截图分析后即刻销毁"),
                ("💾", "数据仅存本地，不上传云端"),
                ("👤", "你的工作内容只属于你")
            ]
            
            for icon, text in tags:
                tagLabel = QLabel(f"{icon} {text}")
                tagLabel.setStyleSheet("""
                    QLabel {
                        background-color: #E8F5E9;
                        color: #2E7D32;
                        padding: 4px 10px;
                        border-radius: 10px;
                        font-size: 10px;
                        border: none;
                    }
                """)
                tagsLayout.addWidget(tagLabel)
            
            tagsLayout.addStretch()
            infoLayout.addLayout(tagsLayout)
            
            headerLayout.addLayout(infoLayout)
            layout.addWidget(headerCard)
            
            # ========== 工作概览卡片 ==========
            overviewCard = QFrame()
            overviewCard.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 12px;
                    border: none;
                }
            """)
            self.cards.append(overviewCard)
            
            overviewLayout = QVBoxLayout(overviewCard)
            overviewLayout.setContentsMargins(20, 20, 20, 20)
            overviewLayout.setSpacing(12)
            
            # 标题
            overviewTitle = QLabel("工作概览")
            overviewTitle.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            overviewLayout.addWidget(overviewTitle)
            
            # 描述文本
            self.overviewDesc = QLabel("加载中...")
            self.overviewDesc.setStyleSheet("font-size: 12px; color: #666666; line-height: 1.6; border: none; background: transparent;")
            self.overviewDesc.setWordWrap(True)
            overviewLayout.addWidget(self.overviewDesc)
            
            # 分隔线
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFixedHeight(1)
            separator.setStyleSheet("background-color: #E0E0E0; border: none;")
            overviewLayout.addWidget(separator)
            
            # 三个统计项
            statsLayout = QHBoxLayout()
            statsLayout.setSpacing(20)
            
            self.recordCountLabel = QLabel("0")
            self.recordCountLabel.setStyleSheet("font-size: 28px; font-weight: bold; color: #4CAF50; border: none; background: transparent;")
            self.recordCountLabel.setAlignment(Qt.AlignCenter)
            
            self.durationLabel = QLabel("0h")
            self.durationLabel.setStyleSheet("font-size: 28px; font-weight: bold; color: #2196F3; border: none; background: transparent;")
            self.durationLabel.setAlignment(Qt.AlignCenter)
            
            self.mainWorkLabel = QLabel("暂无")
            self.mainWorkLabel.setStyleSheet("font-size: 20px; font-weight: bold; color: #FF9800; border: none; background: transparent;")
            self.mainWorkLabel.setAlignment(Qt.AlignCenter)
            
            # 统计项布局
            for label, sub_text in [(self.recordCountLabel, "记录条数"), 
                                     (self.durationLabel, "专注时长"),
                                     (self.mainWorkLabel, "主要工作")]:
                statWidget = QWidget()
                statWidget.setStyleSheet("border: none; background: transparent;")
                statLayout = QVBoxLayout(statWidget)
                statLayout.setSpacing(4)
                statLayout.addWidget(label, 0, Qt.AlignCenter)
                
                subLabel = QLabel(sub_text)
                subLabel.setStyleSheet("font-size: 11px; color: #999999; border: none; background: transparent;")
                subLabel.setAlignment(Qt.AlignCenter)
                statLayout.addWidget(subLabel, 0, Qt.AlignCenter)
                
                statsLayout.addWidget(statWidget)
            
            overviewLayout.addLayout(statsLayout)
            layout.addWidget(overviewCard)
            
            # ========== 时段记录卡片 ==========
            timeCard = QFrame()
            timeCard.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 12px;
                    border: none;
                }
            """)
            self.cards.append(timeCard)
            
            timeLayout = QVBoxLayout(timeCard)
            timeLayout.setContentsMargins(20, 20, 20, 20)
            timeLayout.setSpacing(12)
            
            # 标题栏
            timeHeaderLayout = QHBoxLayout()
            timeTitle = QLabel("时段记录")
            timeTitle.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            timeHeaderLayout.addWidget(timeTitle)
            timeHeaderLayout.addStretch()
            
            # 图例
            legendLayout = QHBoxLayout()
            legendLayout.setSpacing(5)
            legendLabel = QLabel("少")
            legendLabel.setStyleSheet("font-size: 10px; color: #999999; border: none; background: transparent;")
            legendLayout.addWidget(legendLabel)
            
            for intensity in range(5):
                block = QLabel()
                block.setFixedSize(12, 12)
                block.setStyleSheet(f"background-color: rgba(76, 175, 80, {50 + intensity * 50}); border-radius: 2px; border: none;")
                legendLayout.addWidget(block)
            
            legendLabel2 = QLabel("多")
            legendLabel2.setStyleSheet("font-size: 10px; color: #999999; border: none; background: transparent;")
            legendLayout.addWidget(legendLabel2)
            
            timeHeaderLayout.addLayout(legendLayout)
            timeLayout.addLayout(timeHeaderLayout)
            
            # 热力图容器
            heatContainer = QWidget()
            heatContainer.setStyleSheet("background: transparent; border: none;")
            heatContainerLayout = QVBoxLayout(heatContainer)
            heatContainerLayout.setContentsMargins(0, 0, 0, 0)
            heatContainerLayout.setSpacing(4)
            
            # 热力图格子
            heatGrid = QGridLayout()
            heatGrid.setSpacing(4)
            heatGrid.setContentsMargins(0, 0, 0, 0)
            
            self.hourBlocks = []
            for h in range(24):
                block = QLabel("0")
                block.setMinimumSize(30, 28)
                block.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                block.setAlignment(Qt.AlignCenter)
                block.setStyleSheet("""
                    background-color: #E8F5E9;
                    border-radius: 6px;
                    font-size: 10px;
                    color: #666666;
                    border: none;
                """)
                self.hourBlocks.append(block)
                heatGrid.addWidget(block, 0, h)
            
            heatContainerLayout.addLayout(heatGrid)
            
            # 时间标签（使用相同的网格布局，居中对齐）
            timeLabelsGrid = QGridLayout()
            timeLabelsGrid.setSpacing(4)
            timeLabelsGrid.setContentsMargins(0, 0, 0, 0)
            
            for h in range(24):
                if h % 3 == 0:
                    label = QLabel(f"{h}:00")
                    label.setStyleSheet("font-size: 9px; color: #999999; border: none; background: transparent;")
                    label.setAlignment(Qt.AlignCenter)  # 居中对齐
                    timeLabelsGrid.addWidget(label, 0, h)
                else:
                    # 空占位符
                    spacer = QWidget()
                    spacer.setStyleSheet("background: transparent; border: none;")
                    timeLabelsGrid.addWidget(spacer, 0, h)
            
            heatContainerLayout.addLayout(timeLabelsGrid)
            timeLayout.addWidget(heatContainer)
            layout.addWidget(timeCard)
            
            # ========== 显示器信息卡片 ==========
            monitorCard = QFrame()
            monitorCard.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 12px;
                    border: none;
                }
            """)
            self.cards.append(monitorCard)
            
            monitorLayout = QVBoxLayout(monitorCard)
            monitorLayout.setContentsMargins(20, 20, 20, 20)
            monitorLayout.setSpacing(12)
            
            # 标题栏
            monitorHeaderLayout = QHBoxLayout()
            
            monitorIcon = QLabel("🖥️")
            monitorIcon.setStyleSheet("font-size: 16px; border: none; background: transparent;")
            monitorHeaderLayout.addWidget(monitorIcon)
            
            monitorTitle = QLabel("已连接显示器")
            monitorTitle.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            monitorHeaderLayout.addWidget(monitorTitle)
            monitorHeaderLayout.addStretch()
            
            self.monitorCountLabel = QLabel("0台")
            self.monitorCountLabel.setStyleSheet("font-size: 12px; color: #999999; border: none; background: transparent;")
            monitorHeaderLayout.addWidget(self.monitorCountLabel)
            
            monitorLayout.addLayout(monitorHeaderLayout)
            
            # 显示器列表
            self.monitorListLayout = QVBoxLayout()
            self.monitorListLayout.setSpacing(8)
            monitorLayout.addLayout(self.monitorListLayout)
            
            layout.addWidget(monitorCard)
            
            # 添加弹性空间
            layout.addStretch()
            
            scrollArea.setWidget(contentWidget)
            scrollLayout.addWidget(scrollArea)
            
            # 启动入场动画
            QTimer.singleShot(100, self.playEntryAnimations)
            
            # 加载数据
            self.updateData()
        
        def playEntryAnimations(self):
            """播放卡片入场动画"""
            for i, card in enumerate(self.cards):
                # 设置初始状态：透明且向下偏移
                card.setStyleSheet(card.styleSheet() + "opacity: 0;")
                card.setGraphicsEffect(None)  # 移除旧效果
                
                # 创建淡入动画
                opacityEffect = QGraphicsOpacityEffect(card)
                opacityEffect.setOpacity(0)
                card.setGraphicsEffect(opacityEffect)
                
                anim = QPropertyAnimation(opacityEffect, b"opacity")
                anim.setDuration(400)
                anim.setStartValue(0.0)
                anim.setEndValue(1.0)
                anim.setEasingCurve(QEasingCurve.OutCubic)
                
                # 延迟启动
                QTimer.singleShot(i * 150, anim.start)
                
                # 保存动画引用
                if not hasattr(self, '_animations'):
                    self._animations = []
                self._animations.append(opacityEffect)
                self._animations.append(anim)
        
        def updateData(self):
            """更新页面数据"""
            stats = get_today_stats()
            
            # 更新工作概览
            time_range = stats['time_range']
            record_count = stats['record_count']
            duration = stats['duration_hours']
            
            if record_count > 0:
                # 计算下午时段产出
                hour_data = stats['hour_data']
                afternoon_count = sum(hour_data[12:18])
                overview_text = f"今天工作节奏紧凑，{time_range}，共记录{record_count}段活动，累计专注约{duration:.1f}小时。"
                if afternoon_count > record_count * 0.4:
                    overview_text = f"今天工作节奏紧凑，{time_range}，下午时段产出最多，共记录{record_count}段活动，累计专注约{duration:.1f}小时。"
            else:
                overview_text = "今天暂无工作记录，点击截图分析开始记录你的工作内容。"
            
            self.overviewDesc.setText(overview_text)
            
            # 更新统计数字
            self.recordCountLabel.setText(str(record_count))
            self.durationLabel.setText(f"{duration:.1f}h")
            self.mainWorkLabel.setText(stats['main_work'])
            
            # 更新热力图
            max_count = max(stats['hour_data']) if stats['hour_data'] else 1
            if max_count == 0:
                max_count = 1
            
            for h in range(24):
                count = stats['hour_data'][h]
                intensity = count / max_count if max_count > 0 else 0
                
                if count == 0:
                    # 无记录：浅灰色
                    bg_color = "#F0F0F0"
                    text_color = "#CCCCCC"
                else:
                    # 有记录：从白色渐变到绿色
                    # 白色: rgb(255, 255, 255)
                    # 深绿色: rgb(34, 139, 34)
                    r = int(255 - (255 - 34) * intensity)
                    g = int(255 - (255 - 139) * intensity)
                    b = int(255 - (255 - 34) * intensity)
                    bg_color = f"rgb({r}, {g}, {b})"
                    # 文字颜色：浅色背景用深色字，深色背景用白色字
                    text_color = "#FFFFFF" if intensity > 0.5 else "#333333"
                
                self.hourBlocks[h].setText(str(count))
                self.hourBlocks[h].setStyleSheet(f"""
                    background-color: {bg_color};
                    border-radius: 6px;
                    font-size: 10px;
                    color: {text_color};
                    font-weight: bold;
                    border: none;
                """)
            
            # 更新显示器信息
            monitors = get_monitor_info()
            self.monitorCountLabel.setText(f"{len(monitors)}台")
            
            # 清空旧的显示器列表
            while self.monitorListLayout.count():
                child = self.monitorListLayout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # 添加显示器卡片
            for i, monitor in enumerate(monitors):
                monWidget = QFrame()
                monWidget.setStyleSheet("""
                    QFrame {
                        background-color: #F5F5F5;
                        border-radius: 8px;
                        border: none;
                    }
                """)
                monLayout = QHBoxLayout(monWidget)
                monLayout.setContentsMargins(12, 10, 12, 10)
                monLayout.setSpacing(12)
                
                # 序号
                numLabel = QLabel(str(i + 1))
                numLabel.setFixedSize(28, 28)
                numLabel.setAlignment(Qt.AlignCenter)
                numLabel.setStyleSheet("""
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 14px;
                    font-size: 12px;
                    font-weight: bold;
                    border: none;
                """)
                monLayout.addWidget(numLabel)
                
                # 信息
                infoLayout = QVBoxLayout()
                infoLayout.setSpacing(2)
                
                nameLabel = QLabel(monitor['name'])
                nameLabel.setStyleSheet("font-size: 12px; font-weight: bold; color: #333333; border: none; background: transparent;")
                infoLayout.addWidget(nameLabel)
                
                for text in [monitor['resolution'], monitor['scale'], monitor['refresh_rate']]:
                    label = QLabel(text)
                    label.setStyleSheet("font-size: 10px; color: #888888; border: none; background: transparent;")
                    infoLayout.addWidget(label)
                
                monLayout.addLayout(infoLayout)
                monLayout.addStretch()
                
                self.monitorListLayout.addWidget(monWidget)

    # ==================== 截图识别工作线程 ====================
    
    class ScreenshotWorker(QThread):
        """截图识别工作线程 - 在后台执行识别任务，不阻塞UI"""
        # 定义信号
        finished = pyqtSignal(dict)  # 识别完成信号，传递结果
        error = pyqtSignal(str)      # 错误信号，传递错误信息
        
        def run(self):
            """线程执行函数"""
            try:
                # 在后台线程中执行截图识别
                result = run_and_store()
                # 发送完成信号
                self.finished.emit(result)
            except Exception as e:
                # 发送错误信号
                self.error.emit(str(e))

    # ==================== 截图分析页面 ====================
    
    class ScreenshotPage(QWidget):
        """截图分析页面"""
        def __init__(self, main_window, parent=None):
            super().__init__(parent)
            self.main_window = main_window
            self.setObjectName("screenshotPage")
            
            layout = QVBoxLayout(self)
            layout.setContentsMargins(15, 10, 15, 10)
            layout.setSpacing(12)
            
            title = SubtitleLabel("截图分析", self)
            title.setStyleSheet("font-size: 14px; font-weight: bold;")
            layout.addWidget(title)
            
            infoCard = SimpleCardWidget(self)
            infoLayout = QVBoxLayout(infoCard)
            infoLayout.setContentsMargins(15, 12, 15, 12)
            infoLayout.setSpacing(6)
            
            infoText = BodyLabel(
                "点击下方按钮，系统将自动截取当前屏幕画面，"
                "并通过AI识别当前正在进行的工作类型和内容。",
                infoCard
            )
            infoText.setWordWrap(True)
            infoText.setStyleSheet("color: #666666; font-size: 10px; line-height: 1.4;")
            infoLayout.addWidget(infoText)
            
            layout.addWidget(infoCard)
            
            btnCard = SimpleCardWidget(self)
            btnLayout = QVBoxLayout(btnCard)
            btnLayout.setContentsMargins(20, 15, 20, 15)
            btnLayout.setSpacing(8)
            btnLayout.setAlignment(Qt.AlignCenter)
            
            iconLabel = QLabel("📷", self)
            iconLabel.setAlignment(Qt.AlignCenter)
            iconLabel.setStyleSheet("font-size: 28px;")
            btnLayout.addWidget(iconLabel, 0, Qt.AlignCenter)
            
            self.captureBtn = PrimaryPushButton("开始截图分析", self)
            self.captureBtn.setFixedSize(160, 36)
            self.captureBtn.setStyleSheet("""
                PrimaryPushButton {
                    font-size: 12px;
                    font-weight: bold;
                    border-radius: 6px;
                }
            """)
            self.captureBtn.clicked.connect(self.startCapture)
            btnLayout.addWidget(self.captureBtn, 0, Qt.AlignCenter)
            
            self.statusLabel = CaptionLabel("等待操作...", btnCard)
            self.statusLabel.setAlignment(Qt.AlignCenter)
            self.statusLabel.setStyleSheet("color: #999999; font-size: 9px;")
            btnLayout.addWidget(self.statusLabel, 0, Qt.AlignCenter)
            
            layout.addWidget(btnCard)
            
            resultTitle = SectionTitle("分析结果", self)
            layout.addWidget(resultTitle)
            
            resultCard = SimpleCardWidget(self)
            resultLayout = QVBoxLayout(resultCard)
            resultLayout.setContentsMargins(12, 10, 12, 10)
            resultLayout.setSpacing(8)
            
            typeLayout = QHBoxLayout()
            typeLabel = BodyLabel("工作类型:", resultCard)
            typeLabel.setStyleSheet("color: #666666; font-weight: bold; font-size: 10px;")
            self.typeValue = BodyLabel("--", resultCard)
            self.typeValue.setStyleSheet("color: #0078d4; font-size: 12px; font-weight: bold;")
            typeLayout.addWidget(typeLabel)
            typeLayout.addWidget(self.typeValue)
            typeLayout.addStretch()
            resultLayout.addLayout(typeLayout)
            
            separator = QFrame(resultCard)
            separator.setFrameShape(QFrame.HLine)
            separator.setStyleSheet("background-color: #E0E0E0;")
            resultLayout.addWidget(separator)
            
            descLabel = BodyLabel("工作描述:", resultCard)
            descLabel.setStyleSheet("color: #666666; font-weight: bold; font-size: 10px;")
            resultLayout.addWidget(descLabel)
            
            self.descValue = BodyLabel("暂无分析结果", resultCard)
            self.descValue.setWordWrap(True)
            self.descValue.setStyleSheet("color: #333333; font-size: 10px; line-height: 1.4;")
            resultLayout.addWidget(self.descValue)
            
            layout.addWidget(resultCard, 1)
        
        def startCapture(self):
            """开始截图分析 - 使用多线程"""
            # 禁用按钮，防止重复点击
            self.captureBtn.setEnabled(False)
            self.captureBtn.setText("分析中...")
            self.statusLabel.setText("正在截图并分析，请稍候...")
            self.statusLabel.setStyleSheet("color: #FF9800; font-size: 9px;")
            
            # 创建并启动工作线程
            self.worker = ScreenshotWorker()
            self.worker.finished.connect(self.onCaptureSuccess)
            self.worker.error.connect(self.onCaptureError)
            self.worker.start()
        
        def onCaptureSuccess(self, result):
            """识别成功的回调函数"""
            self.typeValue.setText(result['type'])
            self.descValue.setText(result['description'])
            self.statusLabel.setText("分析完成！")
            self.statusLabel.setStyleSheet("color: #4CAF50; font-size: 9px;")
            
            InfoBar.success(
                title="分析完成",
                content=f"已识别为: {result['type']}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
            # 更新其他页面数据
            self.main_window.todayPage.updateData()
            
            # 恢复按钮状态
            self.captureBtn.setEnabled(True)
            self.captureBtn.setText("开始截图分析")
        
        def onCaptureError(self, error_msg):
            """识别失败的回调函数"""
            self.statusLabel.setText(f"分析失败: {error_msg}")
            self.statusLabel.setStyleSheet("color: #F44336; font-size: 9px;")
            
            InfoBar.error(
                title="分析失败",
                content=error_msg,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            
            # 恢复按钮状态
            self.captureBtn.setEnabled(True)
            self.captureBtn.setText("开始截图分析")

    # ==================== 工作记录页面 ====================
    
    class RecordsPage(QWidget):
        """工作记录页面 - Fluent Design 风格"""
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setObjectName("recordsPage")
            
            # 主布局
            mainLayout = QVBoxLayout(self)
            mainLayout.setContentsMargins(0, 0, 0, 0)
            mainLayout.setSpacing(0)
            
            # 滚动区域
            scrollArea = QScrollArea()
            scrollArea.setWidgetResizable(True)
            scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scrollArea.setStyleSheet("QScrollArea { border: none; background-color: #F5F5F5; }")
            
            contentWidget = QWidget()
            contentWidget.setStyleSheet("background-color: #F5F5F5; border: none;")
            layout = QVBoxLayout(contentWidget)
            layout.setContentsMargins(20, 15, 20, 15)
            layout.setSpacing(15)
            
            # 页面标题
            headerCard = QFrame()
            headerCard.setStyleSheet("QFrame { background-color: white; border-radius: 12px; border: none; }")
            headerLayout = QHBoxLayout(headerCard)
            headerLayout.setContentsMargins(20, 15, 20, 15)
            
            title = QLabel("📋 工作记录")
            title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            headerLayout.addWidget(title)
            headerLayout.addStretch()
            
            refreshBtn = QPushButton("🔄 刷新")
            refreshBtn.setCursor(Qt.PointingHandCursor)
            refreshBtn.setStyleSheet("""
                QPushButton {
                    background-color: #E3F2FD;
                    color: #1976D2;
                    padding: 8px 16px;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover { background-color: #BBDEFB; }
                QPushButton:pressed { background-color: #90CAF9; }
            """)
            refreshBtn.clicked.connect(self.updateData)
            headerLayout.addWidget(refreshBtn)
            
            layout.addWidget(headerCard)
            
            # 统计卡片
            statsCard = QFrame()
            statsCard.setStyleSheet("QFrame { background-color: white; border-radius: 12px; border: none; }")
            statsLayout = QHBoxLayout(statsCard)
            statsLayout.setContentsMargins(20, 12, 20, 12)
            statsLayout.setSpacing(30)
            
            self.countLabel = QLabel("📊 共 0 条记录")
            self.countLabel.setStyleSheet("font-size: 14px; color: #333333; font-weight: bold; border: none; background: transparent;")
            statsLayout.addWidget(self.countLabel)
            statsLayout.addStretch()
            
            layout.addWidget(statsCard)
            
            # 表格卡片
            tableCard = QFrame()
            tableCard.setStyleSheet("QFrame { background-color: white; border-radius: 12px; border: none; }")
            tableLayout = QVBoxLayout(tableCard)
            tableLayout.setContentsMargins(15, 15, 15, 15)
            
            # 使用 TableWidget (Fluent Design)
            self.recordsTable = TableWidget(self)
            self.recordsTable.setBorderRadius(8)
            self.recordsTable.setBorderVisible(True)
            self.recordsTable.setColumnCount(5)
            self.recordsTable.setHorizontalHeaderLabels(["序号", "时间", "类型", "描述", "时长"])
            self.recordsTable.horizontalHeader().setStretchLastSection(True)
            self.recordsTable.setColumnWidth(0, 60)
            self.recordsTable.setColumnWidth(1, 120)
            self.recordsTable.setColumnWidth(2, 80)
            self.recordsTable.setColumnWidth(3, 450)
            self.recordsTable.setColumnWidth(4, 80)
            self.recordsTable.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.recordsTable.setSelectionBehavior(QTableWidget.SelectRows)
            self.recordsTable.setAlternatingRowColors(True)
            
            tableLayout.addWidget(self.recordsTable)
            layout.addWidget(tableCard, 1)
            
            scrollArea.setWidget(contentWidget)
            mainLayout.addWidget(scrollArea)
        
        def updateData(self):
            """更新记录数据（按时间倒序排列）"""
            records = get_daily_records()
            
            # 按时间倒序排列（最近的在前面）
            records.sort(key=lambda r: r.get('时间', ''), reverse=True)
            
            self.recordsTable.setRowCount(len(records))
            self.countLabel.setText(f"📊 共 {len(records)} 条记录")
            
            for row, record in enumerate(records):
                # 序号
                idItem = QTableWidgetItem(str(row + 1))
                idItem.setTextAlignment(Qt.AlignCenter)
                self.recordsTable.setItem(row, 0, idItem)
                
                # 时间
                timeItem = QTableWidgetItem(record['时间'])
                timeItem.setTextAlignment(Qt.AlignCenter)
                self.recordsTable.setItem(row, 1, timeItem)
                
                # 类型
                typeItem = QTableWidgetItem(record['工作类型'])
                typeItem.setTextAlignment(Qt.AlignCenter)
                self.recordsTable.setItem(row, 2, typeItem)
                
                # 描述
                descItem = QTableWidgetItem(record['工作描述'])
                self.recordsTable.setItem(row, 3, descItem)
                
                # 时长
                duration = record.get('持续时长(分钟)', '0')
                try:
                    duration_min = float(duration)
                    duration_text = f"{duration_min:.0f}分钟" if duration_min > 0 else "-"
                except:
                    duration_text = "-"
                durationItem = QTableWidgetItem(duration_text)
                durationItem.setTextAlignment(Qt.AlignCenter)
                self.recordsTable.setItem(row, 4, durationItem)

    # ==================== 工作时间线页面 ====================
    
    # 工作类型颜色映射（固定颜色）
    TYPE_COLORS = {
        "开发": "#4CAF50",    # 绿色
        "沟通": "#2196F3",    # 蓝色
        "生活": "#FF9800",    # 橙色
        "学习": "#9C27B0",    # 紫色
        "设计": "#E91E63",    # 粉色
        "管理": "#00BCD4",    # 青色
        "文档": "#795548",    # 棕色
        "娱乐": "#F44336",    # 红色
        "产品": "#FF5722",    # 深橙色
        "会议": "#3F51B5",    # 靛蓝色
        "运维": "#009688",    # 青绿色
        "测试": "#FFC107",    # 琥珀色
        "数据分析": "#673AB7", # 深紫色
        "其他": "#607D8B",    # 灰蓝色
    }
    
    class PieChartWidget(QWidget):
        """饼状图组件"""
        def __init__(self, parent=None):
            super().__init__(parent)
            self.data = []  # [(name, value, color), ...]
            self.show_percentage = True  # True=显示占比, False=显示时长
            self.setMinimumSize(200, 200)
        
        def setData(self, data):
            """设置数据: [(name, value, color), ...]"""
            self.data = data
            self.update()  # 触发重绘
        
        def setShowPercentage(self, show_percentage):
            """设置是否显示占比"""
            self.show_percentage = show_percentage
            self.update()  # 触发重绘
        
        def paintEvent(self, event):
            """绘制饼状图"""
            if not self.data:
                return
            
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 计算可用区域
            width = self.width()
            height = self.height()
            
            # 饼图区域（左侧）
            pie_size = min(width * 0.6, height * 0.9)
            pie_x = 20
            pie_y = (height - pie_size) / 2
            
            # 计算总值
            total = sum(item[1] for item in self.data)
            if total == 0:
                painter.end()
                return
            
            # 绘制饼图
            start_angle = 0
            for name, value, color in self.data:
                if value <= 0:
                    continue
                
                # 计算角度
                angle = int(360 * 16 * value / total)  # Qt使用1/16度为单位
                
                # 设置画刷
                painter.setBrush(QColor(color))
                painter.setPen(QPen(QColor("#FFFFFF"), 2))
                
                # 绘制扇形
                painter.drawPie(int(pie_x), int(pie_y), int(pie_size), int(pie_size), 
                               start_angle, angle)
                
                start_angle += angle
            
            # 绘制图例（右侧）
            legend_x = pie_x + pie_size + 20
            legend_y = pie_y + 10
            legend_spacing = 22
            
            for i, (name, value, color) in enumerate(self.data):
                if value <= 0:
                    continue
                
                y = legend_y + i * legend_spacing
                percentage = (value / total * 100) if total > 0 else 0
                hours = value / 60  # 转换为小时
                
                # 绘制颜色方块
                painter.setBrush(QColor(color))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(int(legend_x), int(y), 12, 12, 2, 2)
                
                # 绘制文字
                painter.setPen(QColor("#333333"))
                font = QFont("Microsoft YaHei", 9)
                painter.setFont(font)
                
                # 根据模式显示时长或占比
                if self.show_percentage:
                    value_text = f"{percentage:.1f}%"
                else:
                    value_text = f"{hours:.1f}h"
                
                painter.drawText(int(legend_x + 18), int(y + 10), 
                               f"{name} {value_text}")
            
            painter.end()
    
    class TimelinePage(QWidget):
        """工作时间线页面 - 替代数据统计页面"""
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setObjectName("timelinePage")
            self.main_window = parent
            
            # 主布局
            mainLayout = QVBoxLayout(self)
            mainLayout.setContentsMargins(0, 0, 0, 0)
            mainLayout.setSpacing(0)
            
            # 滚动区域
            scrollArea = QScrollArea()
            scrollArea.setWidgetResizable(True)
            scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scrollArea.setStyleSheet("QScrollArea { border: none; background-color: #F9F9F9; }")
            
            contentWidget = QWidget()
            contentWidget.setStyleSheet("background-color: #F9F9F9; border: none;")
            layout = QVBoxLayout(contentWidget)
            layout.setSpacing(15)
            layout.setContentsMargins(20, 15, 20, 15)
            
            # ========== 1. 顶部筛选栏 ==========
            filterCard = QFrame()
            filterCard.setStyleSheet("QFrame { background-color: white; border-radius: 10px; border: none; }")
            filterLayout = QHBoxLayout(filterCard)
            filterLayout.setContentsMargins(15, 12, 15, 12)
            filterLayout.setSpacing(12)
            
            # 日期选择 - 开始日期（使用 Fluent CalendarPicker）
            self.startDatePicker = CalendarPicker()
            self.startDatePicker.setDate(QDate.currentDate())
            self.startDatePicker.setDateFormat("yyyy/MM/dd")
            self.startDatePicker.setFixedWidth(140)
            self.startDatePicker.dateChanged.connect(self.updateData)
            filterLayout.addWidget(self.startDatePicker)
            
            # "至" 文本
            toLabel = QLabel("至")
            toLabel.setStyleSheet("color: #666666; font-size: 12px; border: none; background: transparent;")
            filterLayout.addWidget(toLabel)
            
            # 日期选择 - 结束日期（使用 Fluent CalendarPicker）
            self.endDatePicker = CalendarPicker()
            self.endDatePicker.setDate(QDate.currentDate())
            self.endDatePicker.setDateFormat("yyyy/MM/dd")
            self.endDatePicker.setFixedWidth(140)
            self.endDatePicker.dateChanged.connect(self.updateData)
            filterLayout.addWidget(self.endDatePicker)
            
            filterLayout.addStretch()
            
            # 搜索框（使用 Fluent SearchLineEdit）
            self.searchInput = SearchLineEdit()
            self.searchInput.setPlaceholderText("搜索活动...")
            self.searchInput.setClearButtonEnabled(True)
            self.searchInput.setFixedWidth(200)
            self.searchInput.textChanged.connect(self.filterTimeline)
            filterLayout.addWidget(self.searchInput)
            
            layout.addWidget(filterCard)
            
            # ========== 2. 核心数据统计区 ==========
            statsCard = QFrame()
            statsCard.setStyleSheet("QFrame { background-color: white; border-radius: 10px; border: none; }")
            statsLayout = QHBoxLayout(statsCard)
            statsLayout.setContentsMargins(20, 15, 20, 15)
            statsLayout.setSpacing(40)
            
            # 记录条数
            recordWidget = QWidget()
            recordWidget.setStyleSheet("border: none; background: transparent;")
            recordLayout = QVBoxLayout(recordWidget)
            recordLayout.setSpacing(4)
            self.recordCountLabel = QLabel("0")
            self.recordCountLabel.setStyleSheet("font-size: 28px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            recordLayout.addWidget(self.recordCountLabel)
            recordSubLabel = QLabel("记录条数")
            recordSubLabel.setStyleSheet("font-size: 12px; color: #999999; border: none; background: transparent;")
            recordLayout.addWidget(recordSubLabel)
            statsLayout.addWidget(recordWidget)
            
            # 专注时长
            durationWidget = QWidget()
            durationWidget.setStyleSheet("border: none; background: transparent;")
            durationLayout = QVBoxLayout(durationWidget)
            durationLayout.setSpacing(4)
            self.durationLabel = QLabel("0h")
            self.durationLabel.setStyleSheet("font-size: 28px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            durationLayout.addWidget(self.durationLabel)
            durationSubLabel = QLabel("专注时长")
            durationSubLabel.setStyleSheet("font-size: 12px; color: #999999; border: none; background: transparent;")
            durationLayout.addWidget(durationSubLabel)
            statsLayout.addWidget(durationWidget)
            
            # 活跃时段
            activeWidget = QWidget()
            activeWidget.setStyleSheet("border: none; background: transparent;")
            activeLayout = QVBoxLayout(activeWidget)
            activeLayout.setSpacing(4)
            self.activeTimeLabel = QLabel("--:-- — --:--")
            self.activeTimeLabel.setStyleSheet("font-size: 20px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            activeLayout.addWidget(self.activeTimeLabel)
            activeSubLabel = QLabel("活跃时段")
            activeSubLabel.setStyleSheet("font-size: 12px; color: #999999; border: none; background: transparent;")
            activeLayout.addWidget(activeSubLabel)
            statsLayout.addWidget(activeWidget)
            
            statsLayout.addStretch()
            
            # 显示分类时长分布开关
            self.showDistCheckBox = QCheckBox("显示分类时长分布")
            self.showDistCheckBox.setChecked(True)
            self.showDistCheckBox.setStyleSheet("""
                QCheckBox {
                    font-size: 12px; color: #333333; border: none; background: transparent;
                    spacing: 6px;
                }
                QCheckBox::indicator {
                    width: 18px; height: 18px;
                    border: 2px solid #E0E0E0;
                    border-radius: 4px;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    background-color: #4CAF50;
                    border: 2px solid #4CAF50;
                }
            """)
            self.showDistCheckBox.stateChanged.connect(self.toggleDistribution)
            statsLayout.addWidget(self.showDistCheckBox)
            
            layout.addWidget(statsCard)
            
            # ========== 3. 分类时长分布图 ==========
            self.distCard = QFrame()
            self.distCard.setStyleSheet("QFrame { background-color: white; border-radius: 10px; border: none; }")
            distLayout = QVBoxLayout(self.distCard)
            distLayout.setContentsMargins(20, 15, 20, 15)
            distLayout.setSpacing(12)
            
            # 标题栏（含切换按钮）
            distHeaderLayout = QHBoxLayout()
            distTitle = QLabel("📊 分类时长分布")
            distTitle.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; border: none; background: transparent;")
            distHeaderLayout.addWidget(distTitle)
            distHeaderLayout.addStretch()
            
            # 切换按钮样式
            btnStyle = """
                QPushButton {
                    background-color: #E3F2FD;
                    color: #1976D2;
                    padding: 5px 12px;
                    border-radius: 15px;
                    font-size: 11px;
                    border: none;
                }
                QPushButton:hover { background-color: #BBDEFB; }
            """
            
            # 时长/占比切换按钮
            self.distValueBtn = QPushButton("⏱️ 时长")
            self.distValueBtn.setCursor(Qt.PointingHandCursor)
            self.distValueBtn.setStyleSheet(btnStyle)
            self.distValueBtn.clicked.connect(self.toggleDistValueMode)
            distHeaderLayout.addWidget(self.distValueBtn)
            
            # 饼状图/条形图切换按钮
            self.distModeBtn = QPushButton("🥧 条形图")
            self.distModeBtn.setCursor(Qt.PointingHandCursor)
            self.distModeBtn.setStyleSheet(btnStyle)
            self.distModeBtn.clicked.connect(self.toggleDistMode)
            distHeaderLayout.addWidget(self.distModeBtn)
            
            distLayout.addLayout(distHeaderLayout)
            
            # 当前显示模式（False=条形图, True=饼状图）
            self.is_pie_mode = False
            # 当前数值模式（False=时长, True=占比）
            self.is_percentage_mode = False
            
            # 条形容器
            self.barContainer = QWidget()
            self.barContainer.setStyleSheet("border: none; background: transparent;")
            self.distListLayout = QVBoxLayout(self.barContainer)
            self.distListLayout.setSpacing(8)
            self.distListLayout.setContentsMargins(0, 0, 0, 0)
            distLayout.addWidget(self.barContainer)
            
            # 饼状图容器
            self.pieContainer = QWidget()
            self.pieContainer.setStyleSheet("border: none; background: transparent;")
            self.pieContainer.setVisible(False)
            self.pieLayout = QVBoxLayout(self.pieContainer)
            self.pieLayout.setContentsMargins(0, 0, 0, 0)
            self.pieChart = PieChartWidget()
            self.pieChart.setMinimumHeight(250)
            self.pieLayout.addWidget(self.pieChart)
            distLayout.addWidget(self.pieContainer)
            
            layout.addWidget(self.distCard)
            
            # ========== 4. 活动时间轴列表 ==========
            timelineCard = QFrame()
            timelineCard.setStyleSheet("QFrame { background-color: white; border-radius: 10px; border: none; }")
            timelineLayout = QVBoxLayout(timelineCard)
            timelineLayout.setContentsMargins(20, 15, 20, 15)
            timelineLayout.setSpacing(12)
            
            # 工具栏
            toolbarLayout = QHBoxLayout()
            
            toolbarTitle = QLabel("⏱️ 活动时间线")
            toolbarTitle.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; border: none; background: transparent;")
            toolbarLayout.addWidget(toolbarTitle)
            
            # 标签筛选下拉框（使用 Fluent ComboBox）
            self.tagFilterCombo = ComboBox()
            self.tagFilterCombo.addItems(["全部标签", "开发", "沟通", "生活", "学习", "设计", "管理", "文档", "娱乐", "产品", "会议", "运维", "测试", "数据分析", "其他"])
            self.tagFilterCombo.setCurrentIndex(0)
            self.tagFilterCombo.setFixedWidth(120)
            self.tagFilterCombo.currentTextChanged.connect(self.filterTimeline)
            toolbarLayout.addWidget(self.tagFilterCombo)
            
            toolbarLayout.addStretch()
            
            # 快速时间筛选按钮（使用 Fluent PillPushButton）
            for text in ["近30分", "近1小时", "近2小时", "今天"]:
                btn = PillPushButton(text)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setCheckable(False)
                btn.clicked.connect(lambda checked, t=text: self.quickFilter(t))
                toolbarLayout.addWidget(btn)
            
            # 复制日志按钮（使用 Fluent TransparentPushButton）
            copyBtn = TransparentPushButton("复制日志")
            copyBtn.setIcon(FluentIcon.COPY)
            copyBtn.setCursor(Qt.PointingHandCursor)
            copyBtn.clicked.connect(self.copyLog)
            toolbarLayout.addWidget(copyBtn)
            
            timelineLayout.addLayout(toolbarLayout)
            
            # 时间轴列表容器
            self.timelineContainer = QWidget()
            self.timelineContainer.setStyleSheet("border: none; background: transparent;")
            self.timelineListLayout = QVBoxLayout(self.timelineContainer)
            self.timelineListLayout.setSpacing(0)
            self.timelineListLayout.setContentsMargins(0, 0, 0, 0)
            timelineLayout.addWidget(self.timelineContainer)
            
            layout.addWidget(timelineCard, 1)  # 时间轴占据更多空间
            
            # 添加弹性空间
            layout.addStretch()
            
            scrollArea.setWidget(contentWidget)
            mainLayout.addWidget(scrollArea)
            
            # 存储所有记录用于筛选
            self.all_records = []
        
        def toggleDistribution(self, state):
            """切换分类时长分布显示"""
            self.distCard.setVisible(state == Qt.Checked)
        
        def toggleDistMode(self):
            """切换条形图/饼状图模式"""
            self.is_pie_mode = not self.is_pie_mode
            
            if self.is_pie_mode:
                self.distModeBtn.setText("📊 饼状图")
                self.barContainer.setVisible(False)
                self.pieContainer.setVisible(True)
            else:
                self.distModeBtn.setText("🥧 条形图")
                self.barContainer.setVisible(True)
                self.pieContainer.setVisible(False)
            
            # 刷新数据
            self.updateDistribution()
        
        def toggleDistValueMode(self):
            """切换时长/占比显示模式"""
            self.is_percentage_mode = not self.is_percentage_mode
            
            if self.is_percentage_mode:
                self.distValueBtn.setText("📈 占比")
            else:
                self.distValueBtn.setText("⏱️ 时长")
            
            # 更新饼状图显示模式
            self.pieChart.setShowPercentage(self.is_percentage_mode)
            
            # 刷新数据
            self.updateDistribution()
        
        def quickFilter(self, timeText):
            """快速时间筛选"""
            now = QDate.currentDate()
            if timeText == "今天":
                self.startDatePicker.setDate(now)
                self.endDatePicker.setDate(now)
            elif timeText == "近30分":
                self.startDatePicker.setDate(now)
                self.endDatePicker.setDate(now)
            elif timeText == "近1小时":
                self.startDatePicker.setDate(now)
                self.endDatePicker.setDate(now)
            elif timeText == "近2小时":
                self.startDatePicker.setDate(now)
                self.endDatePicker.setDate(now)
        
        def filterTimeline(self):
            """筛选时间轴"""
            self.updateData()
        
        def copyLog(self):
            """复制日志到剪贴板"""
            records = self.getFilteredRecords()
            if not records:
                return
            
            log_text = ""
            for record in records:
                time = record.get('时间', '')
                work_type = record.get('工作类型', '')
                description = record.get('工作描述', '')
                log_text += f"[{time}] [{work_type}] {description}\n"
            
            QApplication.clipboard().setText(log_text)
            InfoBar.success(
                title="复制成功",
                content=f"已复制 {len(records)} 条记录到剪贴板",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        
        def getFilteredRecords(self):
            """获取筛选后的记录"""
            records = self.all_records.copy()
            
            # 按标签筛选
            tag = self.tagFilterCombo.currentText()
            if tag != "全部标签":
                records = [r for r in records if r.get('工作类型') == tag]
            
            # 按搜索关键词筛选
            keyword = self.searchInput.text().strip()
            if keyword:
                records = [r for r in records if keyword.lower() in r.get('工作描述', '').lower()]
            
            return records
        
        def updateData(self):
            """更新页面数据"""
            # 获取日期范围内的记录
            start_date = self.startDatePicker.date.toString("yyyy-MM-dd")
            end_date = self.endDatePicker.date.toString("yyyy-MM-dd")
            
            # 验证日期范围
            if self.startDatePicker.date > self.endDatePicker.date:
                InfoBar.warning(
                    title="日期范围错误",
                    content="开始日期不能晚于结束日期",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                return
            
            # 读取所有记录
            all_records = read_records()
            
            # 筛选日期范围内的记录
            self.all_records = [r for r in all_records if start_date <= r.get('日期', '') <= end_date]
            
            # 更新统计数据
            self.updateStats()
            
            # 更新分类分布
            self.updateDistribution()
            
            # 更新时间轴
            self.updateTimeline()
        
        def updateStats(self):
            """更新统计数据"""
            records = self.all_records
            
            # 记录条数
            self.recordCountLabel.setText(str(len(records)))
            
            # 专注时长（总分钟数转小时）
            total_minutes = 0
            for r in records:
                try:
                    total_minutes += float(r.get('持续时长(分钟)', '0'))
                except:
                    pass
            hours = total_minutes / 60
            self.durationLabel.setText(f"{hours:.1f}h")
            
            # 活跃时段（最早和最晚时间）
            if records:
                times = [r.get('时间', '23:59:59') for r in records]
                earliest = min(times)
                latest = max(times)
                self.activeTimeLabel.setText(f"{earliest[:5]} — {latest[:5]}")
            else:
                self.activeTimeLabel.setText("--:-- — --:--")
        
        def updateDistribution(self):
            """更新分类时长分布"""
            # 统计各类型时长
            type_hours = {}
            total_minutes = 0
            for r in self.all_records:
                work_type = r.get('工作类型', '其他')
                try:
                    minutes = float(r.get('持续时长(分钟)', '0'))
                except:
                    minutes = 0
                type_hours[work_type] = type_hours.get(work_type, 0) + minutes
                total_minutes += minutes
            
            # 按时长排序
            sorted_types = sorted(type_hours.items(), key=lambda x: x[1], reverse=True)
            
            # 更新条形图
            # 清空旧内容
            while self.distListLayout.count():
                child = self.distListLayout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # 创建进度条
            for work_type, minutes in sorted_types:
                hours = minutes / 60
                percentage = (minutes / total_minutes * 100) if total_minutes > 0 else 0
                color = TYPE_COLORS.get(work_type, "#607D8B")
                
                # 单行容器
                rowWidget = QWidget()
                rowWidget.setStyleSheet("border: none; background: transparent;")
                rowLayout = QHBoxLayout(rowWidget)
                rowLayout.setContentsMargins(0, 0, 0, 0)
                rowLayout.setSpacing(12)
                
                # 类型名称
                nameLabel = QLabel(work_type)
                nameLabel.setFixedWidth(50)
                nameLabel.setStyleSheet(f"font-size: 12px; color: {color}; font-weight: bold; border: none; background: transparent;")
                rowLayout.addWidget(nameLabel)
                
                # 进度条背景
                progressBg = QFrame()
                progressBg.setFixedHeight(8)
                progressBg.setStyleSheet("background-color: #EDEDED; border-radius: 4px; border: none;")
                progressBgLayout = QHBoxLayout(progressBg)
                progressBgLayout.setContentsMargins(0, 0, 0, 0)
                progressBgLayout.setSpacing(0)
                
                # 进度条填充（左对齐）
                progressFill = QFrame()
                progressFill.setFixedHeight(8)
                progressFill.setStyleSheet(f"background-color: {color}; border-radius: 4px; border: none;")
                
                # 设置进度条宽度比例
                fillWidth = max(4, int(300 * percentage / 100))
                progressFill.setFixedWidth(fillWidth)
                
                # 添加到布局并左对齐
                progressBgLayout.addWidget(progressFill, 0, Qt.AlignLeft)
                progressBgLayout.addStretch(1)
                
                rowLayout.addWidget(progressBg, 1)
                
                # 时长/占比文本
                if self.is_percentage_mode:
                    valueText = f"{percentage:.1f}%"
                else:
                    valueText = f"{hours:.1f}h"
                timeLabel = QLabel(valueText)
                timeLabel.setFixedWidth(50)
                timeLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                timeLabel.setStyleSheet("font-size: 12px; color: #999999; border: none; background: transparent;")
                rowLayout.addWidget(timeLabel)
                
                self.distListLayout.addWidget(rowWidget)
            
            # 更新饼状图
            pie_data = []
            for work_type, minutes in sorted_types:
                color = TYPE_COLORS.get(work_type, "#607D8B")
                pie_data.append((work_type, minutes, color))
            self.pieChart.setData(pie_data)
        
        def updateTimeline(self):
            """更新时间轴列表"""
            # 清空旧内容
            while self.timelineListLayout.count():
                child = self.timelineListLayout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # 获取筛选后的记录
            records = self.getFilteredRecords()
            
            # 按时间倒序显示（最新的在上面）
            records = list(reversed(records))
            
            for i, record in enumerate(records):
                time = record.get('时间', '')
                date = record.get('日期', '')
                work_type = record.get('工作类型', '其他')
                description = record.get('工作描述', '')
                duration = record.get('持续时长(分钟)', '0')
                color = TYPE_COLORS.get(work_type, "#607D8B")
                
                # 计算结束时间
                try:
                    duration_min = float(duration)
                    start_dt = datetime.strptime(time, '%H:%M:%S')
                    end_dt = start_dt + timedelta(minutes=duration_min)
                    end_time = end_dt.strftime('%H:%M:%S')
                    time_range = f"{time[:5]} — {end_time[:5]}"
                except:
                    time_range = ""
                
                # 格式化日期显示（月-日）
                date_display = ""
                if date:
                    try:
                        date_obj = datetime.strptime(date, '%Y-%m-%d')
                        date_display = date_obj.strftime('%m/%d')
                    except:
                        date_display = ""
                
                # 列表项容器
                itemWidget = QWidget()
                itemWidget.setStyleSheet("border: none; background: transparent;")
                itemLayout = QHBoxLayout(itemWidget)
                itemLayout.setContentsMargins(0, 5, 0, 5)
                itemLayout.setSpacing(12)
                
                # 时间戳（包含日期和时间）
                timeLabel = QLabel(f"{date_display}\n{time[:5]}")
                timeLabel.setFixedWidth(55)
                timeLabel.setAlignment(Qt.AlignRight | Qt.AlignTop)
                timeLabel.setStyleSheet("font-size: 11px; color: #999999; border: none; background: transparent;")
                itemLayout.addWidget(timeLabel)
                
                # 时间轴指示器
                indicatorWidget = QWidget()
                indicatorWidget.setFixedWidth(20)
                indicatorWidget.setStyleSheet("border: none; background: transparent;")
                indicatorLayout = QVBoxLayout(indicatorWidget)
                indicatorLayout.setContentsMargins(0, 4, 0, 0)
                indicatorLayout.setSpacing(0)
                
                # 圆点
                dot = QLabel()
                dot.setFixedSize(10, 10)
                dot.setStyleSheet(f"background-color: {color}; border-radius: 5px; border: none;")
                indicatorLayout.addWidget(dot, 0, Qt.AlignHCenter)
                
                # 连接线（如果不是最后一个）
                if i < len(records) - 1:
                    line = QFrame()
                    line.setFixedWidth(2)
                    line.setStyleSheet("background-color: #E0E0E0; border: none;")
                    indicatorLayout.addWidget(line, 1, Qt.AlignHCenter)
                
                itemLayout.addWidget(indicatorWidget)
                
                # 内容卡片
                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background-color: #FAFAFA;
                        border-radius: 8px;
                        border: 1px solid #F0F0F0;
                    }
                """)
                cardLayout = QVBoxLayout(card)
                cardLayout.setContentsMargins(12, 10, 12, 10)
                cardLayout.setSpacing(8)
                
                # 文本内容
                descLabel = QLabel(description)
                descLabel.setWordWrap(True)
                descLabel.setStyleSheet("font-size: 12px; color: #333333; border: none; background: transparent;")
                cardLayout.addWidget(descLabel)
                
                # 底部标签栏
                tagsLayout = QHBoxLayout()
                tagsLayout.setSpacing(8)
                
                # 类型标签
                typeTag = QLabel(work_type)
                typeTag.setStyleSheet(f"""
                    QLabel {{
                        background-color: {color};
                        color: white;
                        padding: 2px 8px;
                        border-radius: 10px;
                        font-size: 10px;
                        font-weight: bold;
                        border: none;
                    }}
                """)
                tagsLayout.addWidget(typeTag)
                
                # 自动记录标签
                autoTag = QLabel("自动记录")
                autoTag.setStyleSheet("""
                    QLabel {
                        background-color: #E0E0E0;
                        color: #666666;
                        padding: 2px 8px;
                        border-radius: 10px;
                        font-size: 10px;
                        border: none;
                    }
                """)
                tagsLayout.addWidget(autoTag)
                
                # 时间段
                if time_range:
                    timeRangeLabel = QLabel(time_range)
                    timeRangeLabel.setStyleSheet("font-size: 10px; color: #CCCCCC; border: none; background: transparent;")
                    tagsLayout.addWidget(timeRangeLabel)
                
                tagsLayout.addStretch()
                cardLayout.addLayout(tagsLayout)
                
                itemLayout.addWidget(card, 1)
                
                self.timelineListLayout.addWidget(itemWidget)
            
            # 如果没有记录
            if not records:
                emptyLabel = QLabel("暂无记录")
                emptyLabel.setAlignment(Qt.AlignCenter)
                emptyLabel.setStyleSheet("font-size: 14px; color: #CCCCCC; padding: 40px; border: none; background: transparent;")
                self.timelineListLayout.addWidget(emptyLabel)

    # ==================== 报告模板数据 ====================
    
    # 从 store 模块加载报告模板
    from store import read_templates, write_templates, add_template, delete_template, export_templates, import_templates
    REPORT_TEMPLATES = read_templates()
    
    # ==================== 报告生成工作线程 ====================
    
    class ReportGenerateWorker(QThread):
        """报告生成工作线程"""
        chunk_received = pyqtSignal(str)  # 接收到一块内容
        generation_finished = pyqtSignal(str)  # 生成完成
        generation_error = pyqtSignal(str)  # 生成出错
        
        def __init__(self, template_prompt, start_date, end_date, report_type):
            super().__init__()
            self.template_prompt = template_prompt
            self.start_date = start_date
            self.end_date = end_date
            self.report_type = report_type
            self.full_content = ""
        
        def run(self):
            try:
                def on_chunk(chunk, is_finished):
                    if chunk:
                        self.full_content += chunk
                        self.chunk_received.emit(chunk)
                    if is_finished:
                        self.generation_finished.emit(self.full_content)
                
                from screenshot import generate_report_stream
                generate_report_stream(
                    self.template_prompt,
                    self.start_date,
                    self.end_date,
                    self.report_type,
                    callback=on_chunk
                )
            
            except Exception as e:
                self.generation_error.emit(str(e))
    
    # ==================== 生成报告页面 ====================
    
    class TemplateCard(QFrame):
        """模板卡片组件"""
        clicked = pyqtSignal(int)  # 点击信号，传递模板索引
        preview_clicked = pyqtSignal(int)  # 预览按钮点击信号
        delete_clicked = pyqtSignal(int)  # 删除按钮点击信号
        
        def __init__(self, index, name, intro, is_cloud=True, parent=None):
            super().__init__(parent)
            self.index = index
            self.is_selected = False
            self.is_hovered = False
            self.setFixedSize(280, 140)
            self.setCursor(Qt.PointingHandCursor)
            self.setMouseTracking(True)
            
            # 主布局
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 14, 16, 14)
            layout.setSpacing(8)
            
            # 标题行
            titleLayout = QHBoxLayout()
            titleLabel = QLabel(name)
            titleLabel.setStyleSheet("font-size: 14px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            titleLayout.addWidget(titleLabel)
            titleLayout.addStretch()
            
            # 选中对勾图标（默认隐藏）
            self.checkIcon = QLabel("✓")
            self.checkIcon.setFixedSize(20, 20)
            self.checkIcon.setAlignment(Qt.AlignCenter)
            self.checkIcon.setStyleSheet("""
                QLabel {
                    background-color: #16A34A;
                    color: white;
                    border-radius: 10px;
                    font-size: 12px;
                    font-weight: bold;
                    border: none;
                }
            """)
            self.checkIcon.setVisible(False)
            titleLayout.addWidget(self.checkIcon)
            layout.addLayout(titleLayout)
            
            # 简介
            introLabel = QLabel(intro)
            introLabel.setWordWrap(True)
            introLabel.setMaximumHeight(40)
            introLabel.setStyleSheet("font-size: 12px; color: #666666; border: none; background: transparent;")
            introLabel.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            layout.addWidget(introLabel)
            
            layout.addStretch()
            
            # 底部标签行
            tagLayout = QHBoxLayout()
            if is_cloud:
                tag = QLabel("云端")
                tag.setStyleSheet("""
                    QLabel {
                        background-color: #E3F7EA;
                        color: #16A34A;
                        padding: 2px 8px;
                        border-radius: 10px;
                        font-size: 10px;
                        font-weight: bold;
                        border: none;
                    }
                """)
                tagLayout.addWidget(tag)
            tagLayout.addStretch()
            
            # 删除按钮（默认隐藏）
            self.deleteBtn = QPushButton("🗑")
            self.deleteBtn.setFixedSize(28, 28)
            self.deleteBtn.setCursor(Qt.PointingHandCursor)
            self.deleteBtn.setStyleSheet("""
                QPushButton {
                    background-color: #FEE2E2;
                    border-radius: 14px;
                    font-size: 14px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #FECACA;
                }
            """)
            self.deleteBtn.setVisible(False)
            self.deleteBtn.clicked.connect(lambda: self.delete_clicked.emit(self.index))
            tagLayout.addWidget(self.deleteBtn)
            
            # 预览按钮（默认隐藏）
            self.previewBtn = QPushButton("👁")
            self.previewBtn.setFixedSize(28, 28)
            self.previewBtn.setCursor(Qt.PointingHandCursor)
            self.previewBtn.setStyleSheet("""
                QPushButton {
                    background-color: #F3F4F6;
                    border: 1px solid #E5E7EB;
                    border-radius: 14px;
                    font-size: 14px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #E5E7EB;
                }
            """)
            self.previewBtn.setVisible(False)
            self.previewBtn.clicked.connect(lambda: self.preview_clicked.emit(self.index))
            tagLayout.addWidget(self.previewBtn)
            
            layout.addLayout(tagLayout)
            
            self.updateStyle()
        
        def setSelected(self, selected):
            self.is_selected = selected
            self.checkIcon.setVisible(selected)
            self.updateStyle()
        
        def updateStyle(self):
            if self.is_selected:
                self.setStyleSheet("""
                    TemplateCard {
                        background-color: #F0FBF4;
                        border: 2px solid #16A34A;
                        border-radius: 12px;
                    }
                """)
            else:
                self.setStyleSheet("""
                    TemplateCard {
                        background-color: white;
                        border: 1px solid #ECECEC;
                        border-radius: 12px;
                    }
                    TemplateCard:hover {
                        border: 1px solid #D1D5DB;
                    }
                """)
        
        def enterEvent(self, event):
            self.is_hovered = True
            self.previewBtn.setVisible(True)
            self.deleteBtn.setVisible(True)
            super().enterEvent(event)
        
        def leaveEvent(self, event):
            self.is_hovered = False
            self.previewBtn.setVisible(False)
            self.deleteBtn.setVisible(False)
            super().leaveEvent(event)
        
        def mousePressEvent(self, event):
            if not self.previewBtn.underMouse() and not self.deleteBtn.underMouse():
                self.clicked.emit(self.index)
            super().mousePressEvent(event)
    
    class TemplatePreviewDialog(QDialog):
        """模板提示词查看弹窗（4.1）"""
        prompt_updated = pyqtSignal(int, str)  # 信号：模板索引，新提示词
        
        def __init__(self, template_index, template_name, template_desc, prompt_text, parent=None):
            super().__init__(parent)
            self.template_index = template_index
            self.template_name = template_name
            self.is_editing = False
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setModal(True)
            
            # 主布局
            mainLayout = QHBoxLayout(self)
            mainLayout.setContentsMargins(0, 0, 0, 0)
            
            # 半透明遮罩
            overlay = QWidget()
            overlay.setStyleSheet("background-color: rgba(0, 0, 0, 100);")
            overlayLayout = QVBoxLayout(overlay)
            overlayLayout.setAlignment(Qt.AlignCenter)
            
            # 弹窗卡片
            card = QFrame()
            card.setFixedSize(750, 600)
            card.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 16px;
                    border: 1px solid #ECECEC;
                }
            """)
            cardLayout = QVBoxLayout(card)
            cardLayout.setContentsMargins(24, 24, 24, 24)
            cardLayout.setSpacing(16)
            
            # 头部
            headerLayout = QHBoxLayout()
            titleLabel = QLabel(template_name)
            titleLabel.setStyleSheet("font-size: 18px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            headerLayout.addWidget(titleLabel)
            headerLayout.addStretch()
            
            # 修改按钮
            self.editBtn = QPushButton("✏️ 修改")
            self.editBtn.setCursor(Qt.PointingHandCursor)
            self.editBtn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #374151;
                    padding: 8px 16px;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #F9FAFB;
                }
            """)
            self.editBtn.clicked.connect(self.toggleEdit)
            headerLayout.addWidget(self.editBtn)
            
            closeBtn = QPushButton("✕")
            closeBtn.setFixedSize(32, 32)
            closeBtn.setCursor(Qt.PointingHandCursor)
            closeBtn.setStyleSheet("""
                QPushButton {
                    background-color: #F3F4F6;
                    border: none;
                    border-radius: 16px;
                    font-size: 16px;
                    color: #666666;
                }
                QPushButton:hover {
                    background-color: #E5E7EB;
                }
            """)
            closeBtn.clicked.connect(self.close)
            headerLayout.addWidget(closeBtn)
            cardLayout.addLayout(headerLayout)
            
            # 描述
            descLayout = QHBoxLayout()
            descLabel = QLabel(template_desc)
            descLabel.setStyleSheet("font-size: 13px; color: #666666; border: none; background: transparent;")
            descLabel.setWordWrap(True)
            descLayout.addWidget(descLabel)
            
            tag = QLabel("云端")
            tag.setStyleSheet("""
                QLabel {
                    background-color: #E3F7EA;
                    color: #16A34A;
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-size: 10px;
                    font-weight: bold;
                    border: none;
                }
            """)
            descLayout.addWidget(tag)
            descLayout.addStretch()
            cardLayout.addLayout(descLayout)
            
            # 分隔线
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setStyleSheet("background-color: #F3F4F6; border: none; height: 1px;")
            cardLayout.addWidget(separator)
            
            # 提示词内容（可编辑的 QTextEdit）
            self.promptEdit = QTextEdit()
            self.promptEdit.setPlainText(prompt_text)
            self.promptEdit.setReadOnly(True)
            self.promptEdit.setStyleSheet("""
                QTextEdit {
                    background-color: #F9FAFB;
                    padding: 16px;
                    border-radius: 8px;
                    font-size: 13px;
                    color: #374151;
                    font-family: Consolas, monospace;
                    border: 1px solid #E5E7EB;
                }
                QTextEdit:focus {
                    border: 1px solid #16A34A;
                }
            """)
            cardLayout.addWidget(self.promptEdit)
            
            # 底部保存按钮（默认隐藏）
            self.saveBtnLayout = QHBoxLayout()
            self.saveBtnLayout.addStretch()
            
            cancelSaveBtn = QPushButton("取消")
            cancelSaveBtn.setCursor(Qt.PointingHandCursor)
            cancelSaveBtn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #374151;
                    padding: 10px 20px;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #F9FAFB;
                }
            """)
            cancelSaveBtn.clicked.connect(self.cancelEdit)
            self.saveBtnLayout.addWidget(cancelSaveBtn)
            
            saveBtn = QPushButton("保存修改")
            saveBtn.setCursor(Qt.PointingHandCursor)
            saveBtn.setStyleSheet("""
                QPushButton {
                    background-color: #16A34A;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #15803D;
                }
            """)
            saveBtn.clicked.connect(self.saveEdit)
            self.saveBtnLayout.addWidget(saveBtn)
            
            self.saveBtnWidget = QWidget()
            self.saveBtnWidget.setLayout(self.saveBtnLayout)
            self.saveBtnWidget.setVisible(False)
            cardLayout.addWidget(self.saveBtnWidget)
            
            overlayLayout.addWidget(card)
            mainLayout.addWidget(overlay)
        
        def toggleEdit(self):
            """切换编辑模式"""
            self.is_editing = not self.is_editing
            if self.is_editing:
                self.promptEdit.setReadOnly(False)
                self.promptEdit.setStyleSheet("""
                    QTextEdit {
                        background-color: white;
                        padding: 16px;
                        border-radius: 8px;
                        font-size: 13px;
                        color: #374151;
                        font-family: Consolas, monospace;
                        border: 2px solid #16A34A;
                    }
                """)
                self.editBtn.setText("👁 预览")
                self.saveBtnWidget.setVisible(True)
            else:
                self.promptEdit.setReadOnly(True)
                self.promptEdit.setStyleSheet("""
                    QTextEdit {
                        background-color: #F9FAFB;
                        padding: 16px;
                        border-radius: 8px;
                        font-size: 13px;
                        color: #374151;
                        font-family: Consolas, monospace;
                        border: 1px solid #E5E7EB;
                    }
                """)
                self.editBtn.setText("✏️ 修改")
                self.saveBtnWidget.setVisible(False)
        
        def cancelEdit(self):
            """取消编辑"""
            self.is_editing = False
            self.promptEdit.setReadOnly(True)
            self.promptEdit.setStyleSheet("""
                QTextEdit {
                    background-color: #F9FAFB;
                    padding: 16px;
                    border-radius: 8px;
                    font-size: 13px;
                    color: #374151;
                    font-family: Consolas, monospace;
                    border: 1px solid #E5E7EB;
                }
            """)
            self.editBtn.setText("✏️ 修改")
            self.saveBtnWidget.setVisible(False)
        
        def saveEdit(self):
            """保存修改"""
            new_content = self.promptEdit.toPlainText()
            self.prompt_updated.emit(self.template_index, new_content)
            
            # 切换回预览模式
            self.is_editing = False
            self.promptEdit.setReadOnly(True)
            self.promptEdit.setStyleSheet("""
                QTextEdit {
                    background-color: #F9FAFB;
                    padding: 16px;
                    border-radius: 8px;
                    font-size: 13px;
                    color: #374151;
                    font-family: Consolas, monospace;
                    border: 1px solid #E5E7EB;
                }
            """)
            self.editBtn.setText("✏️ 修改")
            self.saveBtnWidget.setVisible(False)
            
            InfoBar.success(
                title="保存成功",
                content="模板提示词已更新",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        
        def mousePressEvent(self, event):
            # 点击遮罩关闭
            if event.pos().x() < 50 or event.pos().x() > self.width() - 50 or \
               event.pos().y() < 50 or event.pos().y() > self.height() - 50:
                self.close()
            super().mousePressEvent(event)
    
    class CreateTemplateDialog(QDialog):
        """创建模板弹窗（4.2）"""
        template_created = pyqtSignal(dict)  # 模板创建信号
        
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setModal(True)
            
            # 主布局
            mainLayout = QHBoxLayout(self)
            mainLayout.setContentsMargins(0, 0, 0, 0)
            
            # 半透明遮罩
            overlay = QWidget()
            overlay.setStyleSheet("background-color: rgba(0, 0, 0, 100);")
            overlayLayout = QVBoxLayout(overlay)
            overlayLayout.setAlignment(Qt.AlignCenter)
            
            # 弹窗卡片
            card = QFrame()
            card.setFixedSize(750, 720)
            card.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 16px;
                    border: 1px solid #ECECEC;
                }
            """)
            cardLayout = QVBoxLayout(card)
            cardLayout.setContentsMargins(24, 24, 24, 24)
            cardLayout.setSpacing(16)
            
            # 头部
            headerLayout = QHBoxLayout()
            titleLabel = QLabel("创建模板")
            titleLabel.setStyleSheet("font-size: 18px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            headerLayout.addWidget(titleLabel)
            headerLayout.addStretch()
            
            closeBtn = QPushButton("✕")
            closeBtn.setFixedSize(32, 32)
            closeBtn.setCursor(Qt.PointingHandCursor)
            closeBtn.setStyleSheet("""
                QPushButton {
                    background-color: #F3F4F6;
                    border: none;
                    border-radius: 16px;
                    font-size: 16px;
                    color: #666666;
                }
                QPushButton:hover {
                    background-color: #E5E7EB;
                }
            """)
            closeBtn.clicked.connect(self.close)
            headerLayout.addWidget(closeBtn)
            cardLayout.addLayout(headerLayout)
            
            # 副标题
            subtitleLabel = QLabel("支持 Markdown 格式，AI 将参考此结构生成报告内容")
            subtitleLabel.setStyleSheet("font-size: 13px; color: #666666; border: none; background: transparent;")
            cardLayout.addWidget(subtitleLabel)
            
            # 模板名称
            nameLabel = QLabel("模板名称")
            nameLabel.setStyleSheet("font-size: 14px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            cardLayout.addWidget(nameLabel)
            
            self.nameInput = QLineEdit()
            self.nameInput.setPlaceholderText("输入模板名称")
            self.nameInput.setStyleSheet("""
                QLineEdit {
                    padding: 10px 12px;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                    font-size: 13px;
                    color: #1a1a1a;
                    background-color: white;
                }
                QLineEdit:focus {
                    border: 1px solid #16A34A;
                }
            """)
            cardLayout.addWidget(self.nameInput)
            
            # 模板简介
            introLabel = QLabel("模板简介")
            introLabel.setStyleSheet("font-size: 14px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            cardLayout.addWidget(introLabel)
            
            self.introInput = QLineEdit()
            self.introInput.setPlaceholderText("简短描述模板用途，如：适合向领导汇报的简洁日报")
            self.introInput.setStyleSheet("""
                QLineEdit {
                    padding: 10px 12px;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                    font-size: 13px;
                    color: #1a1a1a;
                    background-color: white;
                }
                QLineEdit:focus {
                    border: 1px solid #16A34A;
                }
            """)
            cardLayout.addWidget(self.introInput)
            
            # 模板正文
            bodyLabel = QLabel("模板正文")
            bodyLabel.setStyleSheet("font-size: 14px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            cardLayout.addWidget(bodyLabel)
            
            self.bodyInput = QTextEdit()
            self.bodyInput.setPlaceholderText("## 周报 [日期]\n\n### 本周完成\n- [工作项]\n\n### 下周计划\n- [计划项]")
            self.bodyInput.setMinimumHeight(150)
            self.bodyInput.setStyleSheet("""
                QTextEdit {
                    padding: 10px 12px;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                    font-size: 13px;
                    color: #1a1a1a;
                    background-color: white;
                    font-family: Consolas, monospace;
                }
                QTextEdit:focus {
                    border: 1px solid #16A34A;
                }
            """)
            cardLayout.addWidget(self.bodyInput)
            
            bodyHint = QLabel("支持 Markdown 格式，AI 将参考此结构生成报告内容")
            bodyHint.setStyleSheet("font-size: 11px; color: #9CA3AF; border: none; background: transparent;")
            cardLayout.addWidget(bodyHint)
            
            # 自定义指令
            instrLabel = QLabel("自定义指令")
            instrLabel.setStyleSheet("font-size: 14px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            cardLayout.addWidget(instrLabel)
            
            self.instrInput = QTextEdit()
            self.instrInput.setPlaceholderText("例如：用表格输出耗时，结尾补充风险和明日计划，语气保持简洁")
            self.instrInput.setMinimumHeight(80)
            self.instrInput.setStyleSheet("""
                QTextEdit {
                    padding: 10px 12px;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                    font-size: 13px;
                    color: #1a1a1a;
                    background-color: white;
                }
                QTextEdit:focus {
                    border: 1px solid #16A34A;
                }
            """)
            cardLayout.addWidget(self.instrInput)
            
            instrHint = QLabel("写模板固定的输出要求，会随该模板一起保存；生成时还可以叠加本次自定义指令")
            instrHint.setStyleSheet("font-size: 11px; color: #9CA3AF; border: none; background: transparent;")
            cardLayout.addWidget(instrHint)
            
            cardLayout.addStretch()
            
            # 底部按钮
            btnLayout = QHBoxLayout()
            btnLayout.addStretch()
            
            cancelBtn = QPushButton("取消")
            cancelBtn.setCursor(Qt.PointingHandCursor)
            cancelBtn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #374151;
                    padding: 10px 20px;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #F9FAFB;
                }
            """)
            cancelBtn.clicked.connect(self.close)
            btnLayout.addWidget(cancelBtn)
            
            saveBtn = QPushButton("保存模板")
            saveBtn.setCursor(Qt.PointingHandCursor)
            saveBtn.setStyleSheet("""
                QPushButton {
                    background-color: #16A34A;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #15803D;
                }
            """)
            saveBtn.clicked.connect(self.saveTemplate)
            btnLayout.addWidget(saveBtn)
            
            cardLayout.addLayout(btnLayout)
            
            overlayLayout.addWidget(card)
            mainLayout.addWidget(overlay)
        
        def saveTemplate(self):
            name = self.nameInput.text().strip()
            intro = self.introInput.text().strip()
            body = self.bodyInput.toPlainText().strip()
            if not name:
                return
            template = {
                "name": name,
                "intro": intro if intro else body[:30] + "..." if len(body) > 30 else body,
                "desc": body[:50] + "..." if len(body) > 50 else body,
                "is_cloud": False,
                "prompt": body
            }
            self.template_created.emit(template)
            self.close()
    
    class GenerateConfirmDialog(QDialog):
        """生成报告确认弹窗（4.3）"""
        stay_here = pyqtSignal()  # 留在此页信号
        go_history = pyqtSignal()  # 查看历史报告信号
        
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setModal(True)
            
            # 主布局
            mainLayout = QHBoxLayout(self)
            mainLayout.setContentsMargins(0, 0, 0, 0)
            
            # 半透明遮罩
            overlay = QWidget()
            overlay.setStyleSheet("background-color: rgba(0, 0, 0, 100);")
            overlayLayout = QVBoxLayout(overlay)
            overlayLayout.setAlignment(Qt.AlignCenter)
            
            # 弹窗卡片
            card = QFrame()
            card.setFixedSize(450, 220)
            card.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 16px;
                    border: 1px solid #ECECEC;
                }
            """)
            cardLayout = QVBoxLayout(card)
            cardLayout.setContentsMargins(24, 24, 24, 24)
            cardLayout.setSpacing(16)
            
            # 标题
            titleLabel = QLabel("报告正在生成中")
            titleLabel.setStyleSheet("font-size: 18px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            cardLayout.addWidget(titleLabel)
            
            # 描述
            descLabel = QLabel("已提交报告生成任务，AI 正在为你撰写报告。\n是否跳转到历史报告页面查看进度？")
            descLabel.setStyleSheet("font-size: 13px; color: #666666; border: none; background: transparent;")
            descLabel.setWordWrap(True)
            cardLayout.addWidget(descLabel)
            
            cardLayout.addStretch()
            
            # 底部按钮
            btnLayout = QHBoxLayout()
            btnLayout.addStretch()
            
            stayBtn = QPushButton("留在此页")
            stayBtn.setCursor(Qt.PointingHandCursor)
            stayBtn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #374151;
                    padding: 10px 20px;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #F9FAFB;
                }
            """)
            stayBtn.clicked.connect(self.onStay)
            btnLayout.addWidget(stayBtn)
            
            goBtn = QPushButton("查看历史报告")
            goBtn.setCursor(Qt.PointingHandCursor)
            goBtn.setStyleSheet("""
                QPushButton {
                    background-color: #16A34A;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #15803D;
                }
            """)
            goBtn.clicked.connect(self.onGoHistory)
            btnLayout.addWidget(goBtn)
            
            cardLayout.addLayout(btnLayout)
            
            overlayLayout.addWidget(card)
            mainLayout.addWidget(overlay)
        
        def onStay(self):
            self.stay_here.emit()
            self.close()
        
        def onGoHistory(self):
            self.go_history.emit()
            self.close()
    
    class ReportResultDialog(QDialog):
        """报告生成结果弹窗（4.4）- 支持流式输出"""
        def __init__(self, report_type, date_range, template_name, template_prompt, parent=None):
            super().__init__(parent)
            self.report_type = report_type
            self.date_range = date_range
            self.template_name = template_name
            self.template_prompt = template_prompt
            self.is_generating = True
            self.full_content = ""
            
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setModal(True)
            
            # 主布局
            mainLayout = QHBoxLayout(self)
            mainLayout.setContentsMargins(0, 0, 0, 0)
            
            # 半透明遮罩
            overlay = QWidget()
            overlay.setStyleSheet("background-color: rgba(0, 0, 0, 100);")
            overlayLayout = QVBoxLayout(overlay)
            overlayLayout.setAlignment(Qt.AlignCenter)
            
            # 弹窗卡片（接近全屏）
            card = QFrame()
            card.setMinimumSize(900, 700)
            card.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 16px;
                    border: 1px solid #ECECEC;
                }
            """)
            cardLayout = QVBoxLayout(card)
            cardLayout.setContentsMargins(24, 24, 24, 24)
            cardLayout.setSpacing(16)
            
            # 头部
            headerLayout = QHBoxLayout()
            
            self.titleLabel = QLabel(f"{report_type}报告正在生成中...")
            self.titleLabel.setStyleSheet("font-size: 18px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            headerLayout.addWidget(self.titleLabel)
            
            self.statusTag = QLabel("生成中")
            self.statusTag.setStyleSheet("""
                QLabel {
                    color: #F59E0B;
                    font-size: 13px;
                    font-weight: bold;
                    border: none;
                    background: transparent;
                }
            """)
            headerLayout.addWidget(self.statusTag)
            headerLayout.addStretch()
            
            closeBtn = QPushButton("✕")
            closeBtn.setFixedSize(32, 32)
            closeBtn.setCursor(Qt.PointingHandCursor)
            closeBtn.setStyleSheet("""
                QPushButton {
                    background-color: #F3F4F6;
                    border: none;
                    border-radius: 16px;
                    font-size: 16px;
                    color: #666666;
                }
                QPushButton:hover {
                    background-color: #E5E7EB;
                }
            """)
            closeBtn.clicked.connect(self.close)
            headerLayout.addWidget(closeBtn)
            cardLayout.addLayout(headerLayout)
            
            # 副标题
            self.subtitleLabel = QLabel(f"工作{report_type} — {date_range}")
            self.subtitleLabel.setStyleSheet("font-size: 13px; color: #666666; border: none; background: transparent;")
            cardLayout.addWidget(self.subtitleLabel)
            
            # 分隔线
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setStyleSheet("background-color: #F3F4F6; border: none; height: 1px;")
            cardLayout.addWidget(separator)
            
            # 报告内容区域
            self.contentEdit = QTextEdit()
            self.contentEdit.setReadOnly(True)
            self.contentEdit.setStyleSheet("""
                QTextEdit {
                    font-size: 14px;
                    color: #374151;
                    border: none;
                    background: transparent;
                    padding: 16px;
                    font-family: "Microsoft YaHei", sans-serif;
                }
            """)
            cardLayout.addWidget(self.contentEdit)
            
            # 分隔线
            separator2 = QFrame()
            separator2.setFrameShape(QFrame.HLine)
            separator2.setStyleSheet("background-color: #F3F4F6; border: none; height: 1px;")
            cardLayout.addWidget(separator2)
            
            # 底部栏
            footerLayout = QHBoxLayout()
            
            self.infoLabel = QLabel(f"模板：{template_name} · 0 字")
            self.infoLabel.setStyleSheet("font-size: 12px; color: #9CA3AF; border: none; background: transparent;")
            footerLayout.addWidget(self.infoLabel)
            footerLayout.addStretch()
            
            # 操作按钮
            self.actionBtns = {}
            for icon, text, name in [("📋", "复制", "copy"), ("📥", "导出", "export"), ("🔄", "重新生成", "regenerate")]:
                btn = QPushButton(f"{icon} {text}")
                btn.setCursor(Qt.PointingHandCursor)
                btn.setEnabled(False)  # 生成完成前禁用
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: white;
                        color: #374151;
                        padding: 8px 16px;
                        border: 1px solid #E5E7EB;
                        border-radius: 8px;
                        font-size: 12px;
                        border: none;
                    }
                    QPushButton:hover {
                        background-color: #F9FAFB;
                    }
                    QPushButton:disabled {
                        color: #9CA3AF;
                        background-color: #F3F4F6;
                    }
                """)
                if name == "copy":
                    btn.clicked.connect(self.copyContent)
                elif name == "export":
                    btn.clicked.connect(self.exportContent)
                elif name == "regenerate":
                    btn.clicked.connect(self.regenerate)
                self.actionBtns[name] = btn
                footerLayout.addWidget(btn)
            
            cardLayout.addLayout(footerLayout)
            
            overlayLayout.addWidget(card)
            mainLayout.addWidget(overlay)
            
            # 启动生成
            self.startGeneration()
        
        def startGeneration(self):
            """启动报告生成"""
            # 解析日期范围
            dates = self.date_range.split(" 至 ")
            start_date = dates[0]
            end_date = dates[1] if len(dates) > 1 else start_date
            
            # 创建工作线程
            self.worker = ReportGenerateWorker(
                self.template_prompt,
                start_date,
                end_date,
                self.report_type
            )
            
            # 连接信号
            self.worker.chunk_received.connect(self.onChunkReceived)
            self.worker.generation_finished.connect(self.onGenerationFinished)
            self.worker.generation_error.connect(self.onGenerationError)
            
            # 启动线程
            self.worker.start()
        
        def onChunkReceived(self, chunk):
            """接收到一块内容"""
            self.full_content += chunk
            self.contentEdit.setPlainText(self.full_content)
            # 滚动到底部
            self.contentEdit.verticalScrollBar().setValue(
                self.contentEdit.verticalScrollBar().maximum()
            )
            # 更新字数
            self.infoLabel.setText(f"模板：{self.template_name} · {len(self.full_content)} 字")
        
        def onGenerationFinished(self, content):
            """生成完成"""
            self.is_generating = False
            self.full_content = content
            self.contentEdit.setPlainText(content)
            
            # 更新UI
            self.titleLabel.setText(f"{self.report_type}报告生成完成")
            self.statusTag.setText("已完成")
            self.statusTag.setStyleSheet("""
                QLabel {
                    color: #16A34A;
                    font-size: 13px;
                    font-weight: bold;
                    border: none;
                    background: transparent;
                }
            """)
            
            # 启用操作按钮
            for btn in self.actionBtns.values():
                btn.setEnabled(True)
            
            # 更新字数
            self.infoLabel.setText(f"模板：{self.template_name} · {len(content)} 字")
        
        def onGenerationError(self, error):
            """生成出错"""
            self.is_generating = False
            self.contentEdit.setPlainText(f"生成失败: {error}")
            
            self.titleLabel.setText(f"{self.report_type}报告生成失败")
            self.statusTag.setText("失败")
            self.statusTag.setStyleSheet("""
                QLabel {
                    color: #EF4444;
                    font-size: 13px;
                    font-weight: bold;
                    border: none;
                    background: transparent;
                }
            """)
        
        def copyContent(self):
            """复制内容"""
            QApplication.clipboard().setText(self.full_content)
            InfoBar.success(
                title="复制成功",
                content="报告内容已复制到剪贴板",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        
        def exportContent(self):
            """导出内容"""
            from PyQt5.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出报告", f"{self.report_type}报告_{self.date_range.replace('至', '-').strip()}.md",
                "Markdown Files (*.md);;Text Files (*.txt);;All Files (*)"
            )
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.full_content)
                InfoBar.success(
                    title="导出成功",
                    content=f"报告已保存到: {file_path}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
        
        def regenerate(self):
            """重新生成"""
            self.full_content = ""
            self.contentEdit.clear()
            self.is_generating = True
            self.titleLabel.setText(f"{self.report_type}报告正在生成中...")
            self.statusTag.setText("生成中")
            self.statusTag.setStyleSheet("""
                QLabel {
                    color: #F59E0B;
                    font-size: 13px;
                    font-weight: bold;
                    border: none;
                    background: transparent;
                }
            """)
            for btn in self.actionBtns.values():
                btn.setEnabled(False)
            self.startGeneration()
    
    class ReportPage(QWidget):
        """生成报告页面"""
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setObjectName("reportPage")
            self.selected_template_index = 2  # 默认选中AI工作轨迹日报
            self.template_cards = []
            
            # 主布局
            mainLayout = QVBoxLayout(self)
            mainLayout.setContentsMargins(0, 0, 0, 0)
            mainLayout.setSpacing(0)
            
            # 滚动区域
            scrollArea = QScrollArea()
            scrollArea.setWidgetResizable(True)
            scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scrollArea.setStyleSheet("QScrollArea { border: none; background-color: #F7F8F7; }")
            
            contentWidget = QWidget()
            contentWidget.setStyleSheet("background-color: #F7F8F7; border: none;")
            layout = QVBoxLayout(contentWidget)
            layout.setContentsMargins(32, 24, 32, 24)
            layout.setSpacing(24)
            
            # ========== 顶部标题栏 ==========
            headerCard = QFrame()
            headerCard.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 16px;
                    border: 1px solid #ECECEC;
                }
            """)
            headerLayout = QHBoxLayout(headerCard)
            headerLayout.setContentsMargins(24, 20, 24, 20)
            headerLayout.setSpacing(16)
            
            # 左侧标题
            titleLeftLayout = QVBoxLayout()
            titleTopLayout = QHBoxLayout()
            
            iconLabel = QLabel("✨")
            iconLabel.setFixedSize(32, 32)
            iconLabel.setAlignment(Qt.AlignCenter)
            iconLabel.setStyleSheet("""
                QLabel {
                    background-color: #F0FBF4;
                    border-radius: 8px;
                    font-size: 18px;
                    border: none;
                }
            """)
            titleTopLayout.addWidget(iconLabel)
            
            titleLabel = QLabel("报告配置")
            titleLabel.setStyleSheet("font-size: 22px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            titleTopLayout.addWidget(titleLabel)
            titleTopLayout.addStretch()
            titleLeftLayout.addLayout(titleTopLayout)
            
            subtitleLabel = QLabel("配置参数后点击生成，AI 将基于工作记录自动撰写报告")
            subtitleLabel.setStyleSheet("font-size: 13px; color: #666666; border: none; background: transparent;")
            titleLeftLayout.addWidget(subtitleLabel)
            
            headerLayout.addLayout(titleLeftLayout, 1)
            
            # 右侧按钮
            btnLayout = QHBoxLayout()
            btnLayout.setSpacing(12)
            
            # 自定义指令按钮（带角标）
            instrBtnContainer = QWidget()
            instrBtnContainer.setStyleSheet("border: none; background: transparent;")
            instrBtnLayout = QVBoxLayout(instrBtnContainer)
            instrBtnLayout.setContentsMargins(0, 0, 0, 0)
            
            instrBtn = QPushButton("💬 自定义指令")
            instrBtn.setCursor(Qt.PointingHandCursor)
            instrBtn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #374151;
                    padding: 10px 20px;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #F9FAFB;
                }
            """)
            instrBtnLayout.addWidget(instrBtn)
            
            # 建议填写角标
            badge = QLabel("建议填写")
            badge.setFixedSize(60, 20)
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet("""
                QLabel {
                    background-color: #16A34A;
                    color: white;
                    padding: 2px 6px;
                    border-radius: 10px;
                    font-size: 10px;
                    font-weight: bold;
                    border: none;
                }
            """)
            badge.setParent(instrBtn)
            badge.move(instrBtn.width() - 50, -8)
            
            btnLayout.addWidget(instrBtnContainer)
            
            # 开始生成按钮
            generateBtn = QPushButton("✨ 开始生成报告")
            generateBtn.setCursor(Qt.PointingHandCursor)
            generateBtn.setStyleSheet("""
                QPushButton {
                    background-color: #16A34A;
                    color: white;
                    padding: 10px 24px;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #15803D;
                }
            """)
            generateBtn.clicked.connect(self.onGenerate)
            btnLayout.addWidget(generateBtn)
            
            headerLayout.addLayout(btnLayout)
            layout.addWidget(headerCard)
            
            # ========== 主体两栏布局 ==========
            bodyLayout = QHBoxLayout()
            bodyLayout.setSpacing(24)
            
            # 左栏
            leftLayout = QVBoxLayout()
            leftLayout.setSpacing(24)
            
            # 左栏第一张卡片：报告类型 + 时间范围
            typeCard = QFrame()
            typeCard.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 16px;
                    border: 1px solid #ECECEC;
                }
            """)
            typeCardLayout = QHBoxLayout(typeCard)
            typeCardLayout.setContentsMargins(24, 20, 24, 20)
            typeCardLayout.setSpacing(32)
            
            # 左块：报告类型
            reportTypeLayout = QVBoxLayout()
            reportTypeLayout.setSpacing(12)
            
            reportTypeTitle = QLabel("报告类型")
            reportTypeTitle.setStyleSheet("font-size: 15px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            reportTypeLayout.addWidget(reportTypeTitle)
            
            reportTypeDesc = QLabel("选择要生成的报告周期")
            reportTypeDesc.setStyleSheet("font-size: 12px; color: #666666; border: none; background: transparent;")
            reportTypeLayout.addWidget(reportTypeDesc)
            
            # 分段选择按钮
            self.typeButtons = []
            typeBtnLayout = QHBoxLayout()
            typeBtnLayout.setSpacing(8)
            
            for i, (text, days) in enumerate([("日报", 0), ("周报", 7), ("月报", 30)]):
                btn = QPushButton(text)
                btn.setCheckable(True)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setMinimumHeight(36)
                btn.setProperty("days", days)
                btn.clicked.connect(lambda checked, idx=i: self.selectReportType(idx))
                
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: white;
                        color: #374151;
                        padding: 8px 20px;
                        border: 1px solid #E5E7EB;
                        border-radius: 8px;
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QPushButton:checked {
                        background-color: #F0FBF4;
                        color: #16A34A;
                        border: 1px solid #16A34A;
                    }
                    QPushButton:hover {
                        background-color: #F9FAFB;
                    }
                """)
                self.typeButtons.append(btn)
                typeBtnLayout.addWidget(btn)
            
            self.typeButtons[0].setChecked(True)
            reportTypeLayout.addLayout(typeBtnLayout)
            reportTypeLayout.addStretch()
            
            typeCardLayout.addLayout(reportTypeLayout, 1)
            
            # 分隔线
            typeSep = QFrame()
            typeSep.setFrameShape(QFrame.VLine)
            typeSep.setStyleSheet("background-color: #F3F4F6; border: none; width: 1px;")
            typeCardLayout.addWidget(typeSep)
            
            # 右块：时间范围
            timeRangeLayout = QVBoxLayout()
            timeRangeLayout.setSpacing(12)
            
            timeRangeTitle = QLabel("时间范围")
            timeRangeTitle.setStyleSheet("font-size: 15px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            timeRangeLayout.addWidget(timeRangeTitle)
            
            timeRangeDesc = QLabel("默认根据报告类型确定，可手动修改")
            timeRangeDesc.setStyleSheet("font-size: 12px; color: #666666; border: none; background: transparent;")
            timeRangeLayout.addWidget(timeRangeDesc)
            
            # 日期选择器（使用 Fluent CalendarPicker）
            dateLayout = QHBoxLayout()
            dateLayout.setSpacing(12)
            
            self.startDateEdit = CalendarPicker()
            self.startDateEdit.setDate(QDate.currentDate())
            self.startDateEdit.setDateFormat("yyyy/MM/dd")
            self.startDateEdit.setFixedWidth(140)
            self.startDateEdit.dateChanged.connect(self.updatePreviewDate)
            dateLayout.addWidget(self.startDateEdit)
            
            toLabel = QLabel("至")
            toLabel.setStyleSheet("font-size: 13px; color: #666666; border: none; background: transparent;")
            dateLayout.addWidget(toLabel)
            
            self.endDateEdit = CalendarPicker()
            self.endDateEdit.setDate(QDate.currentDate())
            self.endDateEdit.setDateFormat("yyyy/MM/dd")
            self.endDateEdit.setFixedWidth(140)
            self.endDateEdit.dateChanged.connect(self.updatePreviewDate)
            dateLayout.addWidget(self.endDateEdit)
            
            timeRangeLayout.addLayout(dateLayout)
            timeRangeLayout.addStretch()
            
            typeCardLayout.addLayout(timeRangeLayout, 1)
            
            leftLayout.addWidget(typeCard)
            
            # 左栏第二张卡片：选择报告模板
            templateCard = QFrame()
            templateCard.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 16px;
                    border: 1px solid #ECECEC;
                }
            """)
            templateCardLayout = QVBoxLayout(templateCard)
            templateCardLayout.setContentsMargins(24, 20, 24, 20)
            templateCardLayout.setSpacing(16)
            
            # 卡片头部
            templateHeaderLayout = QHBoxLayout()
            
            templateIcon = QLabel("📄")
            templateIcon.setFixedSize(28, 28)
            templateIcon.setAlignment(Qt.AlignCenter)
            templateIcon.setStyleSheet("""
                QLabel {
                    background-color: #F0FBF4;
                    border-radius: 6px;
                    font-size: 14px;
                    border: none;
                }
            """)
            templateHeaderLayout.addWidget(templateIcon)
            
            templateTitle = QLabel("选择报告模板")
            templateTitle.setStyleSheet("font-size: 15px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            templateHeaderLayout.addWidget(templateTitle)
            templateHeaderLayout.addStretch()
            
            # 导入模板按钮
            importBtn = QPushButton("📥 导入模板")
            importBtn.setCursor(Qt.PointingHandCursor)
            importBtn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #374151;
                    padding: 8px 16px;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                    font-size: 12px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #F9FAFB;
                }
            """)
            importBtn.clicked.connect(self.onImportTemplate)
            templateHeaderLayout.addWidget(importBtn)
            
            # 导出模板按钮
            exportBtn = QPushButton("📤 导出模板")
            exportBtn.setCursor(Qt.PointingHandCursor)
            exportBtn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #374151;
                    padding: 8px 16px;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                    font-size: 12px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #F9FAFB;
                }
            """)
            exportBtn.clicked.connect(self.onExportTemplate)
            templateHeaderLayout.addWidget(exportBtn)
            
            # 创建模板按钮
            createBtn = QPushButton("＋ 创建模板")
            createBtn.setCursor(Qt.PointingHandCursor)
            createBtn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #374151;
                    padding: 8px 16px;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                    font-size: 12px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #F9FAFB;
                }
            """)
            createBtn.clicked.connect(self.onCreateTemplate)
            templateHeaderLayout.addWidget(createBtn)
            
            templateCardLayout.addLayout(templateHeaderLayout)
            
            # 副标题
            templateSubtitle = QLabel("选择合适的模板，AI 将为你生成更贴合需求的报告")
            templateSubtitle.setStyleSheet("font-size: 12px; color: #666666; border: none; background: transparent;")
            templateCardLayout.addWidget(templateSubtitle)
            
            # 模板网格
            self.templateGrid = QGridLayout()
            self.templateGrid.setSpacing(16)
            
            for i, template in enumerate(REPORT_TEMPLATES):
                card = TemplateCard(i, template["name"], template.get("intro", template["desc"]), template.get("is_cloud", True))
                card.clicked.connect(self.selectTemplate)
                card.preview_clicked.connect(self.showTemplatePreview)
                card.delete_clicked.connect(self.deleteTemplate)
                self.template_cards.append(card)
                self.templateGrid.addWidget(card, i // 3, i % 3)
            
            templateCardLayout.addLayout(self.templateGrid)
            
            leftLayout.addWidget(templateCard)
            
            bodyLayout.addLayout(leftLayout, 7)
            
            # 右栏：模板预览
            previewCard = QFrame()
            previewCard.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 16px;
                    border: 1px solid #ECECEC;
                }
            """)
            previewCardLayout = QVBoxLayout(previewCard)
            previewCardLayout.setContentsMargins(24, 20, 24, 20)
            previewCardLayout.setSpacing(16)
            
            # 预览标题
            previewTitle = QLabel("模板预览")
            previewTitle.setStyleSheet("font-size: 15px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            previewCardLayout.addWidget(previewTitle)
            
            # 预览头部
            previewHeaderLayout = QHBoxLayout()
            
            previewIcon = QLabel("📄")
            previewIcon.setFixedSize(32, 32)
            previewIcon.setAlignment(Qt.AlignCenter)
            previewIcon.setStyleSheet("""
                QLabel {
                    background-color: #F0FBF4;
                    border-radius: 8px;
                    font-size: 16px;
                    border: none;
                }
            """)
            previewHeaderLayout.addWidget(previewIcon)
            
            previewInfoLayout = QVBoxLayout()
            previewNameLayout = QHBoxLayout()
            self.previewNameLabel = QLabel(REPORT_TEMPLATES[2]["name"])
            self.previewNameLabel.setStyleSheet("font-size: 15px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            previewNameLayout.addWidget(self.previewNameLabel)
            
            previewCloudTag = QLabel("云端")
            previewCloudTag.setStyleSheet("""
                QLabel {
                    background-color: #E3F7EA;
                    color: #16A34A;
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-size: 10px;
                    font-weight: bold;
                    border: none;
                }
            """)
            previewNameLayout.addWidget(previewCloudTag)
            previewNameLayout.addStretch()
            previewInfoLayout.addLayout(previewNameLayout)
            
            self.previewDateLabel = QLabel(f"时间范围：{QDate.currentDate().toString('yyyy-MM-dd')} 至 {QDate.currentDate().toString('yyyy-MM-dd')}")
            self.previewDateLabel.setStyleSheet("font-size: 12px; color: #666666; border: none; background: transparent;")
            previewInfoLayout.addWidget(self.previewDateLabel)
            
            previewHeaderLayout.addLayout(previewInfoLayout)
            previewCardLayout.addLayout(previewHeaderLayout)
            
            # 分隔线
            previewSep = QFrame()
            previewSep.setFrameShape(QFrame.HLine)
            previewSep.setStyleSheet("background-color: #F3F4F6; border: none; height: 1px;")
            previewCardLayout.addWidget(previewSep)
            
            # 预览内容区域
            self.previewContent = QLabel()
            self.previewContent.setWordWrap(True)
            self.previewContent.setStyleSheet("""
                QLabel {
                    background-color: #F9FAFB;
                    padding: 16px;
                    border-radius: 8px;
                    font-size: 13px;
                    color: #374151;
                    font-family: Consolas, monospace;
                    border: 1px solid #E5E7EB;
                }
            """)
            self.previewContent.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.previewContent.setMinimumHeight(300)
            
            previewScroll = QScrollArea()
            previewScroll.setWidget(self.previewContent)
            previewScroll.setWidgetResizable(True)
            previewScroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
            previewCardLayout.addWidget(previewScroll)
            
            # 底部提示
            previewHint = QLabel("实际内容将基于你的工作记录自动生成")
            previewHint.setStyleSheet("font-size: 11px; color: #9CA3AF; border: none; background: transparent;")
            previewHint.setAlignment(Qt.AlignCenter)
            previewCardLayout.addWidget(previewHint)
            
            bodyLayout.addWidget(previewCard, 3)
            
            layout.addLayout(bodyLayout)
            
            scrollArea.setWidget(contentWidget)
            mainLayout.addWidget(scrollArea)
            
            # 初始化
            self.selectReportType(0)
            self.selectTemplate(2)
        
        def selectReportType(self, index):
            """选择报告类型"""
            for i, btn in enumerate(self.typeButtons):
                btn.setChecked(i == index)
            
            today = QDate.currentDate()
            if index == 0:  # 日报
                self.startDateEdit.setDate(today)
                self.endDateEdit.setDate(today)
            elif index == 1:  # 周报
                monday = today.addDays(-(today.dayOfWeek() - 1))
                sunday = monday.addDays(6)
                self.startDateEdit.setDate(monday)
                self.endDateEdit.setDate(sunday)
            elif index == 2:  # 月报
                first = QDate(today.year(), today.month(), 1)
                last = first.addMonths(1).addDays(-1)
                self.startDateEdit.setDate(first)
                self.endDateEdit.setDate(last)
            
            self.updatePreviewDate()
        
        def selectTemplate(self, index):
            """选择模板"""
            self.selected_template_index = index
            for i, card in enumerate(self.template_cards):
                card.setSelected(i == index)
            
            template = REPORT_TEMPLATES[index]
            self.previewNameLabel.setText(template["name"])
            self.previewContent.setText(template["prompt"])
        
        def updatePreviewDate(self):
            """更新预览日期"""
            # 验证日期范围
            if self.startDateEdit.date > self.endDateEdit.date:
                InfoBar.warning(
                    title="日期范围错误",
                    content="开始日期不能晚于结束日期",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                return
            
            start = self.startDateEdit.date.toString("yyyy-MM-dd")
            end = self.endDateEdit.date.toString("yyyy-MM-dd")
            self.previewDateLabel.setText(f"时间范围：{start} 至 {end}")
        
        def showTemplatePreview(self, index):
            """显示模板预览弹窗"""
            template = REPORT_TEMPLATES[index]
            dialog = TemplatePreviewDialog(index, template["name"], template["desc"], template["prompt"], self)
            dialog.prompt_updated.connect(self.onPromptUpdated)
            dialog.exec_()
        
        def onPromptUpdated(self, index, new_content):
            """更新模板提示词"""
            REPORT_TEMPLATES[index]["prompt"] = new_content
            # 如果更新的是当前选中的模板，刷新预览
            if index == self.selected_template_index:
                self.previewContent.setText(new_content)
            # 保存到文件
            write_templates(REPORT_TEMPLATES)
        
        def onImportTemplate(self):
            """导入模板"""
            from PyQt5.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getOpenFileName(
                self, "导入模板", "",
                "CSV Files (*.csv);;All Files (*)"
            )
            if file_path:
                templates = import_templates(file_path)
                if templates:
                    # 添加导入的模板
                    for template in templates:
                        REPORT_TEMPLATES.append(template)
                        add_template(template)
                    
                    # 重建模板网格
                    self.rebuildTemplateGrid()
                    
                    InfoBar.success(
                        title="导入成功",
                        content=f"已导入 {len(templates)} 个模板",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                else:
                    InfoBar.error(
                        title="导入失败",
                        content="无法解析模板文件",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
        
        def onExportTemplate(self):
            """导出模板"""
            from PyQt5.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出模板", "report_templates.csv",
                "CSV Files (*.csv);;All Files (*)"
            )
            if file_path:
                if export_templates(file_path):
                    InfoBar.success(
                        title="导出成功",
                        content=f"模板已保存到: {file_path}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
                else:
                    InfoBar.error(
                        title="导出失败",
                        content="无法保存模板文件",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
        
        def onCreateTemplate(self):
            """打开创建模板弹窗"""
            dialog = CreateTemplateDialog(self)
            dialog.template_created.connect(self.addNewTemplate)
            dialog.exec_()
        
        def addNewTemplate(self, template):
            """添加新模板"""
            REPORT_TEMPLATES.append(template)
            add_template(template)  # 保存到文件
            
            # 重建模板网格
            self.rebuildTemplateGrid()
            
            InfoBar.success(
                title="创建成功",
                content=f"模板「{template['name']}」已添加",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        
        def rebuildTemplateGrid(self):
            """重建模板网格"""
            # 清空现有卡片
            for card in self.template_cards:
                card.deleteLater()
            self.template_cards.clear()
            
            # 清空网格
            while self.templateGrid.count():
                item = self.templateGrid.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # 重新创建模板卡片
            for i, template in enumerate(REPORT_TEMPLATES):
                card = TemplateCard(i, template["name"], template.get("intro", template["desc"]), template.get("is_cloud", True))
                card.clicked.connect(self.selectTemplate)
                card.preview_clicked.connect(self.showTemplatePreview)
                card.delete_clicked.connect(self.deleteTemplate)
                self.template_cards.append(card)
                self.templateGrid.addWidget(card, i // 3, i % 3)
        
        def deleteTemplate(self, index):
            """删除模板"""
            if len(REPORT_TEMPLATES) <= 1:
                InfoBar.warning(
                    title="无法删除",
                    content="至少需要保留一个模板",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
            
            template_name = REPORT_TEMPLATES[index]["name"]
            
            # 确认删除
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除模板「{template_name}」吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 从数据中删除
                REPORT_TEMPLATES.pop(index)
                delete_template(index)  # 保存到文件
                
                # 重建模板网格
                self.rebuildTemplateGrid()
                
                # 如果删除的是当前选中的模板，选中第一个
                if self.selected_template_index >= len(REPORT_TEMPLATES):
                    self.selected_template_index = 0
                
                self.selectTemplate(self.selected_template_index)
                
                InfoBar.success(
                    title="删除成功",
                    content=f"模板「{template_name}」已删除",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
        
        def onGenerate(self):
            """开始生成报告"""
            # 验证日期范围
            if self.startDateEdit.date > self.endDateEdit.date:
                InfoBar.warning(
                    title="日期范围错误",
                    content="开始日期不能晚于结束日期",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                return
            
            dialog = GenerateConfirmDialog(self)
            dialog.stay_here.connect(self.simulateGenerate)
            dialog.go_history.connect(self.goToHistory)
            dialog.exec_()
        
        def simulateGenerate(self):
            """生成报告"""
            report_type = "日报"
            for i, btn in enumerate(self.typeButtons):
                if btn.isChecked():
                    report_type = ["日报", "周报", "月报"][i]
                    break
            
            start = self.startDateEdit.date.toString("yyyy-MM-dd")
            end = self.endDateEdit.date.toString("yyyy-MM-dd")
            date_range = f"{start} 至 {end}"
            template_name = REPORT_TEMPLATES[self.selected_template_index]["name"]
            template_prompt = REPORT_TEMPLATES[self.selected_template_index]["prompt"]
            
            # 打开结果弹窗（会自动启动生成）
            dialog = ReportResultDialog(report_type, date_range, template_name, template_prompt, self)
            dialog.exec_()
        
        def goToHistory(self):
            """跳转到历史报告页面"""
            print("[跳转] 查看历史报告页面")

    # ==================== 设置页面 ====================
    
    class ConnectionTestWorker(QThread):
        """连接测试工作线程"""
        finished = pyqtSignal(bool, str)  # (success, message)
        
        def __init__(self, test_type, host=None, model=None):
            super().__init__()
            self.test_type = test_type
            self.host = host
            self.model = model
        
        def run(self):
            try:
                if self.test_type == "glm":
                    success, message = test_glm_connection()
                elif self.test_type == "ollama":
                    if self.host:
                        set_ollama_config(self.host, self.model)
                    success, message = test_ollama_connection()
                else:
                    success, message = False, "未知的测试类型"
                self.finished.emit(success, message)
            except Exception as e:
                self.finished.emit(False, str(e))

    class SettingsPage(QWidget):
        """设置页面"""
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setObjectName("settingsPage")
            self._test_worker = None
            
            scrollLayout = QVBoxLayout(self)
            scrollLayout.setContentsMargins(0, 0, 0, 0)
            
            scrollArea = QScrollArea()
            scrollArea.setWidgetResizable(True)
            scrollArea.setStyleSheet("QScrollArea { border: none; background-color: #F5F5F5; }")
            
            contentWidget = QWidget()
            contentWidget.setStyleSheet("background-color: #F5F5F5; border: none;")
            layout = QVBoxLayout(contentWidget)
            layout.setSpacing(15)
            layout.setContentsMargins(20, 15, 20, 15)
            
            # 页面标题
            title = QLabel("⚙️ 设置")
            title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            layout.addWidget(title)
            
            # ========== 显示缩放设置 ==========
            scaleCard = QFrame()
            scaleCard.setStyleSheet("QFrame { background-color: white; border-radius: 12px; border: none; }")
            scaleLayout = QVBoxLayout(scaleCard)
            scaleLayout.setContentsMargins(20, 18, 20, 18)
            scaleLayout.setSpacing(10)
            
            scaleTitle = QLabel("🖥️ 显示缩放")
            scaleTitle.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; border: none; background: transparent;")
            scaleLayout.addWidget(scaleTitle)
            
            scaleInfo = QLabel("界面缩放比例（修改后需重启程序生效）")
            scaleInfo.setStyleSheet("color: #888888; font-size: 11px; border: none; background: transparent;")
            scaleLayout.addWidget(scaleInfo)
            
            scaleComboLayout = QHBoxLayout()
            scaleLabel = QLabel("缩放比例:")
            scaleLabel.setStyleSheet("font-size: 12px; color: #333333; border: none; background: transparent;")
            scaleComboLayout.addWidget(scaleLabel)
            
            self.scaleCombo = ComboBox()
            self.scaleCombo.addItems(["25%", "50%", "75%", "100%", "125%", "150%", "175%", "200%"])
            self.scaleCombo.setCurrentText(f"{SCALE_FACTOR * 100:.0f}%")
            self.scaleCombo.currentTextChanged.connect(self.onScaleChanged)
            scaleComboLayout.addWidget(self.scaleCombo)
            scaleComboLayout.addStretch()
            
            scaleLayout.addLayout(scaleComboLayout)
            
            systemScaleLabel = QLabel(f"系统缩放: {get_system_dpi_scale() * 100:.0f}%")
            systemScaleLabel.setStyleSheet("color: #999999; font-size: 10px; border: none; background: transparent;")
            scaleLayout.addWidget(systemScaleLabel)
            
            layout.addWidget(scaleCard)
            
            # ========== 识别模型设置 ==========
            modelCard = QFrame()
            modelCard.setStyleSheet("QFrame { background-color: white; border-radius: 12px; border: none; }")
            modelLayout = QVBoxLayout(modelCard)
            modelLayout.setContentsMargins(20, 18, 20, 18)
            modelLayout.setSpacing(12)
            
            modelTitle = QLabel("🧠 识别模型")
            modelTitle.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; border: none; background: transparent;")
            modelLayout.addWidget(modelTitle)
            
            # 模型选择
            modelSelectLayout = QHBoxLayout()
            modelSelectLabel = QLabel("选择模型:")
            modelSelectLabel.setStyleSheet("font-size: 12px; color: #333333; border: none; background: transparent;")
            modelSelectLayout.addWidget(modelSelectLabel)
            
            self.modelCombo = ComboBox()
            self.modelCombo.addItems(["GLM 通用模型", "自定义 Ollama"])
            self.modelCombo.currentTextChanged.connect(self.onModelTypeChanged)
            modelSelectLayout.addWidget(self.modelCombo)
            modelSelectLayout.addStretch()
            
            modelLayout.addLayout(modelSelectLayout)
            
            # GLM设置区域
            self.glmWidget = QWidget()
            self.glmWidget.setStyleSheet("border: none; background: transparent;")
            glmLayout = QVBoxLayout(self.glmWidget)
            glmLayout.setContentsMargins(0, 5, 0, 0)
            glmLayout.setSpacing(8)
            
            glmInfo = QLabel("使用 GLM-4.6V-Flash 通用模型（无需本地部署）")
            glmInfo.setStyleSheet("color: #666666; font-size: 11px; border: none; background: transparent;")
            glmLayout.addWidget(glmInfo)
            
            glmTestBtnLayout = QHBoxLayout()
            self.glmTestBtn = QPushButton("🔗 测试 GLM 连接")
            self.glmTestBtn.setCursor(Qt.PointingHandCursor)
            self.glmTestBtn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-size: 12px;
                    border: none;
                }
                QPushButton:hover { background-color: #1976D2; }
                QPushButton:pressed { background-color: #1565C0; }
            """)
            self.glmTestBtn.clicked.connect(self.testGlmConnection)
            glmTestBtnLayout.addWidget(self.glmTestBtn)
            glmTestBtnLayout.addStretch()
            glmLayout.addLayout(glmTestBtnLayout)
            
            self.glmStatusLabel = QLabel("")
            self.glmStatusLabel.setStyleSheet("font-size: 11px; border: none; background: transparent;")
            glmLayout.addWidget(self.glmStatusLabel)
            
            modelLayout.addWidget(self.glmWidget)
            
            # Ollama设置区域
            self.ollamaWidget = QWidget()
            self.ollamaWidget.setStyleSheet("border: none; background: transparent;")
            ollamaLayout = QVBoxLayout(self.ollamaWidget)
            ollamaLayout.setContentsMargins(0, 5, 0, 0)
            ollamaLayout.setSpacing(10)
            
            ollamaHostLayout = QHBoxLayout()
            ollamaHostLabel = QLabel("服务器地址:")
            ollamaHostLabel.setStyleSheet("font-size: 12px; color: #333333; border: none; background: transparent;")
            ollamaHostLayout.addWidget(ollamaHostLabel)
            
            self.ollamaHostInput = QLineEdit()
            self.ollamaHostInput.setText("http://192.168.31.23:11434")
            self.ollamaHostInput.setPlaceholderText("http://192.168.31.23:11434")
            self.ollamaHostInput.setStyleSheet("""
                QLineEdit {
                    padding: 6px 10px;
                    border: 1px solid #E0E0E0;
                    border-radius: 6px;
                    font-size: 12px;
                    color: #333333;
                    background-color: white;
                }
                QLineEdit:focus { border: 1px solid #1976D2; }
            """)
            ollamaHostLayout.addWidget(self.ollamaHostInput)
            ollamaLayout.addLayout(ollamaHostLayout)
            
            ollamaModelLayout = QHBoxLayout()
            ollamaModelLabel = QLabel("模型名称:")
            ollamaModelLabel.setStyleSheet("font-size: 12px; color: #333333; border: none; background: transparent;")
            ollamaModelLayout.addWidget(ollamaModelLabel)
            
            self.ollamaModelInput = QLineEdit()
            self.ollamaModelInput.setText("minicpm-v4.6")
            self.ollamaModelInput.setPlaceholderText("minicpm-v4.6")
            self.ollamaModelInput.setStyleSheet("""
                QLineEdit {
                    padding: 6px 10px;
                    border: 1px solid #E0E0E0;
                    border-radius: 6px;
                    font-size: 12px;
                    color: #333333;
                    background-color: white;
                }
                QLineEdit:focus { border: 1px solid #1976D2; }
            """)
            ollamaModelLayout.addWidget(self.ollamaModelInput)
            ollamaLayout.addLayout(ollamaModelLayout)
            
            ollamaBtnLayout = QHBoxLayout()
            
            applyBtn = QPushButton("✅ 应用设置")
            applyBtn.setCursor(Qt.PointingHandCursor)
            applyBtn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-size: 12px;
                    border: none;
                }
                QPushButton:hover { background-color: #43A047; }
                QPushButton:pressed { background-color: #388E3C; }
            """)
            applyBtn.clicked.connect(self.applyOllamaSettings)
            ollamaBtnLayout.addWidget(applyBtn)
            
            self.ollamaTestBtn = QPushButton("🔗 测试 Ollama 连接")
            self.ollamaTestBtn.setCursor(Qt.PointingHandCursor)
            self.ollamaTestBtn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-size: 12px;
                    border: none;
                }
                QPushButton:hover { background-color: #1976D2; }
                QPushButton:pressed { background-color: #1565C0; }
            """)
            self.ollamaTestBtn.clicked.connect(self.testOllamaConnection)
            ollamaBtnLayout.addWidget(self.ollamaTestBtn)
            ollamaBtnLayout.addStretch()
            ollamaLayout.addLayout(ollamaBtnLayout)
            
            self.ollamaStatusLabel = QLabel("")
            self.ollamaStatusLabel.setStyleSheet("font-size: 11px; border: none; background: transparent;")
            ollamaLayout.addWidget(self.ollamaStatusLabel)
            
            modelLayout.addWidget(self.ollamaWidget)
            
            layout.addWidget(modelCard)
            
            # ========== 测试模式 ==========
            testCard = QFrame()
            testCard.setStyleSheet("QFrame { background-color: white; border-radius: 12px; border: none; }")
            testLayout = QVBoxLayout(testCard)
            testLayout.setContentsMargins(20, 18, 20, 18)
            testLayout.setSpacing(10)
            
            testTitle = QLabel("🧪 测试模式")
            testTitle.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; border: none; background: transparent;")
            testLayout.addWidget(testTitle)
            
            testInfo = QLabel("启用后将保存每次截图分析的图片到 data/photo 文件夹")
            testInfo.setStyleSheet("color: #888888; font-size: 11px; border: none; background: transparent;")
            testInfo.setWordWrap(True)
            testLayout.addWidget(testInfo)
            
            # 测试模式开关
            testSwitchLayout = QHBoxLayout()
            testSwitchLabel = QLabel("启用测试模式:")
            testSwitchLabel.setStyleSheet("font-size: 12px; color: #333333; border: none; background: transparent;")
            testSwitchLayout.addWidget(testSwitchLabel)
            
            self.testSwitch = QCheckBox()
            self.testSwitch.setChecked(is_test_mode())
            self.testSwitch.stateChanged.connect(self.onTestModeChanged)
            testSwitchLayout.addWidget(self.testSwitch)
            testSwitchLayout.addStretch()
            
            testLayout.addLayout(testSwitchLayout)
            
            # 测试模式状态
            self.testStatusLabel = QLabel("")
            self.testStatusLabel.setStyleSheet("font-size: 11px; border: none; background: transparent;")
            testLayout.addWidget(self.testStatusLabel)
            self.updateTestStatus()
            
            layout.addWidget(testCard)
            
            # ========== 关于 ==========
            aboutCard = QFrame()
            aboutCard.setStyleSheet("QFrame { background-color: white; border-radius: 12px; border: none; }")
            aboutLayout = QVBoxLayout(aboutCard)
            aboutLayout.setContentsMargins(20, 18, 20, 18)
            aboutLayout.setSpacing(8)
            
            aboutTitle = QLabel("ℹ️ 关于")
            aboutTitle.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; border: none; background: transparent;")
            aboutLayout.addWidget(aboutTitle)
            
            aboutText = QLabel(
                "工作日报助手 v1.0\n"
                "自动截图分析工作内容，生成工作日报。"
            )
            aboutText.setWordWrap(True)
            aboutText.setStyleSheet("color: #666666; font-size: 12px; line-height: 1.5; border: none; background: transparent;")
            aboutLayout.addWidget(aboutText)
            
            layout.addWidget(aboutCard)
            layout.addStretch()
            
            scrollArea.setWidget(contentWidget)
            scrollLayout.addWidget(scrollArea)
            
            # 初始化模型选择状态
            self.onModelTypeChanged(self.modelCombo.currentText())
        
        def onModelTypeChanged(self, text):
            """模型类型改变时的处理"""
            if text == "GLM 通用模型":
                self.glmWidget.setVisible(True)
                self.ollamaWidget.setVisible(False)
                set_use_glm(True)
            else:
                self.glmWidget.setVisible(False)
                self.ollamaWidget.setVisible(True)
                set_use_glm(False)
        
        def testGlmConnection(self):
            """测试GLM连接（多线程）"""
            self.glmTestBtn.setEnabled(False)
            self.glmTestBtn.setText("测试中...")
            self.glmStatusLabel.setText("⏳ 正在测试连接...")
            self.glmStatusLabel.setStyleSheet("color: #FF9800; font-size: 11px; border: none; background: transparent;")
            
            self._test_worker = ConnectionTestWorker("glm")
            self._test_worker.finished.connect(self.onGlmTestFinished)
            self._test_worker.start()
        
        def onGlmTestFinished(self, success, message):
            """GLM测试完成回调"""
            self.glmTestBtn.setEnabled(True)
            self.glmTestBtn.setText("🔗 测试 GLM 连接")
            if success:
                self.glmStatusLabel.setText(f"✅ {message}")
                self.glmStatusLabel.setStyleSheet("color: #4CAF50; font-size: 11px; border: none; background: transparent;")
            else:
                self.glmStatusLabel.setText(f"❌ {message}")
                self.glmStatusLabel.setStyleSheet("color: #F44336; font-size: 11px; border: none; background: transparent;")
        
        def applyOllamaSettings(self):
            """应用Ollama设置"""
            host = self.ollamaHostInput.text().strip()
            model = self.ollamaModelInput.text().strip()
            if not host:
                host = "http://192.168.31.23:11434"
            if not model:
                model = "minicpm-v4.6"
            set_ollama_config(host, model)
            InfoBar.success(
                title="设置已保存",
                content=f"Ollama 服务器: {host}\n模型: {model}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        
        def testOllamaConnection(self):
            """测试Ollama连接（多线程）"""
            host = self.ollamaHostInput.text().strip()
            model = self.ollamaModelInput.text().strip()
            if not host:
                host = "http://192.168.31.23:11434"
            if not model:
                model = "minicpm-v4.6"
            
            self.ollamaTestBtn.setEnabled(False)
            self.ollamaTestBtn.setText("测试中...")
            self.ollamaStatusLabel.setText("⏳ 正在测试连接...")
            self.ollamaStatusLabel.setStyleSheet("color: #FF9800; font-size: 11px; border: none; background: transparent;")
            
            self._test_worker = ConnectionTestWorker("ollama", host, model)
            self._test_worker.finished.connect(self.onOllamaTestFinished)
            self._test_worker.start()
        
        def onOllamaTestFinished(self, success, message):
            """Ollama测试完成回调"""
            self.ollamaTestBtn.setEnabled(True)
            self.ollamaTestBtn.setText("🔗 测试 Ollama 连接")
            if success:
                self.ollamaStatusLabel.setText(f"✅ {message}")
                self.ollamaStatusLabel.setStyleSheet("color: #4CAF50; font-size: 11px; border: none; background: transparent;")
            else:
                self.ollamaStatusLabel.setText(f"❌ {message}")
                self.ollamaStatusLabel.setStyleSheet("color: #F44336; font-size: 11px; border: none; background: transparent;")
        
        def onTestModeChanged(self, state):
            """测试模式开关变化"""
            enabled = state == Qt.Checked
            set_test_mode(enabled)
            self.updateTestStatus()
            
            if enabled:
                InfoBar.success(
                    title="测试模式已启用",
                    content="截图将保存到 data/photo 文件夹",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            else:
                InfoBar.info(
                    title="测试模式已关闭",
                    content="截图将不再保存",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
        
        def updateTestStatus(self):
            """更新测试模式状态显示"""
            if is_test_mode():
                import sys
                if getattr(sys, 'frozen', False):
                    base_dir = os.path.dirname(sys.executable)
                else:
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                photo_dir = os.path.join(base_dir, 'data', 'photo')
                file_count = 0
                if os.path.exists(photo_dir):
                    file_count = len([f for f in os.listdir(photo_dir) if f.endswith('.png')])
                self.testStatusLabel.setText(f"✅ 已启用 - 已保存 {file_count} 张截图")
                self.testStatusLabel.setStyleSheet("color: #4CAF50; font-size: 11px; border: none; background: transparent;")
            else:
                self.testStatusLabel.setText("⏸️ 未启用")
                self.testStatusLabel.setStyleSheet("color: #999999; font-size: 11px; border: none; background: transparent;")
        
        def onScaleChanged(self, text):
            global SCALE_FACTOR
            try:
                new_scale = int(text.replace('%', '')) / 100.0
                if new_scale != SCALE_FACTOR:
                    SCALE_FACTOR = new_scale
                    self.saveScaleSetting(new_scale)
                    InfoBar.info(
                        title="缩放设置已更改",
                        content=f"新缩放比例: {text}，请重启程序使设置生效",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=5000,
                        parent=self
                    )
            except Exception as e:
                print(f"设置缩放失败: {e}")
        
        def saveScaleSetting(self, scale):
            try:
                config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
                os.makedirs(config_dir, exist_ok=True)
                config_file = os.path.join(config_dir, 'config.txt')
                
                config = {}
                if os.path.exists(config_file):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if '=' in line:
                                key, value = line.strip().split('=', 1)
                                config[key] = value
                
                config['scale_factor'] = str(scale)
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    for key, value in config.items():
                        f.write(f"{key}={value}\n")
            except Exception as e:
                print(f"保存配置失败: {e}")

    # ==================== 管理监控页面 ====================
    
    class MonitorPage(QWidget):
        """管理监控页面 - 定时自动截图分析"""
        def __init__(self, main_window, parent=None):
            super().__init__(parent)
            from datetime import datetime  # 导入datetime模块
            self.datetime = datetime  # 保存到实例变量
            self.main_window = main_window
            self.setObjectName("monitorPage")
            self.is_monitoring = False  # 监控状态标志
            
            # 主布局
            mainLayout = QVBoxLayout(self)
            mainLayout.setContentsMargins(0, 0, 0, 0)
            mainLayout.setSpacing(0)
            
            # 滚动区域
            scrollArea = QScrollArea()
            scrollArea.setWidgetResizable(True)
            scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scrollArea.setStyleSheet("QScrollArea { border: none; background-color: #F5F5F5; }")
            
            contentWidget = QWidget()
            contentWidget.setStyleSheet("background-color: #F5F5F5; border: none;")
            layout = QVBoxLayout(contentWidget)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(20)
            
            # ========== 页面标题 ==========
            headerCard = QFrame()
            headerCard.setStyleSheet("QFrame { background-color: white; border-radius: 12px; border: none; }")
            headerLayout = QHBoxLayout(headerCard)
            headerLayout.setContentsMargins(20, 15, 20, 15)
            
            title = QLabel("⚙️ 管理监控")
            title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            headerLayout.addWidget(title)
            headerLayout.addStretch()
            
            # 监控状态标签
            self.statusBadge = QLabel("⏸️ 未监控")
            self.statusBadge.setStyleSheet("""
                QLabel {
                    background-color: #E0E0E0;
                    color: #666666;
                    padding: 6px 14px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: bold;
                    border: none;
                }
            """)
            headerLayout.addWidget(self.statusBadge)
            
            layout.addWidget(headerCard)
            
            # ========== 监控间隔设置 ==========
            intervalCard = QFrame()
            intervalCard.setStyleSheet("QFrame { background-color: white; border-radius: 12px; border: none; }")
            intervalLayout = QVBoxLayout(intervalCard)
            intervalLayout.setContentsMargins(20, 18, 20, 18)
            intervalLayout.setSpacing(12)
            
            # 标题
            intervalTitle = QLabel("⏱️ 监控间隔时长")
            intervalTitle.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; border: none; background: transparent;")
            intervalLayout.addWidget(intervalTitle)
            
            # 说明
            intervalDesc = QLabel("选择自动截图分析的时间间隔，点击开始后将在第一个间隔结束后进行首次分析")
            intervalDesc.setStyleSheet("font-size: 11px; color: #888888; border: none; background: transparent;")
            intervalDesc.setWordWrap(True)
            intervalLayout.addWidget(intervalDesc)
            
            # 间隔选择网格
            intervalGrid = QGridLayout()
            intervalGrid.setSpacing(10)
            
            # 间隔选项（分钟数，显示文本）
            self.interval_options = [
                (1, "1 分钟"), (2, "2 分钟"), (5, "5 分钟"),
                (10, "10 分钟"), (15, "15 分钟"), (20, "20 分钟"),
                (30, "30 分钟"), (60, "1 小时"), (120, "2 小时")
            ]
            
            self.interval_buttons = []
            self.selected_interval = 10  # 默认选中10分钟
            
            for i, (minutes, text) in enumerate(self.interval_options):
                btn = QPushButton(text)
                btn.setCheckable(True)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setMinimumHeight(40)
                
                # 默认选中10分钟
                if minutes == 10:
                    btn.setChecked(True)
                
                # 样式
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #F5F5F5;
                        color: #333333;
                        border: 2px solid #E0E0E0;
                        border-radius: 8px;
                        font-size: 12px;
                        font-weight: bold;
                        padding: 8px 16px;
                    }
                    QPushButton:checked {
                        background-color: #E3F2FD;
                        color: #1976D2;
                        border: 2px solid #1976D2;
                    }
                    QPushButton:hover {
                        background-color: #E8F5E9;
                        border: 2px solid #4CAF50;
                    }
                """)
                
                # 点击事件
                btn.clicked.connect(lambda checked, m=minutes, b=btn: self.selectInterval(m, b))
                
                self.interval_buttons.append(btn)
                intervalGrid.addWidget(btn, i // 3, i % 3)
            
            intervalLayout.addLayout(intervalGrid)
            layout.addWidget(intervalCard)
            
            # ========== 监控日志 ==========
            logCard = QFrame()
            logCard.setStyleSheet("QFrame { background-color: white; border-radius: 12px; border: none; }")
            logLayout = QVBoxLayout(logCard)
            logLayout.setContentsMargins(20, 18, 20, 18)
            logLayout.setSpacing(10)
            
            logTitle = QLabel("📋 监控日志")
            logTitle.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; border: none; background: transparent;")
            logLayout.addWidget(logTitle)
            
            self.logText = QLabel("等待开始监控...")
            self.logText.setStyleSheet("""
                QLabel {
                    background-color: #F5F5F5;
                    color: #666666;
                    padding: 12px;
                    border-radius: 8px;
                    font-size: 11px;
                    font-family: Consolas, monospace;
                    border: none;
                }
            """)
            self.logText.setWordWrap(True)
            self.logText.setAlignment(Qt.AlignTop)
            self.logText.setMinimumHeight(100)
            logLayout.addWidget(self.logText)
            
            layout.addWidget(logCard)
            
            # ========== 开始/结束监控按钮 ==========
            btnCard = QFrame()
            btnCard.setStyleSheet("QFrame { background-color: white; border-radius: 12px; border: none; }")
            btnLayout = QHBoxLayout(btnCard)
            btnLayout.setContentsMargins(20, 18, 20, 18)
            btnLayout.setSpacing(15)
            
            # 开始监控按钮
            self.startBtn = QPushButton("▶️ 开始监控")
            self.startBtn.setCursor(Qt.PointingHandCursor)
            self.startBtn.setMinimumHeight(50)
            self.startBtn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 12px 30px;
                    border-radius: 10px;
                    font-size: 15px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover { background-color: #43A047; }
                QPushButton:pressed { background-color: #388E3C; }
                QPushButton:disabled { background-color: #C8E6C9; color: #A5D6A7; }
            """)
            self.startBtn.clicked.connect(self.startMonitoring)
            btnLayout.addWidget(self.startBtn)
            
            # 结束监控按钮
            self.stopBtn = QPushButton("⏹️ 结束监控")
            self.stopBtn.setCursor(Qt.PointingHandCursor)
            self.stopBtn.setMinimumHeight(50)
            self.stopBtn.setEnabled(False)
            self.stopBtn.setStyleSheet("""
                QPushButton {
                    background-color: #F44336;
                    color: white;
                    padding: 12px 30px;
                    border-radius: 10px;
                    font-size: 15px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover { background-color: #E53935; }
                QPushButton:pressed { background-color: #C62828; }
                QPushButton:disabled { background-color: #FFCDD2; color: #EF9A9A; }
            """)
            self.stopBtn.clicked.connect(self.stopMonitoring)
            btnLayout.addWidget(self.stopBtn)
            
            layout.addWidget(btnCard)
            
            # 添加弹性空间
            layout.addStretch()
            
            scrollArea.setWidget(contentWidget)
            mainLayout.addWidget(scrollArea)
        
        def selectInterval(self, minutes, btn):
            """选择监控间隔"""
            self.selected_interval = minutes
            
            # 更新按钮状态
            for b in self.interval_buttons:
                b.setChecked(b == btn)
            
            print(f"[监控设置] 间隔已选择: {minutes} 分钟")
        
        def startMonitoring(self):
            """开始监控"""
            if self.is_monitoring:
                return
            
            self.is_monitoring = True
            
            # 更新按钮状态
            self.startBtn.setEnabled(False)
            self.stopBtn.setEnabled(True)
            
            # 更新状态标签
            self.statusBadge.setText(f"🔴 监控中 (每{self.selected_interval}分钟)")
            self.statusBadge.setStyleSheet("""
                QLabel {
                    background-color: #E8F5E9;
                    color: #2E7D32;
                    padding: 6px 14px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: bold;
                    border: none;
                }
            """)
            
            # 更新日志
            self.logText.setText(f"[{self.datetime.now().strftime('%H:%M:%S')}] 监控已启动，间隔 {self.selected_interval} 分钟\n等待第一个间隔结束后开始首次分析...")
            
            # 启动定时监控
            start_monitor(
                interval_minutes=self.selected_interval,
                callback=self.onMonitorCallback
            )
            
            InfoBar.success(
                title="监控已启动",
                content=f"每 {self.selected_interval} 分钟自动截图分析",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        
        def stopMonitoring(self):
            """停止监控"""
            if not self.is_monitoring:
                return
            
            self.is_monitoring = False
            
            # 停止定时监控
            stop_monitor()
            
            # 更新按钮状态
            self.startBtn.setEnabled(True)
            self.stopBtn.setEnabled(False)
            
            # 更新状态标签
            self.statusBadge.setText("⏸️ 未监控")
            self.statusBadge.setStyleSheet("""
                QLabel {
                    background-color: #E0E0E0;
                    color: #666666;
                    padding: 6px 14px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: bold;
                    border: none;
                }
            """)
            
            # 更新日志
            current_text = self.logText.text()
            self.logText.setText(current_text + f"\n[{self.datetime.now().strftime('%H:%M:%S')}] 监控已停止")
            
            InfoBar.info(
                title="监控已停止",
                content="定时截图分析已结束",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        
        def onMonitorCallback(self, result, error):
            """监控回调函数 - 每次截图分析完成后调用"""
            if error:
                # 分析失败
                current_text = self.logText.text()
                self.logText.setText(current_text + f"\n[{self.datetime.now().strftime('%H:%M:%S')}] ❌ 分析失败: {str(error)}")
            elif result:
                # 分析成功
                work_type = result.get('type', '未知')
                description = result.get('description', '')
                current_text = self.logText.text()
                # 截断描述，避免日志过长
                short_desc = description[:50] + "..." if len(description) > 50 else description
                self.logText.setText(current_text + f"\n[{self.datetime.now().strftime('%H:%M:%S')}] ✅ [{work_type}] {short_desc}")
                
                # 更新其他页面数据
                self.main_window.todayPage.updateData()
                if hasattr(self.main_window, 'recordsPage'):
                    self.main_window.recordsPage.updateData()
                if hasattr(self.main_window, 'timelinePage'):
                    self.main_window.timelinePage.updateData()

    # ==================== 主窗口 ====================
    
    class MainWindow(FluentWindow):
        """主窗口"""
        def __init__(self):
            super().__init__()
            init_db()
            
            # 创建所有页面
            self.todayPage = TodayWorkPage(self)
            self.screenshotPage = ScreenshotPage(self, self)
            self.recordsPage = RecordsPage(self)
            self.timelinePage = TimelinePage(self)
            self.monitorPage = MonitorPage(self)
            self.reportPage = ReportPage(self)
            self.settingsPage = SettingsPage(self)
            
            # 添加导航项
            self.addSubInterface(self.todayPage, FluentIcon.HOME, "今日工作")
            self.addSubInterface(self.timelinePage, FluentIcon.PIE_SINGLE, "工作时间线")
            self.addSubInterface(self.reportPage, FluentIcon.DOCUMENT, "生成报告")
            self.addSubInterface(self.monitorPage, FluentIcon.PLAY, "管理监控")
            self.addSubInterface(self.recordsPage, FluentIcon.DOCUMENT, "工作记录")
            self.addSubInterface(self.screenshotPage, FluentIcon.CAMERA, "截图分析（内测）")
            self.addSubInterface(self.settingsPage, FluentIcon.SETTING, "设置",
                                NavigationItemPosition.BOTTOM)
            
            self.setWindowTitle("工作日报助手")
            self.resize(1000, 700)
            self.setMinimumSize(800, 600)
            
            # 初始化时加载数据
            self.todayPage.updateData()
            self.recordsPage.updateData()
            self.timelinePage.updateData()  # 更新时间线页面
            
            # 设置系统托盘
            self.setupSystemTray()
            
            # 标志是否从托盘恢复
            self._was_minimized = False
        
        def setupSystemTray(self):
            """设置系统托盘图标和菜单"""
            # 创建系统托盘图标
            self.trayIcon = QSystemTrayIcon(self)
            
            # 使用指定的图片作为图标
            icon_path = r"C:\Users\20057\Desktop\frog.jpg"
            if os.path.exists(icon_path):
                # 加载图片并缩放为图标大小
                pixmap = QPixmap(icon_path)
                pixmap = pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.trayIcon.setIcon(QIcon(pixmap))
            else:
                # 如果图片不存在，使用默认图标
                pixmap = QPixmap(32, 32)
                pixmap.fill(Qt.transparent)
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setBrush(QBrush(QColor("#4CAF50")))
                painter.setPen(QPen(QColor("#388E3C"), 2))
                painter.drawEllipse(2, 2, 28, 28)
                painter.setPen(QColor(Qt.white))
                painter.setFont(QFont("Arial", 14, QFont.Bold))
                painter.drawText(pixmap.rect(), Qt.AlignCenter, "W")
                painter.end()
                self.trayIcon.setIcon(QIcon(pixmap))
            
            # 创建托盘菜单
            trayMenu = QMenu()
            
            # 显示主窗口动作
            showAction = QAction("显示主窗口", self)
            showAction.triggered.connect(self.showMainWindow)
            trayMenu.addAction(showAction)
            
            trayMenu.addSeparator()
            
            # 退出动作
            quitAction = QAction("退出", self)
            quitAction.triggered.connect(self.quitApplication)
            trayMenu.addAction(quitAction)
            
            # 设置托盘菜单
            self.trayIcon.setContextMenu(trayMenu)
            
            # 双击托盘图标显示主窗口
            self.trayIcon.activated.connect(self.trayIconActivated)
            
            # 立即显示托盘图标（程序启动时就在任务栏常驻）
            self.trayIcon.show()
        
        def trayIconActivated(self, reason):
            """处理托盘图标激活事件"""
            if reason == QSystemTrayIcon.DoubleClick:
                self.showMainWindow()
        
        def showMainWindow(self):
            """显示主窗口"""
            self.showNormal()
            self.activateWindow()
            self.raise_()
        
        def quitApplication(self):
            """退出应用程序"""
            # 停止监控
            stop_monitor()
            # 退出应用
            QApplication.quit()
        
        def closeEvent(self, event):
            """处理关闭事件 - 弹窗提示用户选择最小化或关闭"""
            # 忽略默认关闭事件
            event.ignore()
            
            # 创建自定义 Fluent 风格对话框
            dialog = QDialog(self)
            dialog.setWindowTitle(" ")
            dialog.setFixedSize(380, 220)
            dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
            dialog.setAttribute(Qt.WA_TranslucentBackground)
            
            # 主容器
            mainWidget = QWidget(dialog)
            mainWidget.setGeometry(10, 10, 360, 200)
            mainWidget.setStyleSheet("""
                QWidget {
                    background-color: white;
                    border-radius: 12px;
                    border: 1px solid #E0E0E0;
                }
            """)
            
            # 添加阴影效果
            shadow = QGraphicsDropShadowEffect(dialog)
            shadow.setBlurRadius(20)
            shadow.setXOffset(0)
            shadow.setYOffset(4)
            shadow.setColor(QColor(0, 0, 0, 50))
            mainWidget.setGraphicsEffect(shadow)
            
            # 布局
            layout = QVBoxLayout(mainWidget)
            layout.setContentsMargins(24, 20, 24, 20)
            layout.setSpacing(16)
            
            # 标题
            titleLabel = QLabel("👋 确认操作", mainWidget)
            titleLabel.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            layout.addWidget(titleLabel)
            
            # 描述文本
            descLabel = QLabel("请选择您要执行的操作：", mainWidget)
            descLabel.setStyleSheet("font-size: 12px; color: #666666; border: none; background: transparent;")
            layout.addWidget(descLabel)
            
            # 按钮容器
            btnLayout = QHBoxLayout()
            btnLayout.setSpacing(12)
            
            # 最小化到任务栏按钮
            minimizeBtn = QPushButton("🌙 最小化到任务栏", mainWidget)
            minimizeBtn.setCursor(Qt.PointingHandCursor)
            minimizeBtn.setMinimumHeight(40)
            minimizeBtn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #43A047;
                }
                QPushButton:pressed {
                    background-color: #388E3C;
                }
            """)
            minimizeBtn.clicked.connect(lambda: dialog.done(1))
            btnLayout.addWidget(minimizeBtn)
            
            # 直接退出按钮
            closeBtn = QPushButton("🚪 直接退出", mainWidget)
            closeBtn.setCursor(Qt.PointingHandCursor)
            closeBtn.setMinimumHeight(40)
            closeBtn.setStyleSheet("""
                QPushButton {
                    background-color: #F44336;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #E53935;
                }
                QPushButton:pressed {
                    background-color: #C62828;
                }
            """)
            closeBtn.clicked.connect(lambda: dialog.done(2))
            btnLayout.addWidget(closeBtn)
            
            layout.addLayout(btnLayout)
            
            # 取消按钮（文字按钮）
            cancelBtn = QPushButton("取消", mainWidget)
            cancelBtn.setCursor(Qt.PointingHandCursor)
            cancelBtn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #999999;
                    padding: 4px 8px;
                    border: none;
                    font-size: 11px;
                }
                QPushButton:hover {
                    color: #666666;
                }
            """)
            cancelBtn.clicked.connect(lambda: dialog.done(0))
            layout.addWidget(cancelBtn, 0, Qt.AlignCenter)
            
            # 显示对话框并获取结果
            result = dialog.exec_()
            
            # 根据用户选择执行操作
            if result == 1:
                # 最小化到系统托盘
                self.hide()
                self.trayIcon.show()
                self.trayIcon.showMessage(
                    "工作日报助手",
                    "程序已最小化到任务栏，双击图标可恢复窗口",
                    QSystemTrayIcon.Information,
                    2000
                )
            elif result == 2:
                # 直接退出
                self.quitApplication()
            # 如果点击取消，不做任何操作
        
        def changeEvent(self, event):
            """处理窗口状态变化事件"""
            if event.type() == event.WindowStateChange:
                # 如果窗口从最小化恢复
                if self.windowState() == Qt.WindowNoState:
                    self.show()
                    self.activateWindow()
                    self.raise_()
            super().changeEvent(event)
        
        def event(self, event):
            """处理事件，确保窗口能正常恢复"""
            if event.type() == event.WindowStateChange:
                if self.isMinimized():
                    # 最小化时记录状态
                    self._was_minimized = True
                elif self._was_minimized:
                    # 从最小化恢复时
                    self._was_minimized = False
                    self.showNormal()
                    self.activateWindow()
                    self.raise_()
            return super().event(event)

    # ==================== 启动应用 ====================
    
    # 设置应用程序在关闭最后一个窗口时不退出（用于最小化到托盘）
    app.setQuitOnLastWindowClosed(False)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
