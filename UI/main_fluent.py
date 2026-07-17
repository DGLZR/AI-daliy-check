"""
工作日报助手 - Fluent Design 主程序

使用 PyQt-Fluent-Widgets 库实现现代化界面
支持响应式布局，随窗口大小自动调整
支持系统DPI缩放检测和手动调整
"""

import sys
import os
import platform

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
                                 QSizePolicy, QPushButton, QTableWidget, QTableWidgetItem)
    from qfluentwidgets import (FluentWindow, NavigationItemPosition, StrongBodyLabel,
                                TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel,
                                PrimaryPushButton, TransparentPushButton,
                                SimpleCardWidget, HeaderCardWidget, TableWidget,
                                FluentIcon, ComboBox, InfoBar, InfoBarPosition)
    from store import init_db, get_daily_summary, get_daily_records
    from screenshot import run_and_store, get_today_stats, get_monitor_info

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
            avatarPath = r"C:\Users\20057\Desktop\微信图片_20240925102439.jpg"
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
            
            # 热力图网格
            heatGrid = QGridLayout()
            heatGrid.setSpacing(4)
            
            self.hourBlocks = []
            for h in range(24):
                block = QLabel("0")
                block.setMinimumSize(35, 30)
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
            
            timeLayout.addLayout(heatGrid)
            
            # 时间标签
            timeLabelsLayout = QHBoxLayout()
            timeLabelsLayout.setSpacing(0)
            timeLabelsLayout.setContentsMargins(0, 0, 0, 0)
            
            for h in range(24):
                if h % 3 == 0:
                    label = QLabel(f"{h}:00")
                    label.setStyleSheet("font-size: 9px; color: #999999; border: none; background: transparent;")
                    label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                    label.setAlignment(Qt.AlignLeft)
                    timeLabelsLayout.addWidget(label)
                else:
                    spacer = QWidget()
                    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                    spacer.setStyleSheet("border: none;")
                    timeLabelsLayout.addWidget(spacer)
            
            timeLayout.addLayout(timeLabelsLayout)
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
                intensity = count / max_count
                
                if count == 0:
                    bg_color = "#E8F5E9"
                    text_color = "#999999"
                else:
                    alpha = int(50 + intensity * 200)
                    bg_color = f"rgba(76, 175, 80, {alpha})"
                    text_color = "#FFFFFF" if intensity > 0.5 else "#2E7D32"
                
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
            
            infoCard = HeaderCardWidget(self)
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
            self.captureBtn.setEnabled(False)
            self.captureBtn.setText("分析中...")
            self.statusLabel.setText("正在截图并分析，请稍候...")
            self.statusLabel.setStyleSheet("color: #FF9800; font-size: 9px;")
            QTimer.singleShot(100, self.doCapture)
        
        def doCapture(self):
            try:
                result = run_and_store()
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
                
                self.main_window.todayPage.updateData()
            except Exception as e:
                self.statusLabel.setText(f"分析失败: {str(e)}")
                self.statusLabel.setStyleSheet("color: #F44336; font-size: 9px;")
                
                InfoBar.error(
                    title="分析失败",
                    content=str(e),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
            finally:
                self.captureBtn.setEnabled(True)
                self.captureBtn.setText("开始截图分析")

    # ==================== 工作记录页面 ====================
    
    class RecordsPage(QWidget):
        """工作记录页面 - 优化版"""
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
            tableLayout.setContentsMargins(12, 12, 12, 12)
            
            self.recordsTable = QTableWidget()
            self.recordsTable.setColumnCount(5)
            self.recordsTable.setHorizontalHeaderLabels(["ID", "时间", "类型", "描述", "时长"])
            self.recordsTable.horizontalHeader().setStretchLastSection(True)
            self.recordsTable.setColumnWidth(0, 50)
            self.recordsTable.setColumnWidth(1, 100)
            self.recordsTable.setColumnWidth(2, 80)
            self.recordsTable.setColumnWidth(3, 400)
            self.recordsTable.setColumnWidth(4, 80)
            self.recordsTable.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.recordsTable.setStyleSheet("""
                QTableWidget {
                    background-color: white;
                    border: none;
                    gridline-color: #F0F0F0;
                    font-size: 12px;
                }
                QTableWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #F5F5F5;
                }
                QTableWidget::item:selected {
                    background-color: #E3F2FD;
                    color: #1a1a1a;
                }
                QHeaderView::section {
                    background-color: #FAFAFA;
                    color: #333333;
                    padding: 10px;
                    border: none;
                    border-bottom: 2px solid #4CAF50;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
            self.recordsTable.setSelectionBehavior(QTableWidget.SelectRows)
            self.recordsTable.setAlternatingRowColors(True)
            
            tableLayout.addWidget(self.recordsTable)
            layout.addWidget(tableCard, 1)
            
            scrollArea.setWidget(contentWidget)
            mainLayout.addWidget(scrollArea)
        
        def updateData(self):
            """更新记录数据"""
            records = get_daily_records()
            self.recordsTable.setRowCount(len(records))
            self.countLabel.setText(f"📊 共 {len(records)} 条记录")
            
            for row, record in enumerate(records):
                # ID
                idItem = QTableWidgetItem(record['ID'])
                idItem.setTextAlignment(Qt.AlignCenter)
                self.recordsTable.setItem(row, 0, idItem)
                
                # 时间
                timeItem = QTableWidgetItem(record['时间'])
                timeItem.setTextAlignment(Qt.AlignCenter)
                self.recordsTable.setItem(row, 1, timeItem)
                
                # 类型 - 带颜色标签
                typeItem = QTableWidgetItem(record['工作类型'])
                typeItem.setTextAlignment(Qt.AlignCenter)
                self.recordsTable.setItem(row, 2, typeItem)
                
                # 描述
                self.recordsTable.setItem(row, 3, QTableWidgetItem(record['工作描述']))
                
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

    # ==================== 数据统计页面 ====================
    
    class StatsPage(QWidget):
        """数据统计页面 - 优化版"""
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setObjectName("statsPage")
            
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
            layout.setSpacing(15)
            layout.setContentsMargins(20, 15, 20, 15)
            
            # 页面标题
            headerCard = QFrame()
            headerCard.setStyleSheet("QFrame { background-color: white; border-radius: 12px; border: none; }")
            headerLayout = QHBoxLayout(headerCard)
            headerLayout.setContentsMargins(20, 15, 20, 15)
            
            title = QLabel("📊 数据统计")
            title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1a1a1a; border: none; background: transparent;")
            headerLayout.addWidget(title)
            headerLayout.addStretch()
            
            layout.addWidget(headerCard)
            
            # 工作类型时长统计卡片
            typeCard = QFrame()
            typeCard.setStyleSheet("QFrame { background-color: white; border-radius: 12px; border: none; }")
            typeCardLayout = QVBoxLayout(typeCard)
            typeCardLayout.setContentsMargins(20, 15, 20, 15)
            typeCardLayout.setSpacing(12)
            
            typeTitle = QLabel("⏱️ 工作类型时长统计")
            typeTitle.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; border: none; background: transparent;")
            typeCardLayout.addWidget(typeTitle)
            
            typeGrid = QGridLayout()
            typeGrid.setSpacing(10)
            
            self.typeCards = {}
            typeIcons = {
                "开发": "💻", "沟通": "💬", "生活": "🏠",
                "学习": "📚", "设计": "🎨", "管理": "📋",
                "文档": "📝", "娱乐": "🎮", "其他": "📦"
            }
            
            for i, (work_type, icon) in enumerate(typeIcons.items()):
                card = StatCard(f"{work_type}", "0 小时", icon, self)
                card.setMinimumSize(120, 65)
                card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                self.typeCards[work_type] = card
                typeGrid.addWidget(card, i // 3, i % 3)
            
            typeCardLayout.addLayout(typeGrid)
            layout.addWidget(typeCard)
            
            # 每小时记录分布卡片
            hourCard = QFrame()
            hourCard.setStyleSheet("QFrame { background-color: white; border-radius: 12px; border: none; }")
            hourCardLayout = QVBoxLayout(hourCard)
            hourCardLayout.setContentsMargins(20, 15, 20, 15)
            hourCardLayout.setSpacing(12)
            
            hourTitle = QLabel("🕐 每小时记录分布")
            hourTitle.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; border: none; background: transparent;")
            hourCardLayout.addWidget(hourTitle)
            
            # 热力图容器
            heatContainer = QWidget()
            heatContainer.setStyleSheet("border: none; background: transparent;")
            hourGrid = QGridLayout(heatContainer)
            hourGrid.setSpacing(4)
            hourGrid.setContentsMargins(0, 0, 0, 0)
            
            self.hourLabels = {}
            for h in range(24):
                hourWidget = QWidget()
                hourWidget.setStyleSheet("border: none; background: transparent;")
                hourWidgetLayout = QVBoxLayout(hourWidget)
                hourWidgetLayout.setSpacing(2)
                hourWidgetLayout.setContentsMargins(2, 2, 2, 2)
                
                hourLabel = QLabel(f"{h:02d}", hourWidget)
                hourLabel.setAlignment(Qt.AlignCenter)
                hourLabel.setStyleSheet("color: #666666; font-size: 9px; border: none; background: transparent;")
                
                countLabel = QLabel("0", hourWidget)
                countLabel.setAlignment(Qt.AlignCenter)
                countLabel.setStyleSheet("""
                    background-color: #E3F2FD;
                    border-radius: 4px;
                    padding: 4px;
                    color: #1976D2;
                    font-weight: bold;
                    font-size: 10px;
                    border: none;
                """)
                
                hourWidgetLayout.addWidget(countLabel)
                hourWidgetLayout.addWidget(hourLabel)
                
                self.hourLabels[h] = countLabel
                hourGrid.addWidget(hourWidget, h // 8, h % 8)
            
            hourCardLayout.addWidget(heatContainer)
            
            # 时间标签
            timeLabelsLayout = QHBoxLayout()
            timeLabelsLayout.setSpacing(0)
            timeLabelsLayout.setContentsMargins(0, 0, 0, 0)
            
            for h in range(24):
                if h % 3 == 0:
                    label = QLabel(f"{h}:00")
                    label.setStyleSheet("font-size: 9px; color: #999999; border: none; background: transparent;")
                    label.setFixedWidth(40)
                    label.setAlignment(Qt.AlignLeft)
                    timeLabelsLayout.addWidget(label)
                else:
                    spacer = QWidget()
                    spacer.setFixedWidth(40)
                    spacer.setStyleSheet("border: none;")
                    timeLabelsLayout.addWidget(spacer)
            
            hourCardLayout.addLayout(timeLabelsLayout)
            layout.addWidget(hourCard)
            
            # 使用时间卡片
            timeCard = QFrame()
            timeCard.setStyleSheet("QFrame { background-color: white; border-radius: 12px; border: none; }")
            timeCardLayout = QHBoxLayout(timeCard)
            timeCardLayout.setContentsMargins(20, 12, 20, 12)
            timeCardLayout.setSpacing(30)
            
            self.firstUseLabel = QLabel("🌅 最早使用: --:--")
            self.firstUseLabel.setStyleSheet("font-size: 13px; color: #333333; border: none; background: transparent;")
            timeCardLayout.addWidget(self.firstUseLabel)
            timeCardLayout.addStretch()
            
            self.lastUseLabel = QLabel("🌙 最晚使用: --:--")
            self.lastUseLabel.setStyleSheet("font-size: 13px; color: #333333; border: none; background: transparent;")
            timeCardLayout.addWidget(self.lastUseLabel)
            
            layout.addWidget(timeCard)
            
            # 添加弹性空间
            layout.addStretch()
            
            scrollArea.setWidget(contentWidget)
            mainLayout.addWidget(scrollArea)
        
        def updateData(self):
            """更新统计数据"""
            summary = get_daily_summary()
            if summary:
                for work_type in self.typeCards:
                    hours = float(summary.get(f'{work_type}时长(小时)', '0'))
                    self.typeCards[work_type].updateValue(f"{hours:.1f}h")
                
                max_count = 1
                for h in range(24):
                    count = int(summary.get(f'{h:02d}:00记录数', '0') or '0')
                    if count > max_count:
                        max_count = count
                
                for h in range(24):
                    count = int(summary.get(f'{h:02d}:00记录数', '0') or '0')
                    self.hourLabels[h].setText(str(count))
                    if count > 0:
                        intensity = count / max_count
                        alpha = int(80 + intensity * 175)
                        self.hourLabels[h].setStyleSheet(f"""
                            background-color: rgba(76, 175, 80, {alpha});
                            border-radius: 4px;
                            padding: 4px;
                            color: {"white" if intensity > 0.4 else "#2E7D32"};
                            font-weight: bold;
                            font-size: 10px;
                            border: none;
                        """)
                    else:
                        self.hourLabels[h].setStyleSheet("""
                            background-color: #E8F5E9;
                            border-radius: 4px;
                            padding: 4px;
                            color: #999999;
                            font-weight: bold;
                            font-size: 10px;
                            border: none;
                        """)
                
                self.firstUseLabel.setText(f"🌅 最早使用: {summary.get('最早使用时间', '--:--')}")
                self.lastUseLabel.setText(f"🌙 最晚使用: {summary.get('最晚使用时间', '--:--')}")
            else:
                for card in self.typeCards.values():
                    card.updateValue("0h")
                for h in range(24):
                    self.hourLabels[h].setText("0")
                    self.hourLabels[h].setStyleSheet("""
                        background-color: #E8F5E9;
                        border-radius: 4px;
                        padding: 4px;
                        color: #999999;
                        font-weight: bold;
                        font-size: 10px;
                        border: none;
                    """)
                self.firstUseLabel.setText("🌅 最早使用: --:--")
                self.lastUseLabel.setText("🌙 最晚使用: --:--")

    # ==================== 设置页面 ====================
    
    class SettingsPage(QWidget):
        """设置页面"""
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setObjectName("settingsPage")
            
            scrollLayout = QVBoxLayout(self)
            scrollLayout.setContentsMargins(0, 0, 0, 0)
            
            scrollArea = QScrollArea()
            scrollArea.setWidgetResizable(True)
            scrollArea.setStyleSheet("QScrollArea { border: none; background-color: #F5F5F5; }")
            
            contentWidget = QWidget()
            contentWidget.setStyleSheet("background-color: #F5F5F5;")
            layout = QVBoxLayout(contentWidget)
            layout.setSpacing(12)
            layout.setContentsMargins(15, 10, 15, 10)
            
            title = SubtitleLabel("设置", self)
            title.setStyleSheet("font-size: 14px; font-weight: bold;")
            layout.addWidget(title)
            
            # 显示缩放设置
            scaleTitle = SectionTitle("显示缩放", self)
            layout.addWidget(scaleTitle)
            
            scaleCard = SimpleCardWidget(self)
            scaleCard.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            scaleLayout = QVBoxLayout(scaleCard)
            scaleLayout.setContentsMargins(12, 10, 12, 10)
            scaleLayout.setSpacing(6)
            
            scaleInfo = BodyLabel("界面缩放比例（修改后需重启程序生效）", scaleCard)
            scaleInfo.setStyleSheet("color: #666666; font-size: 9px;")
            scaleLayout.addWidget(scaleInfo)
            
            scaleComboLayout = QHBoxLayout()
            scaleLabel = BodyLabel("缩放比例:", scaleCard)
            scaleLabel.setStyleSheet("font-size: 10px;")
            scaleComboLayout.addWidget(scaleLabel)
            
            self.scaleCombo = ComboBox(scaleCard)
            self.scaleCombo.addItems(["25%", "50%", "75%", "100%", "125%", "150%", "175%", "200%"])
            self.scaleCombo.setCurrentText(f"{SCALE_FACTOR * 100:.0f}%")
            self.scaleCombo.currentTextChanged.connect(self.onScaleChanged)
            scaleComboLayout.addWidget(self.scaleCombo)
            scaleComboLayout.addStretch()
            
            scaleLayout.addLayout(scaleComboLayout)
            
            systemScaleLabel = BodyLabel(f"系统缩放: {get_system_dpi_scale() * 100:.0f}%", scaleCard)
            systemScaleLabel.setStyleSheet("color: #888888; font-size: 9px;")
            scaleLayout.addWidget(systemScaleLabel)
            
            layout.addWidget(scaleCard)
            
            # 服务器设置
            serverTitle = SectionTitle("Ollama 服务器", self)
            layout.addWidget(serverTitle)
            
            serverCard = SimpleCardWidget(self)
            serverCard.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            serverLayout = QVBoxLayout(serverCard)
            serverLayout.setContentsMargins(12, 10, 12, 10)
            serverLayout.setSpacing(6)
            
            serverInfo = BodyLabel("服务器地址", serverCard)
            serverInfo.setStyleSheet("color: #666666; font-size: 9px;")
            serverLayout.addWidget(serverInfo)
            
            serverUrl = StrongBodyLabel("http://192.168.31.23:11434", serverCard)
            serverUrl.setStyleSheet("color: #0078d4; font-size: 11px;")
            serverUrl.setWordWrap(True)
            serverLayout.addWidget(serverUrl)
            
            serverStatus = BodyLabel("● 已连接", serverCard)
            serverStatus.setStyleSheet("color: #4CAF50; font-size: 10px;")
            serverLayout.addWidget(serverStatus)
            
            layout.addWidget(serverCard)
            
            # 模型设置
            modelTitle = SectionTitle("识别模型", self)
            layout.addWidget(modelTitle)
            
            modelCard = SimpleCardWidget(self)
            modelCard.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            modelLayout = QVBoxLayout(modelCard)
            modelLayout.setContentsMargins(12, 10, 12, 10)
            modelLayout.setSpacing(6)
            
            modelInfo = BodyLabel("当前模型", modelCard)
            modelInfo.setStyleSheet("color: #666666; font-size: 9px;")
            modelLayout.addWidget(modelInfo)
            
            modelName = StrongBodyLabel("minicpm-v4.6", modelCard)
            modelName.setStyleSheet("color: #333333; font-size: 11px;")
            modelLayout.addWidget(modelName)
            
            modelDesc = BodyLabel("支持图像识别的多模态大语言模型", modelCard)
            modelDesc.setStyleSheet("color: #888888; font-size: 9px;")
            modelDesc.setWordWrap(True)
            modelLayout.addWidget(modelDesc)
            
            layout.addWidget(modelCard)
            
            # 数据存储
            dataTitle = SectionTitle("数据存储", self)
            layout.addWidget(dataTitle)
            
            dataCard = SimpleCardWidget(self)
            dataCard.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            dataLayout = QVBoxLayout(dataCard)
            dataLayout.setContentsMargins(12, 10, 12, 10)
            dataLayout.setSpacing(6)
            
            pathInfo = BodyLabel("存储路径", dataCard)
            pathInfo.setStyleSheet("color: #666666; font-size: 9px;")
            dataLayout.addWidget(pathInfo)
            
            dataPath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
            pathLabel = BodyLabel(dataPath, dataCard)
            pathLabel.setStyleSheet("color: #333333; font-size: 9px;")
            pathLabel.setWordWrap(True)
            pathLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
            dataLayout.addWidget(pathLabel)
            
            filesLabel = BodyLabel("数据文件:", dataCard)
            filesLabel.setStyleSheet("color: #666666; font-size: 9px; margin-top: 4px;")
            dataLayout.addWidget(filesLabel)
            
            filesList = BodyLabel(
                "• daily_summary.csv - 每日汇总数据\n"
                "• records.csv - 截图分析记录",
                dataCard
            )
            filesList.setStyleSheet("color: #888888; font-size: 9px;")
            filesList.setWordWrap(True)
            dataLayout.addWidget(filesList)
            
            layout.addWidget(dataCard)
            
            # 关于
            aboutTitle = SectionTitle("关于", self)
            layout.addWidget(aboutTitle)
            
            aboutCard = SimpleCardWidget(self)
            aboutCard.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            aboutLayout = QVBoxLayout(aboutCard)
            aboutLayout.setContentsMargins(12, 10, 12, 10)
            
            aboutText = BodyLabel(
                "工作日报助手 v1.0\n"
                "自动截图分析工作内容，生成工作日报。",
                aboutCard
            )
            aboutText.setWordWrap(True)
            aboutText.setStyleSheet("color: #666666; font-size: 9px; line-height: 1.4;")
            aboutLayout.addWidget(aboutText)
            
            layout.addWidget(aboutCard)
            layout.addStretch()
            
            scrollArea.setWidget(contentWidget)
            scrollLayout.addWidget(scrollArea)
        
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

    # ==================== 主窗口 ====================
    
    class MainWindow(FluentWindow):
        """主窗口"""
        def __init__(self):
            super().__init__()
            init_db()
            
            self.todayPage = TodayWorkPage(self)
            self.screenshotPage = ScreenshotPage(self, self)
            self.recordsPage = RecordsPage(self)
            self.statsPage = StatsPage(self)
            self.settingsPage = SettingsPage(self)
            
            self.addSubInterface(self.todayPage, FluentIcon.HOME, "今日工作")
            self.addSubInterface(self.screenshotPage, FluentIcon.CAMERA, "截图分析")
            self.addSubInterface(self.recordsPage, FluentIcon.DOCUMENT, "工作记录")
            self.addSubInterface(self.statsPage, FluentIcon.PIE_SINGLE, "数据统计")
            self.addSubInterface(self.settingsPage, FluentIcon.SETTING, "设置",
                                NavigationItemPosition.BOTTOM)
            
            self.setWindowTitle("工作日报助手")
            self.resize(1000, 700)
            self.setMinimumSize(800, 600)
            
            # 初始化时加载数据
            self.todayPage.updateData()
            self.recordsPage.updateData()
            self.statsPage.updateData()

    # ==================== 启动应用 ====================
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
