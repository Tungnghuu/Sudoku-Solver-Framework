import math
from pysat.formula import CNF

def value(row, column, digit, n):
    return (n * n) * (row - 1) + n * (column - 1) + digit

def add_amo(formula, literals, encoding, top_id):
    if encoding == "pairwise":
        # Compare every pair
        for index, first in enumerate(literals):
            for second in literals[index + 1:]:
                # Add clause: both cannot be true at the same time
                formula.append([-first, -second])
        return top_id

    if encoding == "seqcounter":
        from pysat.card import CardEnc, EncType

        # Use PySAT CardEnc to generate At-Most-One clauses efficiently
        encoded = CardEnc.atmost(
            lits = literals,
            bound = 1,
            encoding = EncType.seqcounter,
            top_id = top_id,
        )

        # Add to formula list
        formula.extend(encoded.clauses)
        return encoded.nv

def getSudokuFormula(n, amo_encoding="pairwise"):
    formula = CNF()
    b = int(math.isqrt(n)) # b is the block size (e.g. 3 for a 9x9 board)
    top_id = n ** 3

    # 1. CELL
    for row in range(1, n + 1):
        for column in range(1, n + 1):
            cells = [
                value(row, column, digit, n) for digit in range(1, n + 1)
            ]
            formula.append(cells)
            top_id = add_amo(formula, cells, amo_encoding, top_id)

    # 2. ROW
    for row in range(1, n + 1):
        for digit in range(1, n + 1):
            rows = [
                value(row, c, digit, n) for c in range(1, n + 1)
            ]
            formula.append(rows)
            top_id = add_amo(formula, rows, amo_encoding, top_id)

    # 3. COLLUMN
    for column in range(1, n + 1):
        for digit in range(1, n + 1):
            columns = [
                value(r, column, digit, n) for r in range(1, n + 1)
            ]
            formula.append(columns)
            top_id = add_amo(formula, columns, amo_encoding, top_id)

    # 4. BLOCK
    for block_row in range(0, n, b):
        for block_column in range(0, n, b):
            for digit in range(1, n + 1):
                blocks = [
                    value(r, c, digit, n)
                    for r in range(block_row + 1, block_row + b + 1)
                    for c in range(block_column + 1, block_column + b + 1)
                ]
                formula.append(blocks)
                top_id = add_amo(formula, blocks, amo_encoding, top_id)

    return formula