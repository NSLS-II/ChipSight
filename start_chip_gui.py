from qtpy.QtWidgets import QApplication
from gui.chip_widgets import Chip
from gui.main_window import MainWindow


# To run the application
if __name__ == "__main__":
    app = QApplication([])

    chip = Chip()

    main = MainWindow(chip)
    main.show()

    app.exec_()
