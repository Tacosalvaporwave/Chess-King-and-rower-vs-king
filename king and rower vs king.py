import pygame
import chess
import time
from pygame import gfxdraw

# Constants
WIDTH, HEIGHT = 600, 600
SQUARE_SIZE = WIDTH // 8
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_BLUE = (173, 216, 230)
DARK_BLUE = (0, 0, 139)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# Dictionary to hold piece images
PIECES = {}

def load_images():
    pieces = {
        'K': "KW.png",
        'k': "k.png",
        'r': "R.png"
    }
    for symbol, path in pieces.items():
        try:
            PIECES[symbol] = pygame.transform.scale(
                pygame.image.load(path), (SQUARE_SIZE, SQUARE_SIZE))
        except:
            # Create a placeholder if image not found
            surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
            surf.fill((200, 200, 255) if symbol.isupper() else (50, 50, 50))
            font = pygame.font.SysFont('Arial', 48)
            text_color = BLACK if symbol.isupper() else WHITE
            text = font.render(symbol, True, text_color)
            surf.blit(text, (SQUARE_SIZE//2 - text.get_width()//2, 
                            SQUARE_SIZE//2 - text.get_height()//2))
            PIECES[symbol] = surf

def draw_board(screen, board):
    colors = [(238, 238, 210), (118, 150, 86)]
    
    for r in range(8):
        for c in range(8):
            color = colors[(r + c) % 2]
            pygame.draw.rect(screen, color, pygame.Rect(c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
    
    if board.is_check():
        king_square = board.king(board.turn)
        col = chess.square_file(king_square)
        row = 7 - chess.square_rank(king_square)
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        s.fill((255, 0, 0, 128))
        screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))

def draw_pieces(screen, board):
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            piece_str = piece.symbol()
            row, col = 7 - square // 8, square % 8
            screen.blit(PIECES[piece_str], (col * SQUARE_SIZE, row * SQUARE_SIZE))

def draw_highlights(screen, selected_square, valid_moves, board):
    if selected_square is not None:
        col = chess.square_file(selected_square)
        row = 7 - chess.square_rank(selected_square)
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        s.fill((255, 255, 0, 150))
        screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
        
        for move in valid_moves:
            if move.from_square == selected_square:
                col = chess.square_file(move.to_square)
                row = 7 - chess.square_rank(move.to_square)        
                center = (col * SQUARE_SIZE + SQUARE_SIZE // 2, 
                          row * SQUARE_SIZE + SQUARE_SIZE // 2)
                radius = SQUARE_SIZE // 3
                
                if board.is_capture(move):
                    pygame.draw.circle(screen, (255, 0, 0, 150), center, radius, 5)
                else:
                    pygame.draw.circle(screen, (0, 255, 0, 150), center, radius, 5)

def get_square_under_mouse(pos):
    x, y = pos
    row = 7 - y // SQUARE_SIZE
    col = x // SQUARE_SIZE
    return chess.square(col, row)

def evaluate_board(board):
    if board.is_checkmate():
        return 10000 if board.turn == chess.WHITE else -10000
    if board.is_stalemate():
        return 0
    
    white_king = board.king(chess.WHITE)
    black_king = board.king(chess.BLACK)
    black_rook = None
    
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == chess.BLACK and piece.piece_type == chess.ROOK:
            black_rook = square
            break
    
    if not black_rook:
        return 0
    
    evaluation = 0
    distance_rook = max(abs(chess.square_file(white_king) - chess.square_file(black_rook)),
                        abs(chess.square_rank(white_king) - chess.square_rank(black_rook)))
    distance_kings = max(abs(chess.square_file(white_king) - chess.square_file(black_king)),
                         abs(chess.square_rank(white_king) - chess.square_rank(black_king)))
    
    if board.is_check():
        evaluation += 50 if board.turn == chess.BLACK else -30
    
    edge_distance = min(
        chess.square_file(white_king), 7 - chess.square_file(white_king),
        chess.square_rank(white_king), 7 - chess.square_rank(white_king))
    evaluation += (4 - edge_distance) * 15
    
    if (chess.square_file(white_king) == chess.square_file(black_rook) or 
        chess.square_rank(white_king) == chess.square_rank(black_rook)):
        evaluation += 20
        if distance_rook > 1:
            evaluation += 10
    
    if distance_kings <= 1:
        evaluation -= 30
    
    if (abs(chess.square_file(white_king) - chess.square_file(black_king)) == 2 and 
        chess.square_rank(white_king) == chess.square_rank(black_king)) or \
       (abs(chess.square_rank(white_king) - chess.square_rank(black_king)) == 2 and 
        chess.square_file(white_king) == chess.square_file(black_king)):
        evaluation += 25
    
    return evaluation if board.turn == chess.BLACK else -evaluation

def minimax(board, depth, alpha, beta, maximizing_player):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board), None
    
    best_move = None
    legal_moves = list(board.legal_moves)
    
    legal_moves.sort(key=lambda move: evaluate_move(board, move), reverse=maximizing_player)
    
    if maximizing_player:
        max_eval = float('-inf')
        for move in legal_moves:
            board.push(move)
            eval, _ = minimax(board, depth-1, alpha, beta, False)
            board.pop()
            if eval > max_eval:
                max_eval = eval
                best_move = move
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in legal_moves:
            board.push(move)
            eval, _ = minimax(board, depth-1, alpha, beta, True)
            board.pop()
            if eval < min_eval:
                min_eval = eval
                best_move = move
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval, best_move

def evaluate_move(board, move):
    score = 0
    board.push(move)
    
    if board.is_checkmate():
        score = 10000
    elif board.is_check():
        score = 50
    elif board.is_capture(move):
        score = 30
    
    if board.is_castling(move):
        score += 40
    
    if board.turn == chess.BLACK:
        piece = board.piece_at(move.to_square)
        if piece and piece.piece_type == chess.KING:
            file, rank = chess.square_file(move.to_square), chess.square_rank(move.to_square)
            center_distance = max(abs(3.5 - file), abs(3.5 - rank))
            score += 15 - center_distance * 3
    
    board.pop()
    return score

def get_ai_move(board, depth=3):
    start_time = time.time()
    best_move = None
    
    for move in board.legal_moves:
        board.push(move)
        if board.is_checkmate():
            board.pop()
            return move
        board.pop()
    
    for current_depth in range(1, depth+1):
        _, best_move = minimax(board, current_depth, -float('inf'), float('inf'), board.turn == chess.BLACK)
        if board.is_checkmate() or board.is_stalemate() or time.time() - start_time > 2:
            break
    
    return best_move

def show_message(screen, message):
    font = pygame.font.SysFont('Arial', 36)
    text = font.render(message, True, BLACK)
    rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
    
    s = pygame.Surface((rect.width + 40, rect.height + 20), pygame.SRCALPHA)
    s.fill((255, 255, 255, 200))
    screen.blit(s, (rect.x - 20, rect.y - 10))
    
    pygame.draw.rect(screen, RED, (rect.x - 20, rect.y - 10, rect.width + 40, rect.height + 20), 3)
    
    screen.blit(text, rect)
    pygame.display.flip()
    time.sleep(2)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Rey vs Rey y Torre - Juega con el Rey Blanco")
    load_images()

    board = chess.Board()
    board.clear()
    
    board.set_piece_at(chess.E1, chess.Piece.from_symbol("K"))
    board.set_piece_at(chess.E8, chess.Piece.from_symbol("k"))
    board.set_piece_at(chess.A8, chess.Piece.from_symbol("r"))
    
    board.castling_rights = chess.BB_A8 | chess.BB_H8

    selected_square = None
    valid_moves = []
    running = True
    game_over = False

    while running:
        draw_board(screen, board)
        draw_highlights(screen, selected_square, valid_moves, board)
        draw_pieces(screen, board)
        
        font = pygame.font.SysFont('Arial', 24)
        turn_text = f"Turno: {'Blancas' if board.turn == chess.WHITE else 'Negras'}"
        if board.is_check():
            turn_text += " - ¡JAQUE!"
        text_surface = font.render(turn_text, True, BLACK)
        screen.blit(text_surface, (10, HEIGHT - 30))
        
        pygame.display.flip()

        if not game_over:
            if board.is_checkmate():
                winner = "Negras" if board.turn == chess.WHITE else "Blancas"
                show_message(screen, f"¡Jaque mate! Ganan las {winner}!")
                game_over = True
            elif board.is_stalemate():
                show_message(screen, "¡Tablas por ahogado!")
                game_over = True
            elif board.is_insufficient_material():
                show_message(screen, "¡Tablas por material insuficiente!")
                game_over = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                if board.turn == chess.WHITE:
                    square = get_square_under_mouse(pygame.mouse.get_pos())
                    piece = board.piece_at(square)
                    
                    if selected_square is None:
                        if piece and piece.color == chess.WHITE:
                            selected_square = square
                            valid_moves = [m for m in board.legal_moves if m.from_square == square]
                    else:
                        move = chess.Move(selected_square, square)
                        
                        if move in board.legal_moves:
                            board.push(move)
                            selected_square = None
                            valid_moves = []
                            
                            if not board.is_game_over():
                                pygame.display.flip()
                                ai_move = get_ai_move(board, 3)
                                if ai_move:
                                    board.push(ai_move)
                        elif piece and piece.color == chess.WHITE:
                            selected_square = square
                            valid_moves = [m for m in board.legal_moves if m.from_square == square]
                        else:
                            selected_square = None
                            valid_moves = []
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    board.reset()
                    selected_square = None
                    valid_moves = []
                    game_over = False

    pygame.quit()

if __name__ == '__main__':
    main()