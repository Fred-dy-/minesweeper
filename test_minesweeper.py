import unittest
from unittest.mock import patch
from minesweeper import Cell, TerminalUI, MineSweeper


def make_game(width, height, mine_coords):
    """Create a MineSweeper game with controlled mine placement."""
    with patch.object(MineSweeper, 'set_mines'):
        game = MineSweeper(width, height, 0)
    game.mines = len(mine_coords)
    for x, y in mine_coords:
        game.board[y][x].mine = True
    for row in game.board:
        for cell in row:
            cell.neighbour_mines = sum(1 for n in game.neighbours(cell) if n.mine)
    return game


class TestCell(unittest.TestCase):

    def test_initial_state(self):
        cell = Cell(3, 5)
        self.assertEqual(cell.x, 3)
        self.assertEqual(cell.y, 5)
        self.assertFalse(cell.mine)
        self.assertFalse(cell.open)
        self.assertFalse(cell.flagged)
        self.assertEqual(cell.neighbour_mines, 0)


class TestNeighbours(unittest.TestCase):

    def setUp(self):
        self.game = make_game(3, 3, [])

    def test_corner_has_3_neighbours(self):
        self.assertEqual(len(self.game.neighbours(self.game.board[0][0])), 3)

    def test_edge_has_5_neighbours(self):
        self.assertEqual(len(self.game.neighbours(self.game.board[0][1])), 5)

    def test_center_has_8_neighbours(self):
        self.assertEqual(len(self.game.neighbours(self.game.board[1][1])), 8)

    def test_neighbour_coordinates_are_correct(self):
        game = make_game(5, 5, [])
        center = game.board[2][2]
        coords = {(n.x, n.y) for n in game.neighbours(center)}
        expected = {(1,1),(2,1),(3,1),(1,2),(3,2),(1,3),(2,3),(3,3)}
        self.assertEqual(coords, expected)


class TestSetMines(unittest.TestCase):

    def test_mine_is_placed(self):
        game = make_game(3, 3, [(1, 1)])
        self.assertTrue(game.board[1][1].mine)

    def test_neighbour_mines_counted_correctly(self):
        # Mine in center of 3x3: all 8 surrounding cells should have neighbour_mines == 1
        game = make_game(3, 3, [(1, 1)])
        for row in game.board:
            for cell in row:
                if not cell.mine:
                    self.assertEqual(cell.neighbour_mines, 1)

    def test_corner_mine_only_affects_adjacent_cells(self):
        game = make_game(3, 3, [(0, 0)])
        self.assertEqual(game.board[0][1].neighbour_mines, 1)
        self.assertEqual(game.board[1][0].neighbour_mines, 1)
        self.assertEqual(game.board[1][1].neighbour_mines, 1)
        self.assertEqual(game.board[0][2].neighbour_mines, 0)
        self.assertEqual(game.board[2][0].neighbour_mines, 0)


class TestProcessOpen(unittest.TestCase):

    def test_open_safe_cell(self):
        # Mine at (1,1) is adjacent to (0,0), so (0,0).neighbour_mines == 1
        # and opening it does not trigger flood-fill
        game = make_game(3, 3, [(1, 1)])
        result = game.process_open(game.board[0][0])
        self.assertTrue(result)
        self.assertTrue(game.board[0][0].open)
        self.assertEqual(game.open_cells, 1)

    def test_open_mine_sets_blowed_up(self):
        game = make_game(3, 3, [(1, 1)])
        result = game.process_open(game.board[1][1])
        self.assertTrue(result)
        self.assertTrue(game.blowed_up)

    def test_cannot_open_already_open_cell(self):
        game = make_game(3, 3, [])
        game.board[0][0].open = True
        result = game.process_open(game.board[0][0])
        self.assertFalse(result)
        self.assertEqual(game.open_cells, 0)

    def test_cannot_open_flagged_cell(self):
        game = make_game(3, 3, [])
        game.board[0][0].flagged = True
        result = game.process_open(game.board[0][0])
        self.assertFalse(result)

    def test_opening_zero_cell_triggers_flood_fill(self):
        # Mine only at (0,0); opening (4,4) should flood-fill many cells
        game = make_game(5, 5, [(0, 0)])
        game.process_open(game.board[4][4])
        self.assertGreater(game.open_cells, 1)


class TestProcessToggle(unittest.TestCase):

    def test_flag_closed_cell(self):
        game = make_game(3, 3, [])
        result = game.process_toggle(game.board[0][0])
        self.assertTrue(result)
        self.assertTrue(game.board[0][0].flagged)
        self.assertEqual(game.flags, 1)

    def test_unflag_flagged_cell(self):
        game = make_game(3, 3, [])
        game.board[0][0].flagged = True
        game.flags = 1
        result = game.process_toggle(game.board[0][0])
        self.assertTrue(result)
        self.assertFalse(game.board[0][0].flagged)
        self.assertEqual(game.flags, 0)

    def test_cannot_toggle_open_cell(self):
        game = make_game(3, 3, [])
        game.board[0][0].open = True
        result = game.process_toggle(game.board[0][0])
        self.assertFalse(result)
        self.assertFalse(game.board[0][0].flagged)


class TestProcessForce(unittest.TestCase):

    def setUp(self):
        # 3x3 board, mine at (0,1). Center (1,1) is open with neighbour_mines == 1.
        self.game = make_game(3, 3, [(0, 1)])
        self.center = self.game.board[1][1]
        self.center.open = True
        self.game.open_cells = 1
        self.game.board[1][0].flagged = True  # flag the mine

    def test_force_returns_true_when_flags_match(self):
        self.assertTrue(self.game.process_force(self.center))

    def test_force_opens_unflagged_neighbours(self):
        self.game.process_force(self.center)
        for n in self.game.neighbours(self.center):
            if not n.mine and not n.flagged:
                self.assertTrue(n.open)

    def test_force_does_not_open_flagged_cells(self):
        self.game.process_force(self.center)
        self.assertFalse(self.game.board[1][0].open)

    def test_force_does_not_double_count_center_cell(self):
        self.game.process_force(self.center)
        actual_open = sum(1 for row in self.game.board for cell in row if cell.open)
        self.assertEqual(self.game.open_cells, actual_open)

    def test_force_fails_on_closed_cell(self):
        game = make_game(3, 3, [(0, 1)])
        self.assertFalse(game.process_force(game.board[1][1]))

    def test_force_fails_when_flags_dont_match(self):
        game = make_game(3, 3, [(0, 1)])
        game.board[1][1].open = True
        # mine not flagged → flags (0) != neighbour_mines (1)
        self.assertFalse(game.process_force(game.board[1][1]))

    def test_force_on_mine_with_wrong_flags_sets_blowed_up(self):
        # If a player incorrectly flags a safe cell and forces, a mine gets opened
        game = make_game(3, 3, [(0, 1), (0, 0)])
        center = game.board[1][1]
        center.open = True
        game.open_cells = 1
        # Flag a non-mine cell instead of the actual mine at (0,1)
        game.board[0][1].flagged = True  # (0,1) is the mine — wait, let me recalculate
        # (0,1) is (x=0, y=1) — that IS a mine. Let's flag a safe cell instead.
        game2 = make_game(3, 3, [(2, 2)])
        c = game2.board[1][1]
        c.open = True
        game2.open_cells = 1
        # neighbour_mines for center == 1 (mine at 2,2 is adjacent)
        # flag a safe neighbour so flags == 1 == neighbour_mines, then force
        game2.board[0][0].flagged = True  # safe cell flagged
        game2.process_force(c)
        # mine at (2,2) should now be opened, blowed_up should be True
        self.assertTrue(game2.blowed_up)


class TestOpenArea(unittest.TestCase):

    def test_flood_fill_does_not_open_mines(self):
        game = make_game(5, 5, [(0, 0)])
        game.process_open(game.board[4][4])
        self.assertFalse(game.board[0][0].open)
        self.assertFalse(game.blowed_up)

    def test_flood_fill_does_not_open_flagged_cells(self):
        game = make_game(5, 5, [(0, 0)])
        game.board[3][3].flagged = True
        game.process_open(game.board[4][4])
        self.assertFalse(game.board[3][3].open)

    def test_open_cells_count_matches_actual_open_cells(self):
        game = make_game(5, 5, [(0, 0)])
        game.process_open(game.board[4][4])
        actual_open = sum(1 for row in game.board for cell in row if cell.open)
        self.assertEqual(game.open_cells, actual_open)

    def test_flood_fill_stops_at_numbered_border(self):
        # Cells adjacent to a mine have neighbour_mines > 0 and should not expand further
        game = make_game(5, 5, [(0, 0)])
        game.process_open(game.board[4][4])
        # The mine itself must remain closed
        mine = game.board[0][0]
        self.assertFalse(mine.open)


class TestGameOver(unittest.TestCase):

    def test_not_over_at_start(self):
        game = make_game(3, 3, [(0, 0)])
        self.assertFalse(game.game_over())

    def test_over_when_blowed_up(self):
        game = make_game(3, 3, [(0, 0)])
        game.blowed_up = True
        self.assertTrue(game.game_over())

    def test_over_when_all_safe_cells_open(self):
        # 3x3 = 9 cells, 1 mine → need 8 open cells to win
        game = make_game(3, 3, [(0, 0)])
        game.open_cells = 8
        self.assertTrue(game.game_over())

    def test_not_over_with_one_safe_cell_remaining(self):
        game = make_game(3, 3, [(0, 0)])
        game.open_cells = 7
        self.assertFalse(game.game_over())


class TestProcess(unittest.TestCase):

    def test_out_of_bounds_returns_false(self):
        game = make_game(3, 3, [])
        self.assertFalse(game.process("open", -1, 0))
        self.assertFalse(game.process("open", 0, -1))
        self.assertFalse(game.process("open", 3, 0))
        self.assertFalse(game.process("open", 0, 3))

    def test_unknown_action_returns_false(self):
        game = make_game(3, 3, [])
        self.assertFalse(game.process("explode", 0, 0))


class TestTakeInput(unittest.TestCase):

    def test_valid_input_parsed_correctly(self):
        ui = TerminalUI()
        with patch('builtins.input', return_value='open 3 4'):
            action, x, y = ui.take_input(None, 10, 10)
        self.assertEqual(action, 'open')
        self.assertEqual(x, 3)
        self.assertEqual(y, 4)

    def test_too_few_tokens_reprompts(self):
        ui = TerminalUI()
        with patch('builtins.input', side_effect=['open 5', 'open 1 2']):
            with patch('builtins.print'):
                action, x, y = ui.take_input(None, 10, 10)
        self.assertEqual((action, x, y), ('open', 1, 2))

    def test_non_integer_coordinates_reprompt(self):
        ui = TerminalUI()
        with patch('builtins.input', side_effect=['open a b', 'toggle 0 0']):
            with patch('builtins.print'):
                action, x, y = ui.take_input(None, 10, 10)
        self.assertEqual((action, x, y), ('toggle', 0, 0))

    def test_empty_input_reprompts(self):
        ui = TerminalUI()
        with patch('builtins.input', side_effect=['', 'force 2 3']):
            with patch('builtins.print'):
                action, x, y = ui.take_input(None, 10, 10)
        self.assertEqual((action, x, y), ('force', 2, 3))


if __name__ == '__main__':
    unittest.main()
