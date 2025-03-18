#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import json
import glob
import math
import csv
from datetime import datetime
import chardet
import numpy as np
from scipy import interpolate
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtGui import QIcon
from PySide6.QtCore import QThread, Signal, QCoreApplication

import resource_rc
from MainWindow_ui import Ui_MainWindow


class FileAnalyzerThread(QThread):
    logging = Signal(str, str)
    showInfoSignal = Signal(str)
    flatnessSignal = Signal(str, str, dict)   #文件夹，文件名，平整度数据

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = {
            "dataDirectory": "D:\\",
            "centralZoneLimit": 0.5,
            "rbfFunction": "thin_plate",
            "scanDirectoryInterval": 30
        }
        self._process_next = False
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

    def update_config(self, config):
        self.config = config

    def process_next(self):
        self._process_next = True

    def run(self):
        while True:
            while not self._stop_event:
                search_pattern = os.path.join(self.config['dataDirectory'], "**", "*平整度*.txt")
                scanDirectoryInterval=int(self.config['scanDirectoryInterval'])
                for file_path in glob.iglob(search_pattern, recursive=True):
                    if self._stop_event:
                        break
                    self.showInfoSignal.emit(f"正在分析文件：{file_path}")
                    if os.path.isfile(file_path):  # 确保仅处理文件
                        dirpath = os.path.dirname(file_path)
                        fullfilename = os.path.basename(file_path)
                        filename, fileext = os.path.splitext(fullfilename)
                        
                        result_file=os.path.join(dirpath,filename+".csv")
                        if os.path.isfile(result_file):
                            # 跳过已经转换的txt文件
                            continue
                        
                        self.logging.emit(f"正在分析文件：{file_path}", "INFO")
                        rawdata=self.load_txt_file(file_path)  # 读取三次元量测的txt文件
                        if not rawdata:
                            self.logging.emit(f"文件 {fullfilename} 中没有找到量测数据！", "ERROR")
                            continue

                        result=[["文件名","日期","时间","板编号","量测位置","中心形貌","平整度"]]
                        try:
                            for bga in rawdata:
                                if self._stop_event:
                                    break
                                bga=self.calcFlatness(bga)    # 计算相对理想平面的Z坐标
                                result.append([filename,bga['date'],bga['time'],bga['sn'],bga['location'],bga['shape'],bga['flatness']])
                                self._process_next=False
                                self.flatnessSignal.emit(dirpath,filename,bga)
                                while not (self._process_next or self._stop_event):
                                    self.msleep(50)
                            if self._stop_event:
                                self.logging.emit(f"已经停止文件 {fullfilename} 的平整度分析！", "ERROR")
                                break
                            with open(result_file,mode='w',newline='',encoding='gb2312') as csvfile:
                                # 保存平整度数据
                                writer = csv.writer(csvfile)
                                writer.writerows(result)
                                self.logging.emit(f"文件 {fullfilename} 分析完成！", "INFO")
                        except Exception as e:
                            self.logging.emit(f"文件 {fullfilename} 分析失败：{e}", "ERROR")
                self.showInfoSignal.emit(f"等待 {scanDirectoryInterval}  秒后重新扫描文件夹。")
                for _ in range(scanDirectoryInterval):
                    self.msleep(1000)
                    if self._stop_event:
                        break
                        

            if self._terminal:
                break
            if self._stop_event:
                self.msleep(1000)

                

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
        result = []
        unit = []
        with open(file_path, mode='rb') as f:
            encoding = chardet.detect(f.read())['encoding']
        with open(file_path, mode='r', encoding=encoding, errors='ignore') as f:
            for line in f:
                if self.begin_pattern.match(line):
                    # 识别三次元数据起始标记
                    flag = True
                    unit = []
                    bga = {
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
                    
                    for bga in unit:
                        if "BGA" in bga['location'].upper():
                            if len(bga['pos']) > 2 and bga['sn']!="" and bga['location']!="":
                                result.append(bga)
                            else:
                                if bga['sn']!="" and bga['location']!="":
                                    self.logging.emit(f"文件 {file_path} 中编号 {bga['sn']} 的 {bga['location']} 数据异常，已忽略！", "ERROR")

                elif self.location_pattern.match(line):
                    # 识别测量位置
                    bga['location'] = line.strip()
                    unit.append(bga)
                    bga = {
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

                elif self.pos_pattern.match(line):
                    # 识别测量数据
                    pos = self.pos_pattern.match(line).groups()
                    x = float(pos[0])
                    y = float(pos[1])
                    z = float(pos[2])
                    if bga['minX'] is None or x < bga['minX']:
                        bga['minX'] = x
                    if bga['maxX'] is None or x > bga['maxX']:
                        bga['maxX'] = x
                    if bga['minY'] is None or y < bga['minY']:
                        bga['minY'] = y
                    if bga['maxY'] is None or y > bga['maxY']:
                        bga['maxY'] = y
                    bga['pos'].append([x, y, z])

                elif self.sn_pattern1.match(line):
                    # 识别测量编号，示使如下：
                    # 文字说明 75: 文字说明  文字说明 75: 日期/时间 2025-02-24 18:50:25 9206301-02
                    date, time, sn = self.sn_pattern1.match(line).groups()
                    for bga in unit:
                        bga['sn'] = sn
                        bga['date'] = date
                        bga['time'] = time

                elif self.sn_pattern2.match(line):
                    # 识别测量编号，示例如下：
                    # 提示 44: 提示  提示 44: 输入 42363-03 提示 44: 日期/时间 2025-02-19 13:05:27
                    sn, date, time = self.sn_pattern2.match(line).groups()
                    for bga in unit:
                        bga['sn'] = sn
                        bga['date'] = date
                        bga['time'] = time
        return result
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
        centralZoneLimit = self.config['centralZoneLimit']
        centralMinZ = None      # 中心区域最小Z值
        centralMaxZ = None      # 中心区域最大Z值
        marginalSumZ = 0         # 边区域Z'总和
        marginalCount = 0       # 边区域Z'个数
        minZ = None
        maxZ = None

        # 迭代计算最小、最大、加总、平均Z值
        for point in data['pos']:
            # 计算总体Z'的统计值
            if minZ is None or point[2] < minZ:
                minZ = point[2]
            if maxZ is None or point[2] > maxZ:
                maxZ = point[2]

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
                marginalSumZ += point[2]
                marginalCount += 1

        # 计算中心区域形貌
        marginalAvg = marginalSumZ/marginalCount
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

        data['flatness'] = round(maxZ-minZ,4)
        return data


class MyMainWindow(QMainWindow, Ui_MainWindow):
    start_thread_signal = Signal()
    update_config_signal = Signal(dict)
    stop_thread_signal = Signal()
    resume_thread_signal = Signal()
    terminate_thread_signal = Signal()
    process_next_signal = Signal()

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.load_config()  # 加载配置信息
        self.setWindowTitle("平整度自动分析程序")
        self.setWindowIcon(QIcon(":/icon.ico"))
        self.folderPath.setText(self.config["dataDirectory"])
        self._stop_event = True
        self.figure_3d=plt.figure()
        self.figure_2d=plt.figure()

        self.btnStop.setEnabled(False)
        self.processLog.setReadOnly(True)
        self.processLog.setMaximumBlockCount(1000)

        self.analyzer_thread = FileAnalyzerThread()
        self.analyzer_thread.logging.connect(self.logging)
        self.analyzer_thread.flatnessSignal.connect(self.create_plot)
        self.analyzer_thread.showInfoSignal.connect(self.statusbar.showMessage)
        self.start_thread_signal.connect(self.analyzer_thread.start)
        self.stop_thread_signal.connect(self.analyzer_thread.stop)
        self.stop_thread_signal.connect(self.stop)
        self.terminate_thread_signal.connect(self.analyzer_thread.terminate)
        self.resume_thread_signal.connect(self.analyzer_thread.resume)
        self.resume_thread_signal.connect(self.resume)
        self.process_next_signal.connect(self.analyzer_thread.process_next)
        self.btnSelectFolder.clicked.connect(self.select_folder)
        self.btnStart.clicked.connect(self.start_analysis)
        self.btnStop.clicked.connect(self.stop_analysis)
        self.btnExit.clicked.connect(self.exit_application)  # 添加 btnExit 按钮点击事件处理函数
        self.update_config_signal.connect(self.analyzer_thread.update_config)
        self.start_thread_signal.emit()

        self.statusbar.showMessage("就绪。")  # 初始化状态栏信息
        if self.config["autoStart"]:
            self.btnStart.click()

    def resume(self):
        self._stop_event = False
    def stop(self):
        self._stop_event = True
    def load_config(self):
        # 获取当前脚本文件所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "config.json")

        # 默认配置
        default_config = {
            "dataDirectory": "D:\\",
            "centralZoneLimit": 0.5,
            "rbfFunction": "thin_plate",
            "colorMap": "rainbow",
            "plotDPI":100,
            "scanDirectoryInterval": 30,
            "autoStart": True
        }

        # 读取配置文件
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.logging("配置文件 config.json不存在，使用默认配置。", "WARN")
            config = {}

        # 合并默认配置和读取的配置
        default_config.update(config)
        self.config = default_config

    def save_config(self):
        # 获取当前脚本文件所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "config.json")

        # 将配置保存到 config.json 文件中
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def start_analysis(self):
        folder_path = self.config["dataDirectory"]
        if folder_path:
            self.update_config_signal.emit(self.config)
            self.resume_thread_signal.emit()
            self.logging("正在搜索以下文件夹中的平整度数据："+folder_path, "WARN")
            self.btnSelectFolder.setEnabled(False)
            self.btnStart.setEnabled(False)
            self.btnStop.setEnabled(True)

    def stop_analysis(self):
        self.stop_thread_signal.emit()
        self.logging("手动停止后台平整度数据分析。", "ERROR")
        self.statusbar.showMessage("已停止平整度自动分析。")
        self.btnSelectFolder.setEnabled(True)
        self.btnStart.setEnabled(True)
        self.btnStop.setEnabled(False)

    def logging(self, message, level="INFO"):
        color = {
            "INFO": "#141414",
            "WARN": "#1414FF",
            "ERROR": "#FF6969"
        }.get(level, "#141414")
        
        now=datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.processLog.appendHtml(f'<div style="color: {color}">[{now}] {message}</div>')
        self.processLog.verticalScrollBar().setValue(self.processLog.verticalScrollBar().maximum())

    def select_folder(self):
        selected_dir = QFileDialog.getExistingDirectory(
            parent=None,          # 父窗口（None表示无父窗口）
            caption="选择文件夹",  # 对话框标题
            dir="",               # 初始目录（空字符串表示系统默认）
            options=QFileDialog.ShowDirsOnly  # 只显示文件夹
        )
        if selected_dir:
            selected_dir = os.path.normpath(selected_dir)
            self.folderPath.setText(selected_dir)
            self.config["dataDirectory"]=selected_dir
            self.save_config()
            self.update_config_signal.emit(self.config)

    def closeEvent(self, event):
        self.stop_thread_signal.emit()
        self.terminate_thread_signal.emit()
        plt.close(self.figure_3d)
        plt.close(self.figure_2d)
        self.analyzer_thread.wait()  # 等待线程结束
        event.accept()

    def exit_application(self):  # 新增的退出应用程序函数
        self.stop_thread_signal.emit()
        self.terminate_thread_signal.emit()
        plt.close(self.figure_3d)
        plt.close(self.figure_2d)
        self.analyzer_thread.wait()  # 等待线程结束
        QApplication.quit()  # 退出应用程序

    def get_axes_limit(self, serialx, serialy):
        # 根据X、Y坐标数据计算图表坐标轴显示范围
        xmin = np.min(serialx)
        xmax = np.max(serialx)
        xavg = (xmin+xmax)/2
        ymin = np.min(serialy)
        ymax = np.max(serialy)
        yavg = (ymin+ymax)/2
        xrange = xmax-xmin
        yrange = ymax-ymin
        if xrange > yrange:
            return xmin, xmax, yavg-yrange*xrange/yrange/2, yavg+yrange*xrange/yrange/2
        else:
            return xavg-xrange*yrange/xrange/2, xavg+xrange*yrange/xrange/2, ymin, ymax

    def create_plot(self, dirpath, filename, data):
        # 使用matplotlib绘制三维曲面图及二维等高线图，并将图形保存到指定路径
        # 提取 x, y, z 坐标
        QCoreApplication.processEvents()
        if self._stop_event:
            return
        x = [point[0] for point in data['pos']]
        y = [point[1] for point in data['pos']]
        z = [point[2] for point in data['pos']]
        minX, maxX, minY, maxY = self.get_axes_limit(x, y)

        # 使用RBF插值函数进行曲面拟合
        func_name = self.config['rbfFunction']
        color_map = self.config['colorMap']
        func = interpolate.Rbf(x, y, z, function=func_name)
        xnew, ynew = np.mgrid[np.min(x):np.max(x):50j, np.min(y):np.max(y):50j]
        znew = func(xnew, ynew)
        znew = znew - znew.min()
        zmax = math.ceil(znew.max()*1000)/1000

        dpi=self.config["plotDPI"]

        # 绘制三维曲面图
        QCoreApplication.processEvents()
        if self._stop_event:
            return
        self.figure_3d.clf()
        ax_3d = Axes3D(self.figure_3d, auto_add_to_figure=False)
        ax_3d.set_title(f"{data['sn']} {data['location']}", fontfamily='SimHei', loc='right')
        ax_3d.set_xlabel('X')
        ax_3d.set_ylabel('Y')
        ax_3d.set_zlabel('Z')
        ax_3d.view_init(elev=60, azim=-70)
        ax_3d.set_xlim(minX, maxX)
        ax_3d.set_ylim(minY, maxY)
        self.figure_3d.add_axes(ax_3d)
        surf = ax_3d.plot_surface(
            xnew, ynew, znew, cmap=color_map, vmin=0, vmax=zmax)
        self.figure_3d.colorbar(surf, shrink=0.6, aspect=10)
        self.figure_3d.canvas.draw()
        plot3d_file=os.path.join(dirpath,f"{filename}_{data['sn']}_{data['location']}_3D.jpg")
        self.figure_3d.savefig(plot3d_file, dpi=dpi, bbox_inches="tight")

        # 创建二维等高线图
        QCoreApplication.processEvents()
        if self._stop_event:
            return
        self.figure_2d.clf()
        ax_2d = self.figure_2d.add_subplot(111)
        ax_2d.set_title(f"{data['sn']} {data['location']}", fontfamily='SimHei')
        ax_2d.set_xlabel('X')
        ax_2d.set_ylabel('Y')
        ax_2d.set_xlim(minX, maxX)
        ax_2d.set_ylim(minY, maxY)
        contour = ax_2d.contourf(xnew, ynew, znew, cmap=color_map, vmin=0, vmax=zmax)
        self.figure_2d.colorbar(contour, shrink=0.8, aspect=10)
        ax_2d.scatter(x, y,  c='r', marker='o')
        self.figure_2d.canvas.draw()
        plot2d_file=os.path.join(dirpath,f"{filename}_{data['sn']}_{data['location']}_2D.jpg")
        self.figure_2d.savefig(plot2d_file, dpi=dpi, bbox_inches="tight")

        self.process_next_signal.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec())
