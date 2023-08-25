class Block:
    def __init__(self, x, y):
        self.address = f"{chr(65+x)}{y+1}"
        self.selected = False
        self.queued = "not queued"
        self.exposed = "not exposed"
        self.rows = [Row(self.address, chr(97 + i)) for i in range(21)]


class Row:
    def __init__(self, block_address, row_id):
        self.address = f"{block_address}{row_id}"
        self.selected = False
        self.queued = "not queued"
        self.exposed = "not exposed"


class Chip:
    def __init__(self, chip_name="Chip01"):
        self.name = chip_name
        self.blocks = [[Block(i, j) for j in range(8)] for i in range(8)]
        self.blocks[0][0].selected = True

    def change_name(self, new_name):
        self.name = new_name
