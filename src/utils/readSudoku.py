def read_sudoku(filename):
    with open(filename, 'r') as file:
        return [
            [int(num) for num in line.split()]
            for line in file
            if line.strip()
        ]