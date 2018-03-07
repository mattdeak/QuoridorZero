import pygame
import logwood
from logwood.handlers.stderr import ColoredStderrHandler
from environment.quoridor import Quoridor
from agents.base import BaseAgent
from agents.manual import ManualPygameAgent

logwood.basic_config(
        level = logwood.INFO,
        handlers = [ColoredStderrHandler()]
)

logger = logwood.get_logger('Visuals')

# Define Colors
BLACK = (0, 0, 0)
WHITE = (240, 255, 240)
LIGHTBROWN = (222, 184, 135)
BROWN = (128, 0, 0)
LIGHTRED = (240, 128, 128)
RED = (205, 92, 92)
LIGHTBLUE = (221, 160, 221)
BLUE = (186, 85, 211)
DARKBLUE = (0, 0, 128)

SCREEN_WIDTH = 600
SCREEN_HEIGHT = SCREEN_WIDTH - 200


TILE_WIDTH = SCREEN_HEIGHT  / 10.6
TILE_HEIGHT = SCREEN_HEIGHT / 10.6

WALL_WIDTH = 0.2 * TILE_WIDTH
WALL_HEIGHT = TILE_WIDTH * 2 + WALL_WIDTH



# ---- Main Program Loop ---- #
def main():
    logger.info("Loading Game Environment")
    game = Quoridor()
    player1 = ManualPygameAgent('Matt')
    player2 = ManualPygameAgent('Kelsy')

    player_types = {1 : 'human', 2: 'human'}
    players = {1 : player1, 2 : player2}

    game.load(player1, player2)

    logger.info("Initializing Visuals")
    pygame.init()

    WINDOW_SIZE = [SCREEN_WIDTH, SCREEN_HEIGHT]
    screen = pygame.display.set_mode(WINDOW_SIZE)

    pygame.display.set_caption("QUORIDOR")

    clock = pygame.time.Clock()

    valid_actions = game.valid_actions
    done = False
    while not done:
        player_moved = False
        pawn_moves, walls = draw_game(game, screen, valid_actions)
        valid_walls = [wall for wall in walls if wall[2] in valid_actions]
        if player_types[game.current_player] == 'human':
            touch = pygame.mouse.get_pos()
            for wall, collides, _ in valid_walls:
                for collide in collides:
                    if collide.collidepoint(touch):
                        pygame.draw.rect(screen, LIGHTBROWN, wall)
                        break
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    touch = pygame.mouse.get_pos()
                    # This is messy - fix later
                    for rect, action in pawn_moves:
                        if rect.collidepoint(touch):
                            players[game.current_player].receive_action(action)
                            player_moved = True
                            break
                        if player_moved : break
                    if player_moved : break

                    for rect, collide_points, action in valid_walls:
                        for collides in collide_points:
                            if collides.collidepoint(touch):
                                players[game.current_player].receive_action(action)
                                player_moved = True
                                break
                        if player_moved == True:
                            break

        clock.tick(30)
        pygame.display.flip()

        if player_moved or player_types[game.current_player] == 'computer':
            winner = game.step()
            valid_actions = game.valid_actions
            if winner:
                logger.info(f"Winner is {winner.name}")

    pygame.quit()

def draw_game(game, screen, valid_actions):
        # Calculate valid action tiles
        # Draw Valid Pawn actions
        screen.fill(BLACK)
        pawn_actions = [action for action in valid_actions if action < 12]
        reference_tile = game._positions[game.current_player]

        action_tiles = {}
        for action in pawn_actions:
            if action == game._DIRECTIONS['N']:
                action_tiles[reference_tile + 9] =  action
            elif action == game._DIRECTIONS['S']:
                action_tiles[reference_tile - 9] =  action
            elif action == game._DIRECTIONS['E']:
                action_tiles[reference_tile + 1] = action
            elif action == game._DIRECTIONS['W']:
                action_tiles[reference_tile - 1] = action
            elif action == game._DIRECTIONS['NN']:
                action_tiles[reference_tile + 18] = action
            elif action == game._DIRECTIONS['SS']:
                action_tiles[reference_tile - 18] = action
            elif action == game._DIRECTIONS['EE']:
                action_tiles[reference_tile + 2] = action
            elif action == game._DIRECTIONS['WW']:
                action_tiles[reference_tile - 2] = action
            elif action == game._DIRECTIONS['NE']:
                action_tiles[reference_tile + 10] = action
            elif action == game._DIRECTIONS['NW']:
                action_tiles[reference_tile + 8] = action
            elif action == game._DIRECTIONS['SE']:
                action_tiles[reference_tile - 8] = action
            elif action == game._DIRECTIONS['SW']:
                action_tiles[reference_tile - 10] = action

        # Draw Tiles
        pawn_moves = []
        for row in range(9):
            for column in range(9):
                if row * 9 + column in action_tiles.keys():
                    if game.current_player == 1:
                        color = LIGHTBLUE
                    else:
                        color = LIGHTRED
                    rect = pygame.draw.rect(
                            screen,
                            color,
                            [(TILE_WIDTH + WALL_WIDTH) * column,
                            (WALL_WIDTH + TILE_HEIGHT) * (8 - row),
                            TILE_WIDTH,
                            TILE_HEIGHT]
                            )
                    pawn_moves.append([rect, action_tiles[row * 9 + column]])
                else:
                    if row * 9 + column == game._positions[1]:
                        color = BLUE
                    elif row * 9 + column == game._positions[2]:
                        color = RED
                    else:
                        color = DARKBLUE
                    pygame.draw.rect(screen,
                                    color,
                                    [(TILE_WIDTH + WALL_WIDTH) * column,
                                    (WALL_WIDTH + TILE_HEIGHT) * (8 - row),
                                    TILE_WIDTH,
                                    TILE_HEIGHT])

        walls = []

        # Draw Vertical Walls
        placed_walls = []
        for row in range(8):
            for column in range(8):
                collide_points = []
                rect = pygame.Rect(TILE_WIDTH + (TILE_WIDTH + WALL_WIDTH) * column,
                                  (TILE_HEIGHT + WALL_WIDTH) * (7 - row),
                                  WALL_WIDTH,
                                  WALL_HEIGHT)
                if game._intersections[row * 8 + column] == -1:
                    placed_walls.append(rect)
                else:
                    # Collide rectangles for highlighting the walls on hover
                    collide_top = pygame.Rect(TILE_WIDTH + (TILE_WIDTH + WALL_WIDTH) * column,
                                             (TILE_HEIGHT + WALL_WIDTH) * (7 - row) + TILE_HEIGHT / 2,
                                             WALL_WIDTH,
                                             TILE_HEIGHT / 2)
                    pygame.draw.rect(screen, BLACK, collide_top)
                    collide_points.append(collide_top)

                    collide_bottom = pygame.Rect(TILE_WIDTH + (TILE_WIDTH + WALL_WIDTH) * column,
                                                (TILE_HEIGHT + WALL_WIDTH) * (7 - row) + TILE_HEIGHT + WALL_WIDTH,
                                                WALL_WIDTH,
                                                TILE_HEIGHT / 2)
                    pygame.draw.rect(screen, BLACK, collide_bottom)
                    collide_points.append(collide_bottom)

                pygame.draw.rect(screen, BLACK, rect)
                walls.append([rect, collide_points, row * 8 + column + 64 + 12])

        # Draw Horizontal Walls
        for row in range(8):
            for column in range(8):
                rect = pygame.Rect((TILE_HEIGHT + WALL_WIDTH) * column,
                                    TILE_HEIGHT + (TILE_HEIGHT + WALL_WIDTH) * (7 - row),
                                    WALL_HEIGHT,
                                    WALL_WIDTH)
                if game._intersections[row * 8 + column] == 1:
                    placed_walls.append(rect)
                else:
                    # Collide rectangles for highlighting the walls on hover
                    collide_points = []

                    collide_left = pygame.Rect((TILE_HEIGHT + WALL_WIDTH) * column + TILE_WIDTH / 2,
                                             TILE_HEIGHT + (TILE_HEIGHT + WALL_WIDTH) * (7 - row),
                                             TILE_WIDTH / 2,
                                             WALL_WIDTH)

                    pygame.draw.rect(screen, BLACK, collide_left)
                    collide_points.append(collide_left)

                    collide_right = pygame.Rect((TILE_HEIGHT + WALL_WIDTH) * column + TILE_WIDTH + WALL_WIDTH,
                                                 TILE_HEIGHT + (TILE_HEIGHT + WALL_WIDTH) * (7 - row),
                                                 TILE_WIDTH / 2,
                                                 WALL_WIDTH)
                    pygame.draw.rect(screen, BLACK, collide_right)
                    collide_points.append(collide_right)

                rect = pygame.Rect((TILE_HEIGHT + WALL_WIDTH) * (column),
                                    TILE_HEIGHT + (TILE_HEIGHT + WALL_WIDTH) * (7 - row),
                                    WALL_HEIGHT,
                                    WALL_WIDTH)

                pygame.draw.rect(screen, BLACK, rect)
                walls.append([rect, collide_points, row * 8 + column + 12])

        for wall in placed_walls:
            pygame.draw.rect(screen, BROWN, wall)

        # Draw Walls Remaining
        font = pygame.font.SysFont("arial", 18)

        player1_walls = font.render(f"Walls Remaining: {game._player1_walls_remaining}", 1, BLUE)
        player1_text_position = SCREEN_HEIGHT + 2, SCREEN_HEIGHT * 0.9

        player2_walls = font.render(f"Walls Remaining: {game._player2_walls_remaining}", 1, RED)
        player2_text_position = SCREEN_HEIGHT + 2, SCREEN_HEIGHT * 0.1

        screen.blit(player1_walls, player1_text_position)
        screen.blit(player2_walls, player2_text_position)
        return pawn_moves, walls


def draw_load_screen(screen):
    menu_data = (
        'Player1',
        'Human',
        'AI'
    )

    menu_data = (
        'Player2',
        'Human',
        'AI'
    )

if __name__ == '__main__':
    main()
