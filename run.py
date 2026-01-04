import sys
from PyQt5 import QtWidgets
from homepage import MainWindow

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = MainWindow()
    ui.setupUi(Form)
    Form.setWindowTitle("日志检测系统")
    Form.show()
    sys.exit(app.exec_())
