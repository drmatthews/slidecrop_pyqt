from PyQt5.QtWidgets import QApplication

from slidecrop.gui.main import Window


def run():
    win = Window()
    win.show()        

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    run()
    sys.exit( app.exec_() )
