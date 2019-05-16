from PyQt5.QtWidgets import QApplication

from .gui.main import Window


def run(filepath):
    win = Window(filepath=filepath)
    win.show()        


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    filepath = None
    if (len(sys.argv) == 2):
        filepath = sys.argv[1]    
    run(filepath)
    sys.exit( app.exec_() )
