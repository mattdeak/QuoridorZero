import numpy as np
import logwood
from queue import Queue
from enum import Enum

# Helper class


class Quoridor:

    HORIZONTAL = 1
    VERTICAL = -1

    def __init__(self, safe=False):
        self._logger = logwood.get_logger(f"{self.__class__.__name__}")
        self.safe = safe

    def load(self, player1, player2):
        # Handshake with players
        self.player1 = player1
        self.player2 = player2
        player1.environment = self
        player2.environment = self

        self.current_player = 1

        # Initialize Tiles
        self.tiles = np.zeros(81)

        # Initialize Player Locations
        self._positions = {
            1 : 4,
            2 : 76
        }

        self._DIRECTIONS = {
            'N' : 0, 'S' : 1, 'E' : 2, 'W' : 3,
            'NN' : 4, 'SS' : 5, 'EE' : 6, 'WW' : 7,
            'NE' : 8, 'NW' : 9, 'SE' : 10, 'SW' : 11
        }
        self.N_DIRECTIONS = 12
        self.N_TILES = 81
        self.N_ROWS = 9
        self.N_INTERSECTIONS = 64

        # There are 64 possible intersection
        # Horizontal Walls - 1
        # No Wall - 0
        # Vertical Wall - -1
        self._intersections = np.zeros(64)


        self._player1_walls_remaining = 10
        self._player2_walls_remaining = 10

    def get_state(self, player=1):
        """Returns a set of 9x9 planes that represent the game state.
        1. The current player position
        2. The opponent position
        3. Vertical Walls
        4. Horizontal Walls
        5 - 14. Number of walls remaining for current player
        15 - 24. Number of walls remaining for opponent
        """
        player1_position_plane = self.tiles.copy()
        player1_position_plane[self._positions[1]] = 1
        player1_position_plane = player1_position_plane.reshape([9, 9])

        player2_position_planne = self.tiles.copy()
        player2_position_plane[self._positions[2]] = 1
        player2_position_plane = player2_position_plane.reshape([9, 9])

        player1_walls_plane = np.zeros([10,9,9])
        player2_walls_plane = np.zeros([10,9,9])

        player1_walls_plane[self._player1_walls_remaining - 1, :, :] = 1
        player2_walls_plane[self._player2_walls_remaining - 1, :, :] = 1

        # Set the wall planes
        vertical_walls = np.pad(
            np.int8(self._intersections == -1).reshape([8, 8]),
            (0, 1),
            mode='constant',
            constant_values=0
            )


        horizontal_walls = np.pad(
            np.int8(self._intersections == 1).reshape([8, 8]),
            (0, 1),
            mode='constant',
            constant_values=0
            )

        no_walls = np.pad(
            np.int8(self._intersections == 0).reshape([8, 8]),
            (0, 1),
            mode='constant',
            constant_values=0
            )

        # Adjust the position of planes based on current player
        if player == 1:
            state = np.stack([
                no_walls,
                vertical_walls,
                horizontal_walls,
                player1_position_plane,
                player2_position_plane,
            ])
            state = np.vstack([state, player1_walls_plane, player2_walls_plane])

        if player == 2:
            state = np.stack([
                no_walls,
                vertical_walls,
                horizontal_walls,
                player2_position_plane,
                player1_position_plane,
            ])

            state = np.vstack([state, player2_walls_plane, player1_walls_plane])

        return state

    @property
    def valid_actions(self):
        """The valid actions for the current gamestate"""
        # --------
        # There are 64 possible horizontal wall placements and
        # 64 possible vertical wall placements.
        # These are only invalid actions if they are obstructed by another wall.
        #
        # There are 4 basic pawn actions (N, E, S, W), and 8
        # special case pawn actions (NN, EE, SS, WW, NW, NE, SW, SE) which
        # are applicable only when another pawn is directly adjacent.
        # This makes a total of 64 + 64 + 4 + 8 = 140 possible actions.
        player = self.current_player
        location = self._positions[player]

        opponent = 1 if player == 2 else 2
        opponent_loc = self._positions[opponent]
        walls = self._intersections

        pawn_actions = self._valid_pawn_actions(location=location,
                        opponent_loc=opponent_loc, walls=walls, player=player)

        if ((self.current_player == 1 and self._player1_walls_remaining > 1)
            or (self.current_player == 2 and self._player2_walls_remaining > 1)):
            wall_actions = self._valid_wall_actions()

            # Adjust for the pawn actions (which go up to 12)
            wall_actions = [action + 12 for action in wall_actions]
        else:
            wall_actions = []
        return pawn_actions + wall_actions


    def play(self):
        """Plays an entire game and returns the winner"""
        winner = None
        while not winner:
            winner = self.step()
        self._logger.info(f"Winner is {winner.name}")

    def step(self):
        if self.current_player == 1:
            action = self.player1.choose_action()
        else:
            action = self.player2.choose_action()
        self._logger.info(f"Player {self.current_player} chooses action {action}")
        winner = self.take_action(action)
        return winner


    def take_action(self, action):
        """Take a step in the environment given the current action"""
        player = self.current_player
        if self.safe:
            if not action in self.valid_actions:
                raise ValueError(f"Invalid Action: {action}")

        if action < 12:
            self._handle_pawn_action(action, player)
        else:
            self._handle_wall_action(action - 12)

        winner = self.is_endgame()
        if winner:
            return winner
        else:
            self.rotate_players()
            return None

    def is_endgame(self):
        if self._positions[2] < 9:
            return self.player2
        elif self._positions[1] > 71:
            return self.player1
        else:
            return None

    def _handle_pawn_action(self, action, player):
        if action == self._DIRECTIONS['N']:
            self._positions[player] += 9
        elif action == self._DIRECTIONS['S']:
            self._positions[player] -= 9
        elif action == self._DIRECTIONS['E']:
            self._positions[player] += 1
        elif action == self._DIRECTIONS['W']:
            self._positions[player] -= 1
        elif action == self._DIRECTIONS['NN']:
            self._positions[player] += 18
        elif action == self._DIRECTIONS['SS']:
            self._positions[player] -= 18
        elif action == self._DIRECTIONS['EE']:
            self._positions[player] += 2
        elif action == self._DIRECTIONS['WW']:
            self._positions[player] -= 2
        elif action == self._DIRECTIONS['NW']:
            self._positions[player] += 8
        elif action == self._DIRECTIONS['NE']:
            self._positions[player] += 10
        elif action == self._DIRECTIONS['SW']:
            self._positions[player] -= 10
        elif action == self._DIRECTIONS['SE']:
            self._positions[player] -= 8
        else:
            raise ValueError(f"Invalid Pawn Action: {action}")

    def _handle_wall_action(self, action):
        # Action values less than 64 are horizontal walls
        if action < 64:
            self._intersections[action] = 1
        # Action values above 64 are vertical walls
        else:
            self._intersections[action - 64] = -1

        if self.current_player == 1:
            self._player1_walls_remaining -= 1
        else:
            self._player2_walls_remaining -= 1
        self._logger.info(self._intersections)

    def rotate_players(self):
        """Switch the player turn"""
        self._logger.debug("Rotating Player")
        if self.current_player == 1:
            self.current_player = 2
        else:
            self.current_player = 1


    def _valid_pawn_actions(self, walls, location, opponent_loc, player=1):
        HORIZONTAL = 1
        VERTICAL = -1

        valid = []

        opponent_north = location == opponent_loc - 9
        opponent_south = location == opponent_loc + 9
        opponent_east = location == opponent_loc - 1
        opponent_west = location == opponent_loc + 1

        current_row = location // self.N_ROWS

        intersections = self._get_intersections(walls, location)

        n = intersections['NW'] != HORIZONTAL and intersections['NE'] != HORIZONTAL and not opponent_north
        s = intersections['SW'] != HORIZONTAL and intersections['SE'] != HORIZONTAL and not opponent_south
        e = intersections['NE'] != VERTICAL and intersections['SE'] != VERTICAL and not opponent_east
        w = intersections['NW'] != VERTICAL and intersections['SW'] != VERTICAL and not opponent_west

        if n or (player == 1 and current_row == 8) : valid.append(self._DIRECTIONS['N'])
        if s or (player == 2 and current_row == 0): valid.append(self._DIRECTIONS['S'])
        if e : valid.append(self._DIRECTIONS['E'])
        if w : valid.append(self._DIRECTIONS['W'])


        if opponent_north and intersections['NE'] != HORIZONTAL and intersections['NW'] != HORIZONTAL:
            n_intersections = self._get_intersections(walls, opponent_loc)
            if n_intersections['NW'] != HORIZONTAL and n_intersections['NE'] != HORIZONTAL \
                or (current_row == 7 and player == 1):
                valid.append(self._DIRECTIONS['NN'])

            if n_intersections['NE'] != VERTICAL and intersections['NE'] != VERTICAL:
                valid.append(self._DIRECTIONS['NE'])

            if n_intersections['NW'] != VERTICAL and intersections['NW'] != VERTICAL:
                valid.append(self._DIRECTIONS['NW'])


        if opponent_south and intersections['SE'] != VERTICAL and intersections['SW'] != VERTICAL:
            s_intersections = self._get_intersections(walls, opponent_loc)
            if s_intersections['SW'] != HORIZONTAL and s_intersections['SE'] != HORIZONTAL \
                or (current_row == 1 and player == 2):
                valid.append(self._DIRECTIONS['SS'])

            if s_intersections['SE'] != VERTICAL and intersections['SE'] != VERTICAL:
                valid.append(self._DIRECTIONS['SE'])

            if s_intersections['SW'] != VERTICAL and intersections['SW'] != VERTICAL:
                valid.append(self._DIRECTIONS['SW'])


        elif opponent_east and intersections['SE'] != VERTICAL and intersections['NE'] != VERTICAL:
            e_intersections = self._get_intersections(walls, opponent_loc)
            if e_intersections['SE'] != VERTICAL and e_intersections['SW'] != VERTICAL:
                valid.append(self._DIRECTIONS['EE'])

        elif opponent_west and intersections['SW'] != VERTICAL and intersections['NW'] != VERTICAL:
            w_intersections = self._get_intersections(walls, opponent_loc)
            if w_intersections['SE'] != VERTICAL and w_intersections['SW'] != VERTICAL:
                valid.append(self._DIRECTIONS['WW'])

        return valid


    def _get_intersections(self, intersections, current_tile):
        """Gets the four intersections for a given tile."""
        location_row = current_tile // self.N_ROWS

        n_border = current_tile > 71
        e_border = current_tile % 9 == 8
        s_border = current_tile < 9
        w_border = current_tile % 9 == 0

        if n_border:
            ne_intersection = 1
            if w_border:
                nw_intersection = -1
                sw_intersection = -1
                se_intersection = intersections[(current_tile - 9) - (location_row - 1)]
            elif e_border:
                nw_intersection = 1
                se_intersection = -1
                sw_intersection = intersections[(current_tile - 9) - (location_row - 1) - 1]
            else:
                nw_intersection = 1
                sw_intersection = intersections[(current_tile - 9) - (location_row - 1) - 1]
                se_intersection = intersections[(current_tile - 9) - (location_row - 1)]
        elif s_border:
            sw_intersection = 1
            if w_border:
                nw_intersection = -1
                se_intersection = 1
                ne_intersection = intersections[current_tile - location_row]
            elif e_border:
                se_intersection = -1
                ne_intersection = -1
                nw_intersection = ne_intersection = intersections[current_tile - location_row - 1]
            else:
                se_intersection = 1
                ne_intersection = intersections[current_tile - location_row]
                nw_intersection = ne_intersection = intersections[current_tile - location_row - 1]


        # West but not north or south
        elif w_border:
            nw_intersection = -1
            sw_intersection = -1
            ne_intersection = intersections[current_tile - location_row]
            se_intersection = intersections[(current_tile - 9) - (location_row - 1)]

        elif e_border:
            ne_intersection = -1
            se_intersection = -1
            nw_intersection = intersections[current_tile - location_row - 1]
            sw_intersection = intersections[(current_tile - 9) - (location_row - 1) - 1]

        # No borders
        else:
            ne_intersection = intersections[current_tile - location_row]
            nw_intersection = intersections[current_tile - location_row - 1]
            sw_intersection = intersections[(current_tile - 9) - (location_row - 1) - 1]
            se_intersection = intersections[(current_tile - 9) - (location_row - 1)]

        self._logger.debug(ne_intersection)
        return {'NW' : nw_intersection,
                'NE' : ne_intersection,
                'SE' : se_intersection,
                'SW' : sw_intersection}


    def _valid_wall_actions(self):
        valid = []
        # If
        for ix in range(self._intersections.size):
            if self._validate_horizontal(ix):
                valid.append(ix)

            if self._validate_vertical(ix):
                valid.append(ix + 64)

        return valid


    def _validate_horizontal(self, ix):
        column = ix % 8

        if self._intersections[ix] != 0:
            return False

        if column != 0:
            if self._intersections[ix - 1] == 1:
                return False

        if column != 7:
            if self._intersections[ix + 1] == 1:
                return False

        return not self._blocks_path(ix, self.HORIZONTAL)


    def _validate_vertical(self, ix):
        row = ix // 8
        if self._intersections[ix] != 0:
            return False

        if row != 0:
            if self._intersections[ix - 8] == -1:
                return False

        if row != 7:
            if self._intersections[ix + 8] == -1:
                return False

        return not self._blocks_path(ix, self.VERTICAL)


    def _blocks_path(self, wall_location, orientation):
        player1_target = 8
        player2_target = 0

        player1_position = self._positions[1]
        player2_position = self._positions[2]

        intersections = self._intersections.copy()
        intersections[wall_location] = orientation

        # BFS to target row
        player1_valid = self._bfs_to_goal(intersections, player1_target, player1_position, player2_position, player=1)
        player2_valid = self._bfs_to_goal(intersections, player2_target, player2_position, player1_position, player=2)

        return not (player1_valid and player2_valid)


    def _bfs_to_goal(self, intersections, target_row, player_position, opponent_position, player=1):
        visited = []
        invalid_rows = [9, -1]
        visit_queue = Queue()
        visit_queue.put(player_position)
        target_visited = False

        while not target_visited and not visit_queue.empty():
            current_position = visit_queue.get()
            valid_directions = self._valid_pawn_actions(intersections,
                                    location=current_position,
                                    opponent_loc=opponent_position,
                                    player=player)
            for direction in valid_directions:
                if direction == self._DIRECTIONS['N']:
                    new_position = current_position + 9
                elif direction == self._DIRECTIONS['S']:
                    new_position = current_position - 9
                elif direction == self._DIRECTIONS['E']:
                    new_position = current_position + 1
                elif direction == self._DIRECTIONS['W']:
                    new_position = current_position - 1
                elif direction == self._DIRECTIONS['NN']:
                    new_position = current_position + 18
                elif direction == self._DIRECTIONS['SS']:
                    new_position = current_position - 18
                elif direction == self._DIRECTIONS['EE']:
                    new_position = current_position + 2
                elif direction == self._DIRECTIONS['WW']:
                    new_position = current_position - 2
                elif direction == self._DIRECTIONS['NE']:
                    new_position = current_position + 10
                elif direction == self._DIRECTIONS['NW']:
                    new_position = current_position + 8
                elif direction == self._DIRECTIONS['SW']:
                    new_position = current_position - 10
                elif direction == self._DIRECTIONS['SE']:
                    new_position = current_position - 8
                else:
                    raise ValueError('Invalid direction - should never happen')

                new_row = new_position // self.N_ROWS
                if new_row == target_row:
                    target_visited = True
                elif new_position not in visited:
                    visited.append(new_position)
                    if new_row not in invalid_rows:
                        visit_queue.put(new_position)

        return target_visited

    def add_wall(self, wall, orientation):
        self._intersections[wall] = orientation

    def print_board(self):
        player1_row = self._positions[1] // 9
        player1_col = self._positions[1] % 9
        player2_row = self._positions[2] // 9
        player2_col = self._positions[2] % 9

        x = 'X'
        o = 'O'

        v = 'v'
        h = 'h'
        dash = '-'
        none = ''

        grid = [[f'{dash:4}' for i in range(9)] for i in range(9)]
        i_reshaped = self._intersections.reshape([8, 8])


        grid[player1_row][player1_col] = f'{x:4}'
        grid[player2_row][player2_col] = f'{o:4}'

        intersection_row = 7
        for i in range(8, -1, -1):
            for j in range(9):
                print(grid[i][j], end='')
            print()
            if intersection_row >= 0:
                print(f'{none:2}', end='')
                for j in i_reshaped[intersection_row, :]:
                    if j == 1:
                        print(f'{h:4}', end='')
                    elif j == -1:
                        print(f'{v:4}', end='')
                    else:
                        print(f'{none:4}', end='')
                intersection_row -= 1
                print()
