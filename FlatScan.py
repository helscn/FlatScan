#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import glob
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtCore import QObject, QThread, Signal, Slot

from MainWindow_ui import Ui_MainWindow


class FileAnalyzerThread(QThread):
    logging = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.directory = ""
        self._stop_event = True
        self._terminal = False

    def set_directory(self, directory):
        self.directory = directory

    def run(self):
        while True:
            while not self._stop_event:
                for file_path, _, name_part, _ in find_matching_files(self.directory, "*.txt"):
                    if self._stop_event:
                        break
                    self.logging.emit(name_part+".txt", "INFO")
            if self._terminal:
                break
            if self._stop_event:
                self.msleep(1000)  # Sleep for 1 second before checking again

    def resume(self):
        self._stop_event = False
    def stop(self):
        self._stop_event = True

    def terminate(self):
        self._terminal = True
        self._stop_event = True


class MyMainWindow(QMainWindow, Ui_MainWindow):
    start_thread_signal = Signal()
    set_directory_signal = Signal(str)
    stop_thread_signal = Signal()
    resume_thread_signal = Signal()
    terminate_thread_signal = Signal()

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.analyzer_thread = FileAnalyzerThread()
        self.analyzer_thread.logging.connect(self.logging)
        self.set_directory_signal.connect(self.analyzer_thread.set_directory)
        self.start_thread_signal.connect(self.analyzer_thread.start)
        self.stop_thread_signal.connect(self.analyzer_thread.stop)
        self.terminate_thread_signal.connect(self.analyzer_thread.terminate)
        self.resume_thread_signal.connect(self.analyzer_thread.resume)
        self.btnSelectFolder.clicked.connect(self.select_folder)
        self.btnStart.clicked.connect(self.start_analysis)
        self.btnStop.clicked.connect(self.stop_analysis)
        self.btnExit.clicked.connect(self.exit_application)  # 添加 btnExit 按钮点击事件处理函数

        self.folderPath.setText("D:\\")
        self.processLog.setReadOnly(True)
        self.processLog.setMaximumBlockCount(1000)
        self.start_thread_signal.emit()
        self.btnStop.setEnabled(False)

    def start_analysis(self):
        folder_path = self.folderPath.text()
        if folder_path:
            self.set_directory_signal.emit(folder_path)
            self.resume_thread_signal.emit()
            self.logging("正在搜索以下文件夹中的平整度数据："+folder_path, "WARN")
            self.btnSelectFolder.setEnabled(False)
            self.btnStart.setEnabled(False)
            self.btnStop.setEnabled(True)

    def stop_analysis(self):
        self.stop_thread_signal.emit()
        self.logging("正在停止后台平整度数据分析...", "ERROR")
        self.btnSelectFolder.setEnabled(True)
        self.btnStart.setEnabled(True)
        self.btnStop.setEnabled(False)

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

    def closeEvent(self, event):
        self.terminate_thread_signal.emit()
        self.analyzer_thread.wait()  # 等待线程结束
        event.accept()

    def exit_application(self):  # 新增的退出应用程序函数
        self.terminate_thread_signal.emit()
        self.analyzer_thread.wait()  # 等待线程结束
        QApplication.quit()  # 退出应用程序

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
