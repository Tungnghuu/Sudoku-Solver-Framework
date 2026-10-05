from pysat.formula import CNF

def value(row, collumn, digit, n):
    return (n * n) * (row - 1) + n * (collumn - 1) + digit

def getSudokuFormula(n):
    formula = CNF()
    b = int(n ** 0.5) # b is the block size (e.g. 3 for a 9x9 board)

    # 1. CELL
    for row in range(1, n + 1):
        for collumn in range(1, n + 1):
            # ALO
            formula.append([value(row, collumn, d, n) for d in range(1, n + 1)])

            # AMO
            for digit1 in range(1, n + 1):
                for digit2 in range(digit1 + 1, n + 1):
                    formula.append([-value(row, collumn, digit1, n), -value(row, collumn, digit2, n)])

    # 2. ROW
    for row in range(1, n + 1):
        for digit in range(1, n + 1):
            # ALO
            formula.append([value(row, c, digit, n) for c in range(1, n + 1)])

            # AMO
            for collumn1 in range(1, n + 1):
                for collumn2 in range(collumn1 + 1, n + 1):
                    formula.append([-value(row, collumn1, digit, n), -value(row, collumn2, digit, n)])

    # 3. COLLUMN
    for collumn in range(1, n + 1):
        for digit in range(1, n + 1):
            # ALO
            formula.append([value(r, collumn, digit, n) for r in range(1, n + 1)])

            # AMO
            for row1 in range(1, n + 1):
                for row2 in range(row1 + 1, n + 1):
                    formula.append([-value(row1, collumn, digit, n), -value(row2, collumn, digit, n)])

    # 4. BLOCK
    for block_row in range(b):
        for block_column in range(b):
            cells = []
            for row in range(1 + b * block_row, 1 + b * block_row + b):
                for column in range(1 + b * block_column, 1 + b * block_column + b):
                    cells.append((row, column))

            for digit in range(1, n + 1):
                # ALO:
                formula.append([ value(row, column, digit, n) for row, column in cells ])
                # AMO:
                for i in range(n):
                    for j in range(i + 1, n):
                        row1, column1 = cells[i]
                        row2, column2 = cells[j]
                        formula.append([ -value(row1, column1, digit, n), -value(row2, column2, digit, n) ])
    return formula