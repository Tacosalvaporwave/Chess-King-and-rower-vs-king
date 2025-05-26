import pygame
import chess
import time
from pygame import gfxdraw

# Constants
WIDTH, HEIGHT = 480, 480
SQUARE_SIZE = WIDTH // 8
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_BLUE = (173, 216, 230)
DARK_BLUE = (0, 0, 139)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Dictionary to hold piece images
PIECES = {}

def load_images():
    pieces = {
        'K': "KW.png",
        'R': "R.png",
        'k': "k.png"
    }
    for symbol, path in pieces.items():
        try:
            PIECES[symbol] = pygame.transform.scale(
                pygame.image.load(path), (SQUARE_SIZE, SQUARE_SIZE))
        except:
            # Create a placeholder if image not found
            surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
            surf.fill((255, 0, 255) if symbol.isupper() else (0, 255, 255))
            font = pygame.font.SysFont(None, 36)
            text = font.render(symbol, True, BLACK)
            surf.blit(text, (SQUARE_SIZE//2 - text.get_width()//2, 
                            SQUARE_SIZE//2 - text.get_height()//2))
            PIECES[symbol] = surf

def draw_board(screen):
    colors = [WHITE, GRAY]
    for r in range(8):
        for c in range(8):
            color = colors[(r + c) % 2]
            pygame.draw.rect(screen, color, pygame.Rect(c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def draw_pieces(screen, board):
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            piece_str = piece.symbol()
            row, col = 7 - square // 8, square % 8
            screen.blit(PIECES[piece_str], (col * SQUARE_SIZE, row * SQUARE_SIZE))

def draw_highlights(screen, selected_square, valid_moves):
    if selected_square is not None:
        col = chess.square_file(selected_square)
        row = 7 - chess.square_rank(selected_square)
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        s.fill((255, 255, 0, 128))
        screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
        
        for move in valid_moves:
            if move.from_square == selected_square:
                col = chess.square_file(move.to_square)
                row = 7 - chess.square_rank(move.to_square)
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                s.fill((0, 255, 0, 128))
                screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
                
                # Draw a circle to indicate valid moves
                center = (col * SQUARE_SIZE + SQUARE_SIZE // 2, 
                          row * SQUARE_SIZE + SQUARE_SIZE // 2)
                radius = SQUARE_SIZE // 4
                pygame.draw.circle(screen, GREEN, center, radius, 2)

def get_square_under_mouse(pos):
    x, y = pos
    row = 7 - y // SQUARE_SIZE
    col = x // SQUARE_SIZE
    return chess.square(col, row)

def evaluate_board(board):
    """Improved evaluation function for KR vs K endgame"""
    if board.is_checkmate():
        return 10000 if board.turn == chess.BLACK else -10000
    if board.is_stalemate():
        return -500  # Penalize stalemate
    
    # Get piece positions
    white_king = board.king(chess.WHITE)
    white_rook = None
    black_king = board.king(chess.BLACK)
    
    # Find the white rook
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == chess.WHITE and piece.piece_type == chess.ROOK:
            white_rook = square
            break
    
    if not white_rook:
        return 0  # Shouldn't happen in this endgame
    
    # Distance between black king and white rook
    bk_file, bk_rank = chess.square_file(black_king), chess.square_rank(black_king)
    wr_file, wr_rank = chess.square_file(white_rook), chess.square_rank(white_rook)
    distance_rook = max(abs(bk_file - wr_file), abs(bk_rank - wr_rank))
    
    # Distance between kings
    wk_file, wk_rank = chess.square_file(white_king), chess.square_rank(white_king)
    distance_kings = max(abs(bk_file - wk_file), abs(bk_rank - wk_rank))
    
    # Encourage pushing the black king to the edge
    edge_distance = min(
        black_king % 8, 7 - (black_king % 8),
        black_king // 8, 7 - (black_king // 8))
    
    # Encourage rook to be on the same rank/file as black king but not adjacent
    rook_alignment = 0
    if bk_file == wr_file or bk_rank == wr_rank:
        rook_alignment = 2
        if distance_rook > 1:  # More points if not adjacent (safe position)
            rook_alignment = 5
    
    # Encourage opposition (kings facing each other with one square in between)
    opposition = 0
    if distance_kings == 1:
        opposition = -50  # Don't let kings get too close
    elif (abs(bk_file - wk_file) == 2 and bk_rank == wk_rank) or \
         (abs(bk_rank - wk_rank) == 2 and bk_file == wk_file):
        opposition = 20
    
    # Encourage checks
    check_bonus = 10 if board.is_check() else 0
    
    # The evaluation from white's perspective
    evaluation = (100 - edge_distance * 10 + 
                 rook_alignment + 
                 opposition + 
                 check_bonus - 
                 distance_kings * 2)
    
    # Return from current player's perspective
    return evaluation if board.turn == chess.WHITE else -evaluation

def minimax(board, depth, alpha, beta, maximizing_player):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board), None
    
    best_move = None
    legal_moves = list(board.legal_moves)
    
    # Sort moves to help alpha-beta pruning
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
    """Quick evaluation of a move to help with move ordering"""
    board.push(move)
    score = 0
    
    # Checkmate is best
    if board.is_checkmate():
        score = 10000
    # Checks are good
    elif board.is_check():
        score = 50
    # Captures are good (though rare in this endgame)
    elif board.is_capture(move):
        score = 30
    
    # Encourage moving king toward the center (for black)
    if board.turn == chess.WHITE:  # We just made a move, so turn has changed
        piece = board.piece_at(move.to_square)
        if piece and piece.piece_type == chess.KING:
            file, rank = chess.square_file(move.to_square), chess.square_rank(move.to_square)
            center_distance = max(abs(3.5 - file), abs(3.5 - rank))
            score += 10 - center_distance
    
    board.pop()
    return score

def get_ai_move(board, depth=3):
    """Get the AI move with iterative deepening"""
    best_move = None
    # Start with depth 1 and increase to see if we can find a quick mate
    for current_depth in range(1, depth+1):
        _, best_move = minimax(board, current_depth, -float('inf'), float('inf'), board.turn == chess.WHITE)
        # If we found a mate, no need to search deeper
        if board.is_checkmate() or board.is_stalemate():
            break
    return best_move

def show_message(screen, message):
    font = pygame.font.SysFont('Arial', 36)
    text = font.render(message, True, RED)
    rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
    
    # Create a semi-transparent background
    s = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
    s.fill((0, 0, 0, 180))
    screen.blit(s, (rect.x - 10, rect.y - 10))
    
    screen.blit(text, rect)
    pygame.display.flip()
    time.sleep(3)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("King and Rook vs King - Play as White")
    load_images()

    # Set up the initial position
    board = chess.Board()
    board.clear()
    board.set_piece_at(chess.E1, chess.Piece.from_symbol("K"))  # White King
    board.set_piece_at(chess.A1, chess.Piece.from_symbol("R"))  # White Rook
    board.set_piece_at(chess.E8, chess.Piece.from_symbol("k"))  # Black King

    selected_square = None
    valid_moves = []
    running = True

    while running:
        draw_board(screen)
        draw_highlights(screen, selected_square, valid_moves)
        draw_pieces(screen, board)
        pygame.display.flip()

        if board.is_checkmate():
            winner = "Black" if board.turn == chess.WHITE else "White"
            show_message(screen, f"Checkmate! {winner} wins!")
            running = False
            continue
        elif board.is_stalemate():
            show_message(screen, "Stalemate! Draw!")
            running = False
            continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if board.turn == chess.WHITE:  # Human's turn
                    square = get_square_under_mouse(pygame.mouse.get_pos())
                    piece = board.piece_at(square)
                    
                    # Select a piece
                    if selected_square is None:
                        if piece and piece.color == chess.WHITE:
                            selected_square = square
                            valid_moves = [m for m in board.legal_moves if m.from_square == square]
                    # Move the selected piece
                    else:
                        move = chess.Move(selected_square, square)
                        if move in board.legal_moves:
                            board.push(move)
                            selected_square = None
                            valid_moves = []
                            
                            # AI's turn
                            if not board.is_game_over():
                                pygame.display.flip()  # Update display before AI thinks
                                ai_move = get_ai_move(board, 3)
                                if ai_move:
                                    board.push(ai_move)
                        elif piece and piece.color == chess.WHITE:
                            # Clicked on another white piece - select it instead
                            selected_square = square
                            valid_moves = [m for m in board.legal_moves if m.from_square == square]
                        else:
                            selected_square = None
                            valid_moves = []

    pygame.quit()

if __name__ == '__main__':
    main()