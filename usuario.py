from datetime import datetime
from typing import ContextManager
import rpyc
import socket
from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap , QIcon
from datetime import datetime
import sys
import ctypes
import json
import os


class Usuario(QMainWindow):
    ventana_gestionar = 0
    def __init__(self):
        super(Usuario,self).__init__()
        uic.loadUi('usuario.ui' , self)
        self.conexion = None
        self.host = None
        self.puerto = None
            
        self.btn_gestionar.clicked.connect(self.gestionar)
        self.btn_conectar.clicked.connect(self.conectar)
        self.btn_manual.clicked.connect(self.conectar_manual)
        self.btn_respaldo.clicked.connect(self.respaldo)
        self.inicializar()

    def inicializar(self):
        actual = os.path.abspath(os.getcwd())
        actual = actual.replace('\\' , '/')
        ruta = actual + '/madenco logo.png'
        foto = QPixmap(ruta)
        self.lb_logo.setPixmap(foto)
        if os.path.isfile(actual + '/manifest.txt'):
            print('encontrado manifest')
            with open(actual + '/manifest.txt' , 'r', encoding='utf-8') as file:
                lines = file.readlines()
                try:
                    n_host = lines[0].split(':')
                    n_host = n_host[1]
                    host = n_host[:len(n_host)-1]

                    n_port = lines[1].split(':')
                    n_port = n_port[1]
                    port = n_port[:len(n_port)-1]

                    self.host = host
                    self.puerto = port
                except IndexError:
                    pass #si no encuentra alguna linea
        else:
            print('manifest no encontrado')

    def conectar(self):
        try:
            if self.host and self.puerto:
                self.conexion = rpyc.connect(self.host , self.puerto)
                self.lb_conexion.setText('CONECTADO')
            else:
                QMessageBox.about(self,'ERROR', 'Host y puerto no encontrados en el manifest' )

        except ConnectionRefusedError:
            self.lb_conexion.setText('EL SERVIDOR NO RESPONDE')
            
        except socket.error:
            self.lb_conexion.setText('SERVIDOR FUERA DE RED')

    def conectar_manual(self):
        dialog = InputDialog()
        if dialog.exec():
                hostx , puertox = dialog.getInputs()
                try:
                    puertox = int(puertox)
                    self.conexion = rpyc.connect(hostx , puertox)
                    self.lb_conexion.setText('CONECTADO')
                except ValueError:
                    QMessageBox.about(self,'ERROR' ,'Ingrese solo numeros en el PUERTO')
                except ConnectionRefusedError:
                    self.lb_conexion.setText('EL SERVIDOR NO RESPONDE')
                    
                except socket.error:
                    self.lb_conexion.setText('SERVIDOR FUERA DE LA RED')
    def gestionar(self):
        self.hide()
        self.ventana_gestionar = Gestionar(self, self.conexion )
        self.ventana_gestionar.show()

    def respaldo(self):
        
        fecha = datetime.now().strftime("%d-%m-%Y")
        if self.conexion : 
            if self.conexion.root.respaldo(str(fecha)):
                QMessageBox.about(self,'Exito', 'Respaldo hasta: ' + str(fecha) +' generado correctamente en el servidor')
            else: 
                QMessageBox.about(self,'ERROR', 'Se produjo un error al generar el respaldo. Contacte con el soporte')
            
        else:
            QMessageBox.about(self,'ALERTA', 'No ha establecido la conexión con el servidor')



class Gestionar(QMainWindow):

    def __init__(self, parent , conn ):
        super(Gestionar, self).__init__(parent)
        uic.loadUi('gestionar_usuario.ui', self)
        self.conexion = conn
        self.usuarios= []
        self.buscar_usuario()
        self.r_inicio.setDate( datetime.now().date() )
        self.r_termino.setDate( datetime.now().date() )
        self.m_inicio.setDate( datetime.now().date() )
        self.super_no.setChecked(True)
        self.super_no_2.setChecked(True)
        self.r_vendedor.setChecked(True)
        self.r_vendedor_2.setChecked(True)
        self.groupBox_6.hide()
        self.groupBox_2.hide()
        self.btn_registrar.clicked.connect(self.registrar)
        self.btn_actualizar.clicked.connect(self.actualizar)
        self.btn_obtener.clicked.connect(self.obtener)
        self.btn_retirar.clicked.connect(self.retirar)
        self.btn_atras.clicked.connect(self.atras)
        self.r_vendedor.toggled.connect(self.ocultar_personal)
        self.r_personal.toggled.connect(self.ocultar_vendedor)
        self.r_vendedor_2.toggled.connect(self.ocultar_personal_2)
        self.r_personal_2.toggled.connect(self.ocultar_vendedor_2)
        
    def buscar_usuario(self):
        if self.conexion:
            try:
                resultado = self.conexion.root.obtener_usuario_activo()
                self.usuarios = resultado
                for item in resultado:
                    self.box_usuario1.addItem(item[0])
                    self.box_usuario2.addItem(item[0])

            except EOFError:
                QMessageBox.about(self,'CONEXION','No se pudo obtener la lista de dimensionadores. El servidor no responde') 
        
        else:
            QMessageBox.about(self,'CONEXION','No ha establecido conexion con el servidor.') 
        
    def registrar(self):
        if self.conexion:
            nombre = self.txt_nombre.text()
            contra = self.txt_contra.text()
            telefono = self.txt_telefono.text()
            full_nom = self.txt_fullnom1.text()
            tipo = None
            super = 'NO'
            func_area = []
            func_vendedor = [] 

            inicio = self.r_inicio.date()
            inicio = inicio.toPyDate()

            if self.r_dim.isChecked():
                func_area.append('dimensionado')
            if self.r_elab.isChecked():
                func_area.append('elaboracion')
            if self.r_carp.isChecked():
                func_area.append('carpinteria')
            if self.r_pall.isChecked():
                func_area.append('pallets')

            if self.r_manual.isChecked():
                func_vendedor.append('manual')
            if self.r_informes.isChecked():
                func_vendedor.append('informes')

            if self.r_personal.isChecked():
                tipo = 'area'
            if self.r_vendedor.isChecked():
                tipo = 'vendedor'
            #version 5.4 agrego al personal de porteria ... posibles funciones como porteria por agregar.
            if self.r_porteria.isChecked():
                tipo = "porteria"
            formato = {
                        "area" : func_area,
                        "vendedor" : func_vendedor
                    }
            detalle = json.dumps(formato)

            if nombre != '' :
                if contra != '' :
                    if full_nom != '':
                        try:
                            telefono = int(telefono)
                            if self.super_no.isChecked():
                                super = 'NO'
                            if self.super_si.isChecked():
                                super = 'SI'

                            if self.conexion.root.registrar_usuario(nombre,contra ,telefono, str(inicio), super ,tipo, detalle, full_nom ) :
                                QMessageBox.about(self,'EXITO','Usuario registrado correctamente')
                                self.hide()
                                self.parent().show()
                            else:
                                QMessageBox.about(self,'ERROR','Problemas al registrar al usuario en la base de datos.')


                        except ValueError:
                            QMessageBox.about(self,'DATOS ERRONEO','Ingrese solo numeros en el campo telefono')           
                    else:
                        QMessageBox.about(self,'DATOS INCOMPLETOS','Ingrese el nombre completo antes de registrar')
                else: 
                    QMessageBox.about(self,'DATOS INCOMPLETOS','Ingrese una contraseña antes de registrar')           
            else:
                QMessageBox.about(self,'DATOS INCOMPLETOS','Ingrese un nombre antes de registrar') 
        else:
            QMessageBox.about(self,'CONEXION','No ha establecido conexion con el servidor.') 
    

    def obtener(self):
        self.r_dim_2.setChecked(False)
        self.r_elab_2.setChecked(False)
        self.r_carp_2.setChecked(False)
        self.r_pall_2.setChecked(False)
        self.r_manual_2.setChecked(False)
        self.r_informes_2.setChecked(False)
        self.r_vendedor_2.setChecked(True)

        nombre = self.box_usuario1.currentText()
        for datos in self.usuarios:
            if datos[0] == nombre:
                self.m_nombre.setText(datos[0])
                self.m_contra.setText( datos[1])
                self.m_telefono.setText(str(datos[2]))
                aux =   datetime.fromisoformat( str(datos[3]) )  
                self.m_inicio.setDate( aux )

                if datos[4] == 'SI':
                    self.super_si_2.setChecked(True)
                    
                elif datos[4] == 'NO':
                    self.super_no_2.setChecked(True)
                if datos[6] == 'area':
                    self.r_personal_2.setChecked(True)
                    self.r_vendedor_2.setChecked(False)
                detalle = json.loads(datos[7])

                f_area = detalle["area"]
                f_vend = detalle["vendedor"]
                print(f_area)
                print(f_vend)
                
                for i in f_area:
                    if i == 'dimensionado':
                        self.r_dim_2.setChecked(True)
                    if i == 'elaboracion':
                        self.r_elab_2.setChecked(True)
                    if i == 'carpinteria':
                        self.r_carp_2.setChecked(True)
                    if i == 'pallets':
                        self.r_pall_2.setChecked(True)
                for j in f_vend:
                    if j == 'manual':
                        self.r_manual_2.setChecked(True)
                    if j == 'informes':
                        self.r_informes_2.setChecked(True)
                if datos[8]:
                    self.txt_fullnom2.setText(datos[8]) #nombre completo

                break

    def actualizar(self):
        nombre = self.box_usuario1.currentText()

        nuevo_nombre = self.m_nombre.text()
        nueva_contra = self.m_contra.text()
        nuevo_telefono = self.m_telefono.text()
        nuevo_inicio = self.m_inicio.date()
        nuevo_inicio = nuevo_inicio.toPyDate()
        nuevo_full_nom = self.txt_fullnom2.text()

        super = 'NO'
        nro_usuario = 0
        for datos in self.usuarios:
            if datos[0] == nombre:
                nro_usuario = datos[5]
                print(nro_usuario)
                break
        func_area = []
        func_vendedor = [] 
        if self.r_dim_2.isChecked():
            func_area.append('dimensionado')
        if self.r_elab_2.isChecked():
            func_area.append('elaboracion')
        if self.r_carp_2.isChecked():
            func_area.append('carpinteria')
        if self.r_pall_2.isChecked():
            func_area.append('pallets')

        if self.r_manual_2.isChecked():
            func_vendedor.append('manual')
        if self.r_informes_2.isChecked():
            func_vendedor.append('informes')

        if self.r_personal_2.isChecked():
            tipo = 'area'
        if self.r_vendedor_2.isChecked():
            tipo = 'vendedor'
        formato = {
                    "area" : func_area,
                    "vendedor" : func_vendedor
                }
        detalle = json.dumps(formato)
        if self.conexion:
            if self.usuarios:
                if nuevo_nombre != '' :
                    if nueva_contra != '' :
                        try:
                            nuevo_telefono = int(nuevo_telefono)
                            if self.super_si_2.isChecked():
                                super = 'SI'

                            if self.conexion.root.actualizar_usuario(nuevo_nombre,nueva_contra,nuevo_telefono, str(nuevo_inicio), super,tipo,detalle , nro_usuario, nuevo_full_nom ) :
                                QMessageBox.about(self,'EXITO','Usuario ACTUALIZADO correctamente')
                                self.hide()
                                self.parent().show()
                            else:
                                QMessageBox.about(self,'ERROR','No se detectaron cambios. Intente modificando algun dato')
                                
                        except ValueError:
                            QMessageBox.about(self,'DATOS ERRONEO','Ingrese solo numeros en el campo telefono')    
                        except EOFError:
                            QMessageBox.about(self,'CONEXION','El servidor no responde')        

                    else: 
                        QMessageBox.about(self,'DATOS INCOMPLETOS','Ingrese una contraseña antes de registrar')           
                else:
                    QMessageBox.about(self,'DATOS INCOMPLETOS','Ingrese un nombre antes de registrar') 
            else:
                QMessageBox.about(self,'ERROR','No se encontraron usuarios ACTIVOS') 
        else:
            QMessageBox.about(self,'CONEXION','No ha establecido conexion con el servidor.') 
    def retirar(self):
        nombre = self.box_usuario2.currentText()    
        termino = self.r_termino.date().toPyDate()   
        nro_usuario = 0
        for datos in self.usuarios:
            if datos[0] == nombre:
                nro_usuario = datos[5]
                print(nro_usuario)
                break

        if self.conexion:
            if self.usuarios:
                try:
                    if self.conexion.root.retirar_usuario(nro_usuario , str( termino ) ):
                        QMessageBox.about(self,'EXITO','Usuario RETIRADO correctamente')
                        self.hide()
                        self.parent().show()
                    else:
                        QMessageBox.about(self,'ERROR','El usuario no se retiro correctamente. Analisar posibles causas...')     

                except EOFError:
                    QMessageBox.about(self,'CONEXION','El servidor no responde')     
            else: 
                QMessageBox.about(self,'ERROR','No se encontraron usuarios ACTIVOS') 
        else:
            QMessageBox.about(self,'CONEXION','No ha establecido conexion con el servidor.') 

    def ocultar_personal(self):
        if self.r_vendedor.isChecked():
            self.groupBox.show()
            self.groupBox_2.hide()
    def ocultar_vendedor(self):
        if self.r_personal.isChecked():
            self.groupBox.hide()
            self.groupBox_2.show()
    def ocultar_personal_2(self):
        if self.r_vendedor_2.isChecked():
            self.groupBox_5.show()
            self.groupBox_6.hide()
    def ocultar_vendedor_2(self):
        if self.r_personal_2.isChecked():
            self.groupBox_5.hide()
            self.groupBox_6.show()

    def atras(self):
        self.hide()
        self.parent().show()

class InputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.host = QLineEdit(self)
        self.puerto = QLineEdit(self)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self);

        layout = QFormLayout(self)
        layout.addRow("HOST:", self.host)
        layout.addRow("PUERTO:", self.puerto)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        return self.host.text(), self.puerto.text()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('usuario_logo.ico')) 
   
    myappid = 'madenco.usuario' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid) 
    usuario = Usuario()
    usuario.show()
    sys.exit(app.exec_())
