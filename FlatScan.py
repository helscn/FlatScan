#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import glob
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtCore import QObject, QThread, Signal, Slot, QMutex, QWaitCondition
from MainWindow_ui import Ui_MainWindow

class MyMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.init()
        
    def init(self):
        self.folderPath.setText("D:/")
        self.processLog.setReadOnly(True)
        self.processLog.setMaximumBlockCount(30)
        self.btnSelectFolder.clicked.connect(self.select_folder)
        self.btnStart.clicked.connect(self.start_analysis)
        self.btnStop.clicked.connect(self.stop_analysis)

    def start_analysis(self):
        self.logging("开始分析...", "INFO")


    def stop_analysis(self):
        self.logging("异常","ERROR")

    
    def logging(self, message, level="INFO"):
        color = {
            "INFO": "#141414",
            "WARN": "#1414FF",
            "ERROR": "#FF6969"
        }.get(level, "#D4D4D4")
        
        self.processLog.appendHtml(f'<div style="color: {color}">{message}</div>')
        self.processLog.verticalScrollBar().setValue(self.processLog.verticalScrollBar().maximum())


    def select_folder(self):
        selected_dir = QFileDialog.getExistingDirectory(
            parent=None,          # 父窗口（None表示无父窗口）
            caption="选择文件夹",  # 对话框标题
            dir="",               # 初始目录（空字符串表示系统默认）
            options=QFileDialog.ShowDirsOnly  # 只显示文件夹
        )
        if selected_dir:
            self.folderPath.setText(selected_dir)

def find_matching_files(directory, pattern):
    """
    使用 glob 模块递归遍历目录，查找所有符合通配符模式的文件。
    """
    # 构造递归匹配模式（兼容跨平台路径格式）
    search_pattern = os.path.join(directory, "**", pattern)
    
    # 遍历所有匹配路径（使用生成器模式节省内存）
    for file_path in glob.iglob(search_pattern, recursive=True):
        if os.path.isfile(file_path):  # 确保仅处理文件
            dirpath = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            name_part, ext_part = os.path.splitext(filename)
            yield (file_path, dirpath, name_part, ext_part)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec())