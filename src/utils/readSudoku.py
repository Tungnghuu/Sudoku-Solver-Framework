def read_sudoku(filename):
    board = []
    
    with open(filename, 'r') as file:
        for line in file:
            # Skip empty lines
            if not line.strip():
                continue
                
            # Split the line, then convert each string into an integer
            row = []
            for num_str in line.split():
                row.append(int(num_str))
            
            board.append(row)
            
    return board