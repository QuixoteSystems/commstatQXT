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
beacon_owner = None  # To store who send the tx_once()


# Notificacion tipo Toast
class Toast(QtWidgets.QWidget):
    def __init__(self, message, parent=None, duration=3000, icon_path=None):
        super().__init__(parent)

        # Ventana sin bordes
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.X11BypassWindowManagerHint
        )

        # Fondo normal (sin transparencia)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)

        # ---- CONTENEDOR PRINCIPAL ----
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        self.setLayout(layout)

        # ---- ICONO ----
        if icon_path is not None:
            pixmap = QtGui.QPixmap(icon_path)
            icon_label = QtWidgets.QLabel()
            icon_label.setPixmap(pixmap.scaled(24, 24, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
            layout.addWidget(icon_label)

        # ---- TEXTO ----
        text_label = QtWidgets.QLabel(message)
        text_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
            }
        """)
        layout.addWidget(text_label)

        # ---- ESTILO DEL TOAST ----
        self.setStyleSheet("""
            QWidget {
                background-color: rgb(0, 150, 0); /* Verde sólido */
                border-radius: 8px;
            }
        """)

        self.adjustSize()

        # Timer para cerrar
        QtCore.QTimer.singleShot(duration, self.close)

    def show_at(self, parent_widget):
        parent_rect = parent_widget.geometry()

        # 20 px desde el borde derecho e inferior
        x = parent_rect.x() + parent_rect.width() - self.width() - 20
        y = parent_rect.y() + parent_rect.height() - self.height() - 20

        self.move(x, y)
        self.show()



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
        
        # Read the current Beacon status
        self.update_beacon_status()


    def retranslateUi(self, FormBeacon):
        global beacon_timer
        _translate = QtCore.QCoreApplication.translate
        FormBeacon.setWindowTitle(_translate("FormBeacon", "Baliza de CommStat QXT"))
        self.lineEdit_2.setText(_translate("FormBeacon", "60" ))
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
            interval = beacon_timer.interval() / 60000
            # Baliza activa
            self.label_status.setText(f"Estado baliza: ACTIVA cada {int(interval)} min")
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
    
    
    def show_auto_msg(self, message):
        # Si ya hay un mensaje anterior, lo cerramos
        if hasattr(self, "msg_box") and self.msg_box is not None:
            self.msg_box.close()

        # Creamos y guardamos la referencia en self
        self.msg_box = QMessageBox(self.MainWindow)  # o None si ya cerraste esa ventana
        self.msg_box.setWindowTitle("CommStat QXT Tx")
        self.msg_box.setText("Baliza enviada: " + message)
        self.msg_box.setIcon(QMessageBox.Information)
        self.msg_box.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        self.msg_box.setStandardButtons(QMessageBox.Ok)

        self.msg_box.show()

        # Cerrar automáticamente a los 60 segundos (60000 ms)
        QtCore.QTimer.singleShot(60000, self.msg_box.accept)


    #from PyQt5 import QtWidgets

    def tx_once(self):
        global selectedgroup

        group = "@" + selectedgroup
        message = f"{group} SNR?"
        messageType = js8callAPIsupport.TYPE_TX_SEND

        # 1) Enviar la baliza
        self.sendMessage(messageType, message)

        # 2) Intentar localizar la ventana principal (QMainWindow)
        mainwin = None
        for w in QtWidgets.QApplication.topLevelWidgets():
            if isinstance(w, QtWidgets.QMainWindow):
                mainwin = w
                break

        # 3) Si no encontramos QMainWindow, usar la ventana de beacon como fallback
        if mainwin is None:
            mainwin = self.MainWindow

        # 4) Crear el toast SIEMPRE antes de usarlo
        toast = Toast(
            message=f"Baliza enviada: {message}",
            parent=mainwin,
            duration=10000,
            icon_path="icon_ok.png"
        )
        toast.show_at(mainwin)



    def transmit(self):
        global selectedgroup
        global callsign
        global state
        global beacon_timer, beacon_owner
            
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

        interval_ms = minutes * 60 * 1000

        print("Starting QXT SNR Beacon...")
        print(f"Sending '@{selectedgroup} SNR?' now and each {minutes} min")

        # 1) Enviar una vez ahora
        self.tx_once()

        # 2) Crear el timer global si no existe
        if beacon_timer is None:
            beacon_timer = QtCore.QTimer()     # SIN padre
            beacon_timer.setSingleShot(False)
            beacon_timer.timeout.connect(self.tx_once)
            beacon_owner = self  # guardamos referencia para que no lo recoja el GC

        # 3) Arrancar/actualizar intervalo
        beacon_timer.start(interval_ms)

        # 4) Actualizar el status visual
        self.update_beacon_status()

        # 5) Cerrar solo la ventana de beacon (el timer sigue vivo)
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
