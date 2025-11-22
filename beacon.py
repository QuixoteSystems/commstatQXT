#!/usr/bin/python
import os
import sqlite3
from configparser import ConfigParser
import re
import time

from PyQt5.QtCore import QDateTime, Qt
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtCore, QtGui, QtWidgets
import random
import datetime
import js8callAPIsupport

serverip = ""
serverport = ""
callsign = ""
grid = ""
selectedgroup = ""

# Global to allow stop later in a different windows
beacon_timer = None


class Ui_FormBeacon(object):
    global beacon_timer
    
    def setupUi(self, FormBeacon):
        self.MainWindow = FormBeacon
        FormBeacon.setObjectName("FormBeacon")
        FormBeacon.resize(835, 215)
        font = QtGui.QFont()
        font.setPointSize(10)
        FormBeacon.setFont(font)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("USA-32.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        FormBeacon.setWindowIcon(icon)
        
        # Text field
        self.label = QtWidgets.QLabel(FormBeacon)
        self.label.setGeometry(QtCore.QRect(75, 15, 650, 81))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setObjectName("label")
        
        # Interval label field
        self.label_2 = QtWidgets.QLabel(FormBeacon)
        self.label_2.setGeometry(QtCore.QRect(75, 125, 350, 20))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        
        # minutes filling field
        self.lineEdit_2 = QtWidgets.QLineEdit(FormBeacon)
        self.lineEdit_2.setGeometry(QtCore.QRect(352, 126, 40, 22))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.lineEdit_2.setFont(font)
        self.lineEdit_2.setMaxLength(4)
        self.lineEdit_2.setObjectName("lineEdit_2")
        
        # Program Button
        self.pushButton = QtWidgets.QPushButton(FormBeacon)
        self.pushButton.setGeometry(QtCore.QRect(441, 176, 75, 24))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.pushButton.setFont(font)
        self.pushButton.setObjectName("pushButton")
        self.pushButton.clicked.connect(self.transmit)
        
        # Stop Button
        self.stopButton = QtWidgets.QPushButton(FormBeacon)
        self.stopButton.setGeometry(QtCore.QRect(541, 176, 75, 24))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.stopButton.setFont(font)
        self.stopButton.setObjectName("stopButton")
        self.stopButton.clicked.connect(self.stop)

        # Cancel Button
        self.cancelButton = QtWidgets.QPushButton(FormBeacon)
        self.cancelButton.setGeometry(QtCore.QRect(641, 176, 75, 24))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.cancelButton.setFont(font)
        self.cancelButton.setObjectName("cancelButton")
        self.cancelButton.clicked.connect(self.MainWindow.close)
        
        # Indicador de estado de la baliza
        self.label_status = QtWidgets.QLabel(FormBeacon)
        self.label_status.setGeometry(QtCore.QRect(75, 156, 250, 20))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_status.setFont(font)
        self.label_status.setObjectName("label_status")


        self.retranslateUi(FormBeacon)
        QtCore.QMetaObject.connectSlotsByName(FormBeacon)

        self.getConfig()
        self.serveripad = serverip
        self.servport = int(serverport)
        self.api = js8callAPIsupport.js8CallUDPAPICalls((self.serveripad),
                                                        int(self.servport))
        
        

        self.MainWindow.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.CustomizeWindowHint |
            QtCore.Qt.WindowTitleHint |
            QtCore.Qt.WindowCloseButtonHint |
            QtCore.Qt.WindowStaysOnTopHint
        )
        
        # QTimer for periodical beacons
        self.beacon_timer = QtCore.QTimer(self.MainWindow)
        self.beacon_timer.setSingleShot(False)  # it repeats
        self.beacon_timer.timeout.connect(self.tx_once)
        
        # Read the current Beacon status
        self.update_beacon_status()


    def retranslateUi(self, FormBeacon):
        _translate = QtCore.QCoreApplication.translate
        FormBeacon.setWindowTitle(_translate("FormBeacon", "Baliza de CommStat QXT"))
        self.lineEdit_2.setText(_translate("FormBeacon", "60"))
        self.label.setText(_translate("FormBeacon", 
                """<html><head/><body><p>Esta baliza es una peticion tipo SNR? (Signal-to-Noise Ratio) y se enviara al Grupo automáticamente </p><p> 
                                         en el intervalo que definas abajo. Por lo que las estaciones que escuchen tu baliza responderán con </p><p>
                                         su nivel de SNR en dB. De esta manera, sabrás que estaciones te escuchan y con que SNR.</p><p><br/></p></body></html>"""))
        
        self.label_2.setText(_translate("FormBeacon", "Intervalo de Transmisión (mínimo cada 60 min) : "))
        self.pushButton.setText(_translate("FormBeacon", "Programar"))
        self.stopButton.setText(_translate("FormBeacon", "Parar"))
        self.cancelButton.setText(_translate("FormBeacon", "Cancelar"))
        self.label_status.setText(_translate("FormBeacon", "Estado baliza: DETENIDA"))
        self.label_status.setStyleSheet("color: red;")
    
    
    def update_beacon_status(self):
        global beacon_timer
        if beacon_timer and beacon_timer.isActive():
            # Baliza activa
            self.label_status.setText("Estado baliza: ACTIVA")
            self.label_status.setStyleSheet("color: green;")
        else:
            # Baliza detenida
            self.label_status.setText("Estado baliza: DETENIDA")
            self.label_status.setStyleSheet("color: red;")


    def getConfig(self):
        global serverip
        global serverport
        global grid
        global callsign
        global selectedgroup
        global state
        if os.path.exists("config.ini"):
            config_object = ConfigParser()
            config_object.read("config.ini")
            userinfo = config_object["USERINFO"]
            systeminfo = config_object["DIRECTEDCONFIG"]
            callsign = format(userinfo["callsign"])
            callsignSuffix = format(userinfo["callsignsuffix"])
            group1 = format(userinfo["group1"])
            group2 = format(userinfo["group2"])
            grid = format(userinfo["grid"])
            path = format(systeminfo["path"])
            serverip = format(systeminfo["server"])
            serverport = format(systeminfo["port"])
            state = format(systeminfo["state"])
            selectedgroup = format(userinfo["selectedgroup"])


    def tx_once(self):
            group = "@"+selectedgroup
            message = f"{group} SNR?"
            messageType = js8callAPIsupport.TYPE_TX_SEND
            messageString = message

            #res = QMessageBox.question(FormBeacon, "Question", "Are you sure?", QMessageBox.Yes | QMessageBox.No)
            msg = QMessageBox()
            msg.setWindowTitle("CommStat QXT Tx")
            msg.setText("La Baliza será : "+message)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
            x = msg.exec_()

            self.sendMessage(messageType, messageString)
            #self.closeapp()

            
    def transmit(self):
        global selectedgroup
        global callsign
        global state
        global beacon_timer
        
        mins = format(self.lineEdit_2.text())
        minutes_str = re.sub(r"[^0-9]+", "", mins)

        if minutes_str == "":
            msg = QMessageBox()
            msg.setWindowTitle("CommStat QXT error")
            msg.setText("Intervalo no válido.")
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
            msg.exec_()
            return

        minutes = int(minutes_str)

        if minutes < 60:
            msg = QMessageBox()
            msg.setWindowTitle("CommStat QXT error")
            msg.setText("Intervalo demasiado corto. Mínimo 60 min")
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
            msg.exec_()
            return

        # intervalo en milisegundos para QTimer
        interval_ms = minutes * 60 * 1000

        print("Starting QXT SNR Beacon...")
        print(f"Sending '@{selectedgroup} SNR?' now and each {minutes} min")

        # 1) Enviar UNA VEZ ahora
        self.tx_once()
        
        beacon_timer = QtCore.QTimer()
        beacon_timer.timeout.connect(self.tx_once)
        # 2) Programar el timer para las siguientes veces
        beacon_timer.start(interval_ms)
        # Updating beacon status
        self.update_beacon_status()

        # Close windows but dont kill loop process
        self.MainWindow.close()
    
    
    
    def stop(self):
        global beacon_timer
        if beacon_timer:
            beacon_timer.stop()
            print("Is it the Beacon Timer active?", beacon_timer.isActive())
            #if not beacon_timer.isActive():
             #   QMessageBox.information(None, "Baliza", "Baliza detenida correctamente")
            #else:
              #  QMessageBox.warning(None, "Baliza", "No se pudo detener la baliza")
        self.update_beacon_status()
        self.MainWindow.close()
        

    def closeapp(self):
        self.MainWindow.close()


    def sendMessage(self, messageType, messageText):
        self.api.sendMessage(messageType, messageText)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    FormBeacon = QtWidgets.QWidget()
    ui = Ui_FormBeacon()
    ui.setupUi(FormBeacon)
    FormBeacon.show()
    sys.exit(app.exec_())
