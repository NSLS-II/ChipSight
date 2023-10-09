from pathlib import Path

import yaml
from qtpy.QtWidgets import QApplication

from gui.chip_widgets import Chip
from gui.main_window import MainWindow

# To run the application
if __name__ == "__main__":
    app = QApplication([])
    with Path("gui_config.yml").open("r") as f:
        config = yaml.load(f, Loader=yaml.Loader)
    chip = Chip()

    main = MainWindow(chip, config=config)
    main.show()

    app.exec_()
