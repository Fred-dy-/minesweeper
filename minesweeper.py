'''
Created on 12 Jun 2017

@author: fgurkov1
'''
from typing import List
from random import shuffle, sample
from unicodedata import east_asian_width

class Cell(object):
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.mine = False
        self.open = False
        self.flagged = False
        self.neighbour_mines = 0
        

class TerminalUI(object):

    def __init__(self):
        pass

    def to_char(self, cell, reveal):
        if reveal or cell.open:
            if cell.mine:
                return "X"
            if cell.neighbour_mines == 0:
                return " "
            else:
                return str(cell.neighbour_mines)
        elif cell.flagged:
            return "F"
        else:
            return "."
    
    def display_board(self, board:List[List[Cell]], reveal:bool = False):
        text = "\n".join(["".join([self.to_char(cell, reveal) for cell in row]) for row in board])
        print(text)
        
    def display_result(self, won:bool):
        if won:
            print("Congratulations! You've won!")
        else:
            print("You lost. Better luck next time!")
            
    def take_input(self, board, width, height):
        text = input("Your turn. Input action x y: ")
        action, tx, ty = text.split(" ")
        x, y = int(tx), int(ty)
        """
        action = input("Enter action (toggle, open, force): ")
        x = int(input(f"Enter the x coordinate (0<=x<{width}): "))
        y = int(input(f"Enter the y coordinate (0<=y<{height}): "))
        """
        return action, x, y

    def invalid_input(self, action, x, y):
        print(f"Cannot {action} at ({x}, {y}). Try again.\n")
class MineSweeper(object):
    '''
    Classic MineSweeper game
    '''
    hardness = [10, 20, 40]

    def __init__(self, width:int, height:int, level:int, ui=TerminalUI()):
        self.width = width
        self.height = height
        self.level = level
        self.mines = MineSweeper.hardness[self.level] * self.width * self.height // 100
        self.flags = 0
        self.open_cells = 0
        self.blowed_up = False
        self.ui = ui
        self.create_board()
        self.set_mines()
        
    def game_loop(self):
        while not self.game_over():
            self.show_board()
            action, x, y = self.take_input()
            while not self.process(action, x, y):
                self.invalid_input(action, x, y)
                action, x, y = self.take_input()
        self.show_board(reveal = True)
        self.display_result()
        
    def create_board(self):
        self.board = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(Cell(x, y))
            self.board.append(row)
    
    def set_mines(self):
        addresses = sample([a for a in range(self.width * self.height)], self.mines)
        for address in addresses:
            x, y = address % self.width, address // self.width
            cell = self.board[y][x]
            cell.mine = True
            for neighbour in self.neighbours(cell):
                neighbour.neighbour_mines += 1
        
    def neighbours(self, cell):
        n = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                nx, ny = cell.x + dx, cell.y + dy
                if not (dx == 0 and dy == 0) and 0 <= nx < self.width and 0 <= ny < self.height:
                    n.append(self.board[ny][nx]) 
        return n

    def show_board(self, reveal:bool = False):
        self.ui.display_board(self.board, reveal)
        
    def take_input(self):
        return self.ui.take_input(self.board, self.width, self.height)
    
    def invalid_input(self, action, x, y):
        self.ui.invalid_input(action, x, y)
    
    def process(self, action, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            cell = self.board[y][x]
            if action == "toggle":
                return self.process_toggle(cell)
            elif action == "open":
                return self.process_open(cell)
            elif action == "force":
                return self.process_force(cell)
        return False
    
    def process_toggle(self, cell):
        if cell.open:
            return False
        elif cell.flagged:
            self.flags -= 1
            cell.flagged = False
            return True
        else:
            self.flags += 1
            cell.flagged = True
            return True
    
    def process_open(self, cell):
        if cell.open or cell.flagged:
            return False
        else:
            cell.open = True
            self.open_cells += 1
            if cell.mine:
                self.blowed_up = True
            elif cell.neighbour_mines == 0:
                self.open_area(cell)
            return True
        
    def process_force(self, cell):
        if not cell.open or cell.flagged:
            return False
        neighbour_flags = sum([1 for n in self.neighbours(cell) if n.flagged])
        if cell.neighbour_mines == neighbour_flags:
            cell.open = True
            self.open_cells += 1
            if cell.mine:
                self.blowed_up = True
            else:
                self.open_area(cell)
            return True
        else:
            return False
        
    def open_area(self, cell):
        queue = [cell]
        while len(queue):
            cell = queue.pop(0)
            for neighbour in self.neighbours(cell):
                if not neighbour.mine:
                    neighbour_flags = sum([1 for n in self.neighbours(neighbour) if n.flagged])
                    if neighbour.neighbour_mines == neighbour_flags and not neighbour.open and not neighbour.flagged:
                        queue.append(neighbour) 
                if not neighbour.open and not neighbour.flagged:
                    self.open_cells += 1
                    neighbour.open = True
                    
    def game_over(self):
        return self.blowed_up or self.width * self.height - self.open_cells == self.mines
    
    def display_result(self):
        self.ui.display_result(not self.blowed_up)

if __name__ == "__main__":
    game = MineSweeper(10, 10, 0)
    game.game_loop()