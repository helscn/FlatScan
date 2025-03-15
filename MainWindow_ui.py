# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MainWindow.ui'
##
## Created by: Qt User Interface Compiler version 6.5.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QPlainTextEdit, QPushButton, QSizePolicy,
    QStatusBar, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(611, 417)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.folderPath = QLineEdit(self.centralwidget)
        self.folderPath.setObjectName(u"folderPath")
        self.folderPath.setEnabled(False)

        self.horizontalLayout.addWidget(self.folderPath)

        self.btnSelectFolder = QPushButton(self.centralwidget)
        self.btnSelectFolder.setObjectName(u"btnSelectFolder")

        self.horizontalLayout.addWidget(self.btnSelectFolder)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.processLog = QPlainTextEdit(self.centralwidget)
        self.processLog.setObjectName(u"processLog")
        self.processLog.setReadOnly(True)

        self.horizontalLayout_3.addWidget(self.processLog)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(60)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.btnStart = QPushButton(self.centralwidget)
        self.btnStart.setObjectName(u"btnStart")

        self.horizontalLayout_2.addWidget(self.btnStart)

        self.btnStop = QPushButton(self.centralwidget)
        self.btnStop.setObjectName(u"btnStop")

        self.horizontalLayout_2.addWidget(self.btnStop)

        self.btnExit = QPushButton(self.centralwidget)
        self.btnExit.setObjectName(u"btnExit")

        self.horizontalLayout_2.addWidget(self.btnExit)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"\u5e73\u6574\u5ea6\u6570\u636e\u6587\u4ef6\u5939\uff1a", None))
        self.btnSelectFolder.setText(QCoreApplication.translate("MainWindow", u"\u9009\u62e9...", None))
        self.btnStart.setText(QCoreApplication.translate("MainWindow", u"\u81ea\u52a8\u5206\u6790\u5e73\u6574\u5ea6", None))
        self.btnStop.setText(QCoreApplication.translate("MainWindow", u"\u505c\u6b62\u5206\u6790\u5e73\u6574\u5ea6", None))
        self.btnExit.setText(QCoreApplication.translate("MainWindow", u"\u5173\u95ed\u7a0b\u5e8f", None))
    # retranslateUi

