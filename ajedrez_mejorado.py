import pygame
import chess
import time

# Constants
WIDTH, HEIGHT = 600, 600
SQUARE_SIZE = WIDTH // 8
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_SQUARE = (238, 238, 210)
DARK_SQUARE = (118, 150, 86)
YELLOW = (255, 255, 0, 150)
RED = (255, 0, 0, 150)
GREEN = (0, 255, 0, 150)

# Dictionary to hold piece images
PIECES = {}

def load_images():
    pieces = {
        'K': "KW.png",  # Rey blanco
        'k': "k.png",   # Rey negro
        'r': "R.png"    # Torre negra
    }
    for symbol, path in pieces.items():
        try:
            image = pygame.image.load(path)
            PIECES[symbol] = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))
        except:
            # Imagen no encontrada: creamos superficie con letra
            surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
            surf.fill((200, 200, 255) if symbol.isupper() else (50, 50, 50))
            font = pygame.font.SysFont('Arial', 48)
            text_color = BLACK if symbol.isupper() else WHITE
            text = font.render(symbol, True, text_color)
            surf.blit(text, (SQUARE_SIZE//2 - text.get_width()//2, SQUARE_SIZE//2 - text.get_height()//2))
            PIECES[symbol] = surf

def draw_board(screen, board):
    for row in range(8):
        for col in range(8):
            color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
            pygame.draw.rect(screen, color, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
    # Si está en jaque, pinta el rey de rojo semitransparente
    if board.is_check():
        king_square = board.king(board.turn)
        if king_square is not None:
            col = chess.square_file(king_square)
            row = 7 - chess.square_rank(king_square)
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill((255, 0, 0, 120))
            screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))

def draw_pieces(screen, board):
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            piece_str = piece.symbol()
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            screen.blit(PIECES[piece_str], (col * SQUARE_SIZE, row * SQUARE_SIZE))

def draw_highlights(screen, selected_square, valid_moves, board):
    if selected_square is not None:
        col = chess.square_file(selected_square)
        row = 7 - chess.square_rank(selected_square)
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        s.fill(YELLOW)
        screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))

        for move in valid_moves:
            if move.from_square == selected_square:
                col = chess.square_file(move.to_square)
                row = 7 - chess.square_rank(move.to_square)
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                if board.is_capture(move):
                    s.fill(RED)
                else:
                    s.fill(GREEN)
                screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))

def get_square_under_mouse(pos):
    x, y = pos
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        col = x // SQUARE_SIZE
        row = y // SQUARE_SIZE
        return chess.square(col, 7 - row)
    return None

def evaluate_board(board):
    # Evaluación simple para Rey vs Rey y Torre
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
    dist_rook = max(abs(chess.square_file(white_king) - chess.square_file(black_rook)),
                    abs(chess.square_rank(white_king) - chess.square_rank(black_rook)))
    dist_kings = max(abs(chess.square_file(white_king) - chess.square_file(black_king)),
                     abs(chess.square_rank(white_king) - chess.square_rank(black_king)))
    
    if board.is_check():
        evaluation += 50 if board.turn == chess.BLACK else -30
    
    edge_dist = min(chess.square_file(white_king), 7 - chess.square_file(white_king),
                    chess.square_rank(white_king), 7 - chess.square_rank(white_king))
    evaluation += (4 - edge_dist) * 15
    
    if (chess.square_file(white_king) == chess.square_file(black_rook) or
        chess.square_rank(white_king) == chess.square_rank(black_rook)):
        evaluation += 20
        if dist_rook > 1:
            evaluation += 10
    
    if dist_kings <= 1:
        evaluation -= 30
    
    if (abs(chess.square_file(white_king) - chess.square_file(black_king)) == 2 and
        chess.square_rank(white_king) == chess.square_rank(black_king)) or \
       (abs(chess.square_rank(white_king) - chess.square_rank(black_king)) == 2 and
        chess.square_file(white_king) == chess.square_file(black_king)):
        evaluation += 25
    
    return evaluation if board.turn == chess.BLACK else -evaluation

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
            eval, _ = minimax(board, depth - 1, alpha, beta, False)
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
            eval, _ = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            if eval < min_eval:
                min_eval = eval
                best_move = move
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval, best_move

def get_ai_move(board, depth=3):
    start_time = time.time()
    best_move = None
    
    # Si hay jaque mate directo, ejecutar inmediatamente
    for move in board.legal_moves:
        board.push(move)
        if board.is_checkmate():
            board.pop()
            return move
        board.pop()
    
    # Buscar mejor jugada con minimax
    for current_depth in range(1, depth + 1):
        _, best_move = minimax(board, current_depth, -float('inf'), float('inf'), board.turn == chess.BLACK)
        # Romper si el juego termina o pasa mucho tiempo
        if board.is_checkmate() or board.is_stalemate() or time.time() - start_time > 2:
            break
    
    return best_move

def show_message(screen, message):
    font = pygame.font.SysFont('Arial', 36)
    text = font.render(message, True, BLACK)
    rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    
    s = pygame.Surface((rect.width + 40, rect.height + 20), pygame.SRCALPHA)
    s.fill((255, 255, 255, 200))
    screen.blit(s, (rect.x - 20, rect.y - 10))
    
    pygame.draw.rect(screen, RED, (rect.x - 20, rect.y - 10, rect.width + 40, rect.height + 20), 3)
    
    screen.blit(text, rect)
    pygame.display.update()
    pygame.time.wait(2000)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Rey vs Rey y Torre")
    clock = pygame.time.Clock()
    
    load_images()
    
    board = chess.Board()
    
    # Setup inicial sólo con rey blanco, rey negro y torre negra
    board.clear_board()
    board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    board.set_piece_at(chess.H8, chess.Piece(chess.ROOK, chess.BLACK))
    board.turn = chess.WHITE
    
    selected_square = None
    valid_moves = []
    
    running = True
    while running:
        screen.fill(WHITE)
        draw_board(screen, board)
        draw_pieces(screen, board)
        draw_highlights(screen, selected_square, valid_moves, board)
        pygame.display.flip()
        clock.tick(30)
        
        if board.is_checkmate():
            show_message(screen, "¡Jaque Mate! Fin del juego.")
            running = False
            continue
        if board.is_stalemate():
            show_message(screen, "¡Tablas! Fin del juego.")
            running = False
            continue
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if board.turn == chess.WHITE:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    sq = get_square_under_mouse(event.pos)
                    if sq is not None:
                        piece = board.piece_at(sq)
                        if selected_square is None:
                            if piece and piece.color == chess.WHITE:
                                selected_square = sq
                                valid_moves = [move for move in board.legal_moves if move.from_square == sq]
                        else:
                            move = chess.Move(selected_square, sq)
                            if move in board.legal_moves:
                                board.push(move)
                                selected_square = None
                                valid_moves = []
                            else:
                                # Seleccionar otro cuadrado si es pieza blanca
                                if piece and piece.color == chess.WHITE:
                                    selected_square = sq
                                    valid_moves = [move for move in board.legal_moves if move.from_square == sq]
                                else:
                                    selected_square = None
                                    valid_moves = []
            
            else:
                # Turno de las negras (IA)
                ai_move = get_ai_move(board, depth=3)
                if ai_move:
                    board.push(ai_move)
                else:
                    running = False

    pygame.quit()

if __name__ == "__main__":
    main()
