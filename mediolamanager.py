#!/usr/bin/env python

import sys
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtCore import QThread, pyqtSignal, QObject, pyqtSlot, QTimer
from PyQt5.QtWidgets import QTableWidgetItem, QDialog
import requests
import json

class addDevice(QtWidgets.QDialog):
    def __init__(self, parent):
        super(addDevice, self).__init__(parent)
        uic.loadUi('adddevice.ui', self)
        self.hideAllGroups()
        self.findChild(QObject, 'comboDeviceType').currentTextChanged.connect(self.deviceTypeChanged)
        self.findChild(QObject, 'btnClose').clicked.connect(self.hide)
        self.deviceTypeChanged(self.findChild(QObject, 'comboDeviceType').currentText())
        
    def hideAllGroups(self):
        self.findChild(QObject, 'groupElero').setVisible(False)
        self.findChild(QObject, 'groupSomfy').setVisible(False)
        self.findChild(QObject, 'groupIntertechno').setVisible(False)
        
    def deviceTypeChanged(self, text):
        self.hideAllGroups()
        if text == 'Elero':
            self.findChild(QObject, 'groupElero').setVisible(True)
        elif text == 'Intertechno':
            self.findChild(QObject, 'groupIntertechno').setVisible(True)
        elif text == 'Somfy':
            self.findChild(QObject, 'groupSomfy').setVisible(True)
    


class eleroManager(QtWidgets.QDialog):
    def __init__(self, parent):
        super(eleroManager, self).__init__(parent)
        self.ui = parent
        uic.loadUi('eleromanager.ui', self)
        self.findChild(QObject, 'btnClose').clicked.connect(self.hide)
        self.findChild(QObject, 'btnUp').clicked.connect(self.btnUpClicked)
        self.findChild(QObject, 'btnDown').clicked.connect(self.btnDownClicked)
        self.findChild(QObject, 'btnStop').clicked.connect(self.btnStopClicked)
        self.findChild(QObject, 'btnLearn').clicked.connect(self.btnLearnClicked)

    def getChannel(self):   
        idx = self.findChild(QObject, 'comboChannel').currentIndex()
        channel = format(idx+1, 'x')
        return channel

    def btnUpClicked(self):
        channel = self.getChannel()
        data = '0' + channel + '01'
        payload = {
            'type' : 'ER',
            'data' : data 
            }
        self.ui.sendRequest('SendSC', payload)
        
    def btnStopClicked(self):
        channel = self.getChannel()
        data = '0' + channel + '02'
        payload = {
            'type' : 'ER',
            'data' : data
            }
        self.ui.sendRequest('SendSC', payload)
    
    def btnDownClicked(self):
        channel = self.getChannel()
        data = '0' + channel + '00'
        payload = {
            'type' : 'ER',
            'data' : data
            }
        self.ui.sendRequest('SendSC', payload)
        
    def btnLearnClicked(self, checked):
        if checked:
            cmd = 'LearnSC'
        else:
            cmd = 'stopLearn'
        channel = self.getChannel()
        adr = '0' + channel
        payload = {
            'type' : 'ER',
            'adr' : adr
            }
        self.ui.sendRequest(cmd, payload)

    def closeEvent(self, event):
        self.hide()
        event.ignore()

class Ui(QtWidgets.QMainWindow):
    def __init__(self):

        super(Ui, self).__init__()
        uic.loadUi('mediolamanager.ui', self)
        btnConnect = self.findChild(QObject, 'btnConnect')
        btnConnect.clicked.connect(self.connect)
        btnEleroManager = self.findChild(QObject, 'btnEleroManager')
        btnEleroManager.clicked.connect(self.eleroManager)
        btnAddDevice = self.findChild(QObject, 'btnAddDevice')
        btnAddDevice.clicked.connect(self.addDevice)
        btnDelDevice = self.findChild(QObject, 'btnDeleteDevice')
        btnDelDevice.clicked.connect(self.delDevice)
        self.version = 4
        self.url = ''
        self.devices = []
        self.show()
        self.eleroManager = eleroManager(self)
        self.addDevice = addDevice(self)
        self.gatewayDisconnected()
        
    def gatewayDisconnected(self):
        self.findChild(QObject, 'btnEleroManager').setEnabled(False)
        self.findChild(QObject, 'btnAddDevice').setEnabled(False)
        self.findChild(QObject, 'btnDeleteDevice').setEnabled(False)
        self.findChild(QObject, 'btnConnect').setChecked(False)
        self.findChild(QObject, 'editHostname').setEnabled(True)
        self.findChild(QObject, 'tblDevices').clear()
        
    def gatewayConnected(self):
        self.findChild(QObject, 'btnEleroManager').setEnabled(True)
        self.findChild(QObject, 'btnAddDevice').setEnabled(True)
        self.findChild(QObject, 'btnDeleteDevice').setEnabled(True)
        self.findChild(QObject, 'statusbar').showMessage('Connected.')
        self.findChild(QObject, 'editHostname').setEnabled(False)
    
    def addDevice(self):
        self.addDevice.show()
        
    def delDevice(self):
        pass
        
    def eleroManager(self):
        self.eleroManager.show()
    
    def parseResponse(self, text):
        ret = {}
        res = False
        if self.version == 4:
            if text.startswith('{XC_SUC}'):
                text = text.replace('{XC_SUC}', '')
                if len(text) > 0:
                    ret = json.loads(text)
                res = True
            elif text.startswith('{XC_ERR}'):
                text = text.replace('{XC_ERR}', '')
                ret = text
                res = False
        elif self.version == 5:
            ret = json.loads(text)
            if 'XC_SUC' in ret:
                ret = ret['XC_SUC']
                res = True
            else:
                ret = ret['XC_ERR']
                res = False
        return res, ret
        
    
    def connect(self, checked):
        if checked:
            hostname = self.findChild(QObject, 'editHostname').text()
            if hostname == '':
                self.findChild(QObject, 'btnConnect').setChecked(False)
                return
            version = self.findChild(QObject, 'comboVersion').currentText()
            if version == 'v4/v4+':
                self.version = 4
                self.url = 'http://' + hostname + '/command'
            elif version == 'v5/v5+':
                self.version = 5
                self.url = 'http://' + hostname + '/cmd'

            status, message = self.sendRequest('GetSI')
            if status:
                self.gatewayConnected()
                print('Connected.')

                info = 'MAC: ' + message['MAC'] + '\n'
                info += 'HW: ' + message['HWV'] + '\n'
                info += 'SW: ' + message['VER'] + '\n'
                self.findChild(QObject, 'textInformation').clear()
                self.findChild(QObject, 'textInformation').append(info)
                self.getDevices()
            else:
                print('Error connecting to Gateway')
                self.findChild(QObject, 'statusbar').showMessage('Error connecting to Gateway')
                self.gatewayDisconnected()
                
        else:
            self.findChild(QObject, 'textInformation').clear()
            self.findChild(QObject, 'statusbar').showMessage('Disconnected.')
            self.gatewayDisconnected()

    def sendRequest(self, command, data = None):
        print('sendRequest')
        print(command)
        print(data)
        payload = { 'XC_FNC' : command }
        if data:
            payload.update(data)
        print(payload)
        try:
            response = requests.get(self.url, params=payload, headers={'Connection':'close'})
        except:
            return False, ''
        message = ''
        if response.status_code == 200:
            res, message = self.parseResponse(response.text)
        else:
            res = False
        return res, message

    def getDevices(self):
        status, message = self.sendRequest('GetStates')
        if status:
            self.devices = message
            count = len(message)
            if count > 0:
                offset = 0
                if message[0]['type'] == 'EVENT':
                    print('EVENT')
                    count = count-1
                    offset = 1
                tab = self.findChild(QObject, 'tblDevices')
                tab.setRowCount(count)
                tab.setColumnCount(3)
                tab.setHorizontalHeaderItem(0, QTableWidgetItem('Type'))
                tab.setHorizontalHeaderItem(1, QTableWidgetItem('Address'))
                tab.setHorizontalHeaderItem(2, QTableWidgetItem('State'))
                for ii in range(offset, count+offset):
                    tab.setItem(ii-offset, 0, QTableWidgetItem(message[ii]['type']))
                    tab.setItem(ii-offset, 1, QTableWidgetItem(message[ii]['adr']))
                    tab.setItem(ii-offset, 2, QTableWidgetItem(message[ii]['state']))
                    
                


app = QtWidgets.QApplication(sys.argv)

window = Ui()
sys.exit(app.exec_())
