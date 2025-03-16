#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import glob
import math
import chardet
import numpy as np
from scipy import interpolate
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtCore import QObject, QThread, Signal, Slot

from MainWindow_ui import Ui_MainWindow


class FileAnalyzerThread(QThread):
    logging = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = plt.figure()
        self.directory = ""
        self._stop_event = True
        self._terminal = False
        self.begin_pattern = re.compile(r'^\:BEGIN\s*$')
        self.end_pattern = re.compile(r'^\:END\s*$')
        self.pos_pattern = re.compile(
            r'^点 \d+\: X 坐标\s+(-?\d+\.?\d*).*Y 坐标\s+(-?\d+\.?\d*).*Z 坐标\s+(-?\d+\.?\d*).*')
        self.location_pattern = re.compile(r'^[^\s\:]+\s*$')
        self.sn_pattern1 = re.compile(
            r'^文字说明 \d+.*日期/时间 (\d{4}\-\d{2}\-\d{2}) (\d{2}\:\d{2}\:\d{2}) ([^\s]+)\s*$')
        self.sn_pattern2 = re.compile(
            r'^提示 \d+.*输入 ([^\s]+)\s+.*日期/时间 (\d{4}\-\d{2}\-\d{2}) (\d{2}\:\d{2}\:\d{2})\s*$')

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

    def load_txt_file(self,file_path):
        # 导入三次元测量数据 .txt 文件，将所有单元的数据存储在数组中
        flag = False
        data = []
        with open(file_path, mode='rb') as f:
            encoding = chardet.detect(f.read())['encoding']
        with open(file_path, mode='r', encoding=encoding, errors='ignore') as f:
            for line in f:
                if self.begin_pattern.match(line):
                    # 识别三次元数据起始标记
                    flag = True
                    unit = {
                        'sn': '',
                        'location': '',
                        'date': '',
                        'time': '',
                        'minX': None,
                        'maxX': None,
                        'minY': None,
                        'maxY': None,
                        'flatness': None,
                        'shape': '未知',
                        'pos': []
                    }
                    continue

                if not flag:
                    # 未识别到三次元数据起始标记时忽略
                    continue

                if self.end_pattern.match(line):
                    # 识别三次元数据结束标记
                    flag = False
                    if len(unit['pos']) > 2:
                        data.append(unit)

                elif self.location_pattern.match(line):
                    # 识别测量位置
                    unit['location'] = line.strip()

                elif self.pos_pattern.match(line):
                    # 识别测量数据
                    pos = self.pos_pattern.match(line).groups()
                    x = float(pos[0])
                    y = float(pos[1])
                    z = float(pos[2])
                    if unit['minX'] is None or x < unit['minX']:
                        unit['minX'] = x
                    if unit['maxX'] is None or x > unit['maxX']:
                        unit['maxX'] = x
                    if unit['minY'] is None or y < unit['minY']:
                        unit['minY'] = y
                    if unit['maxY'] is None or y > unit['maxY']:
                        unit['maxY'] = y
                    unit['pos'].append([x, y, z])

                elif self.sn_pattern1.match(line):
                    # 识别测量编号，示使如下：
                    # 文字说明 75: 文字说明  文字说明 75: 日期/时间 2025-02-24 18:50:25 9206301-02
                    date, time, sn = self.sn_pattern1.match(line).groups()
                    unit['sn'] = sn
                    unit['date'] = date
                    unit['time'] = time

                elif self.sn_pattern2.match(line):
                    # 识别测量编号，示例如下：
                    # 提示 44: 提示  提示 44: 输入 42363-03 提示 44: 日期/时间 2025-02-19 13:05:27
                    sn, date, time = self.sn_pattern1.match(line).groups()
                    unit['sn'] = sn
                    unit['date'] = date
                    unit['time'] = time

    def create_plot(self, data, save_path):
        # 使用matplotlib绘制三维图形并保存到指定路径
        # 提取 x, y, z 坐标
        x = [point[0] for point in data['pos']]
        y = [point[1] for point in data['pos']]
        z = [point[2] for point in data['pos']]

        # 创建三维图形Axes3D对象
        self.figure.clear()
        ax = Axes3D(self.figure, auto_add_to_figure=False)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.view_init(elev=75, azim=-70)
        ax.set_xlim(data['minX'], data['maxX'])
        ax.set_ylim(data['minY'], data['maxY'])
        self.figure.add_axes(ax)

        # 使用RBF插值函数进行曲面拟合
        func_name = 'thin_plate'
        color_map = 'rainbow'
        func = interpolate.Rbf(x, y, z, function=func_name)
        xnew, ynew = np.mgrid[np.min(x):np.max(x):50j, np.min(y):np.max(y):50j]
        znew = func(xnew, ynew)
        # newz = func(x, y)
        # ax.scatter(x, y, newz+0.001, c='r', marker='o')

        # 绘制曲面
        surf = ax.plot_surface(
            xnew, ynew, znew, cmap=color_map)
        self.figure.colorbar(
            surf, shrink=0.6, aspect=10)


        # 保存图形
        self.figure.canvas.draw()
        plt.savefig(save_path)
        plt.close(self.figure)

    def calcFlatness(self,data):
        # 计算理想参考平面的系数
        matrixA = [[v[0], v[1], 1] for v in data['pos']]
        matrixB = [[v[2]] for v in data['pos']]
        matrixA = np.array(matrixA)
        matrixB = np.array(matrixB)
        matrixCoeff = np.dot(np.dot(np.linalg.inv(
            np.dot(matrixA.T, matrixA)), matrixA.T), matrixB)
        coeffA = -1 * matrixCoeff[0][0]
        coeffB = -1 * matrixCoeff[1][0]
        coeffC = 1
        coeffD = -1 * matrixCoeff[2][0]
        constant = math.sqrt(coeffA*coeffA+coeffB*coeffB+coeffC*coeffC)

        # 计算每个点参考理想平面的高度
        for point in data['pos']:
            point[2] = (coeffA*point[0]+coeffB*point[1] +
                        coeffC*point[2]+coeffD)/constant

        # 计算中心形貌统计值
        centralZoneLimit = 0.5  # 中心区域限制
        centralMinZ = None      # 中心区域最小Z值
        centralMaxZ = None      # 中心区域最大Z值
        marginalSum = 0         # 边区域Z'总和
        marginalCount = 0       # 边区域Z'个数
        minZ = None
        maxZ = None
        sum = 0

        # 迭代计算最小、最大、加总、平均Z值
        for point in data['pos']:
            # 计算总体Z'的统计值
            if minZ is None or point[2] < minZ:
                minZ = point[2]
            if maxZ is None or point[2] > maxZ:
                maxZ = point[2]
            sum += point[2]

            # 计算中心区域Z'统计值
            minX = data['minX']
            maxX = data['maxX']
            minY = data['minY']
            maxY = data['maxY']
            rangeX = maxX-minX
            rangeY = maxY-minY

            if abs(2*(point[0]-minX)/rangeX - 1) < centralZoneLimit and abs(2*(point[1]-minY)/rangeY - 1) < centralZoneLimit:
                # 当前量测点为板中心位置时
                if centralMinZ is None or point[2] < centralMinZ:
                    centralMinZ = point[2]
                if centralMaxZ is None or point[2] > centralMaxZ:
                    centralMaxZ = point[2]
            else:
                # 当前量测点为板边位置时
                marginalSum += point[2]
                marginalCount += 1

        # 计算中心区域形貌
        marginalAvg = marginalSum/marginalCount
        data['shape'] = '未知'
        if centralMinZ is not None:
            if centralMinZ > marginalAvg:
                # 中心凸起
                data['shape'] = '中心凸起'
            elif centralMaxZ < marginalAvg:
                # 中心下凹
                data['shape'] = '中心下凹'
            else:
                # 凹凸不平
                data['shape'] = '凹凸不平'

        # 将Z坐标转换为正值
        for point in data['pos']:
            point[2] = point[2]-minZ
        data['flatness'] = maxZ-minZ
        return data


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
