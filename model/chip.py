class Block:
    def __init__(self, x, y, num_rows, num_cols):
        self.address = f"{chr(65+x)}{y+1}"
        self.selected = False
        self.queued = "not queued"
        self.exposed = "not exposed"
        self.position = (x, y)
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.rows = [Row(self.address, chr(97 + i)) for i in range(num_rows)]


class Row:
    def __init__(self, block_address, row_id):
        self.address = f"{block_address}{row_id}"
        self.selected = False
        self.queued = "not queued"
        self.exposed = "not exposed"


class Chip:
    def __init__(
        self, chip_name="Chip01", rows=8, columns=8, block_rows=20, block_cols=20
    ):
        self.name = chip_name
        self.rows = rows
        self.columns = columns
        self.blocks: "list[list[Block]]" = [
            [Block(r, c, block_rows, block_cols) for c in range(columns)]
            for r in range(rows)
        ]
        self.blocks[0][0].selected = True

    def change_name(self, new_name):
        self.name = new_name
