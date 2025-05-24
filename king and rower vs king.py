import chess
import pygame
import sys
import math
import time
from copy import deepcopy

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 640, 680
BOARD_SIZE = 600
SQUARE_SIZE = BOARD_SIZE // 8
MARGIN = (WIDTH - BOARD_SIZE) // 2

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT = (247, 247, 105, 150)
MOVE_HINT = (106, 168, 79, 150)
TEXT_COLOR = (50, 50, 50)

# Fonts
font = pygame.font.SysFont('Arial', 32)
small_font = pygame.font.SysFont('Arial', 24)

# Piece symbols (Unicode)
PIECE_SYMBOLS = {
    'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
    'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
}

class ChessEndgameSolver:
    def __init__(self):
        self.board = chess.Board()
        self.max_depth = 3
        self.nodes_evaluated = 0
        self.transposition_table = {}
        self.selected_square = None
        self.possible_moves = []
        self.message = ""
        self.message_time = 0
        
    def setup_custom_position(self, white_king_pos, white_rook_pos, black_king_pos):
        """Set up a custom starting position for the endgame"""
        self.board.clear()
        self.board.set_piece_at(white_king_pos, chess.Piece(chess.KING, chess.WHITE))
        self.board.set_piece_at(white_rook_pos, chess.Piece(chess.ROOK, chess.WHITE))
        self.board.set_piece_at(black_king_pos, chess.Piece(chess.KING, chess.BLACK))
        self.board.turn = chess.WHITE
        
    def evaluate_board(self, board):
        """Evaluate the board position with a simple heuristic"""
        self.nodes_evaluated += 1
        
        if board.is_checkmate():
            return math.inf if board.turn == chess.BLACK else -math.inf
        if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
            return 0
            
        white_king = board.king(chess.WHITE)
        white_rook = list(board.pieces(chess.ROOK, chess.WHITE))[0] if board.pieces(chess.ROOK, chess.WHITE) else None
        black_king = board.king(chess.BLACK)
        
        if not white_rook:
            return -math.inf  # Lost the rook
        
        score = 0
        rook_safety = chess.square_distance(white_rook, black_king)
        score += rook_safety * 5
        
        king_proximity = 14 - chess.square_distance(white_king, black_king)
        score += king_proximity * 3
        
        file, rank = chess.square_file(white_rook), chess.square_rank(white_rook)
        centrality = (3.5 - abs(file - 3.5)) + (3.5 - abs(rank - 3.5))
        score += centrality * 2
        
        if (chess.square_file(white_king) == chess.square_file(black_king) or 
            chess.square_rank(white_king) == chess.square_rank(black_king)):
            score += 10
            
        if board.is_check():
            score += 15
            
        return score
    
    def minimax(self, board, depth, alpha, beta, maximizing_player):
        """Minimax algorithm with alpha-beta pruning"""
        board_fen = board.fen()
        if board_fen in self.transposition_table:
            entry = self.transposition_table[board_fen]
            if entry['depth'] >= depth:
                return entry['value']
        
        if depth == 0 or board.is_game_over():
            eval = self.evaluate_board(board)
            self.transposition_table[board_fen] = {'value': eval, 'depth': depth}
            return eval
            
        if maximizing_player:
            max_eval = -math.inf
            for move in board.legal_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, False)
                board.pop()
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            self.transposition_table[board_fen] = {'value': max_eval, 'depth': depth}
            return max_eval
        else:
            min_eval = math.inf
            for move in board.legal_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            self.transposition_table[board_fen] = {'value': min_eval, 'depth': depth}
            return min_eval
    
    def find_best_move(self, board, depth=3):
        """Find the best move using minimax"""
        best_move = None
        best_value = -math.inf if board.turn == chess.WHITE else math.inf
        
        for move in board.legal_moves:
            board.push(move)
            if board.turn == chess.BLACK:
                current_value = self.minimax(board, depth - 1, -math.inf, math.inf, True)
            else:
                current_value = self.minimax(board, depth - 1, -math.inf, math.inf, False)
            board.pop()
            
            if board.turn == chess.WHITE and current_value > best_value:
                best_value = current_value
                best_move = move
            elif board.turn == chess.BLACK and current_value < best_value:
                best_value = current_value
                best_move = move
                
        return best_move
    
    def draw_board(self, screen):
        """Draw the chess board and pieces"""
        # Draw board squares
        for row in range(8):
            for col in range(8):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(
                    screen, color, 
                    (MARGIN + col*SQUARE_SIZE, MARGIN + row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
                
                # Highlight selected square
                if self.selected_square and chess.square(col, 7-row) == self.selected_square:
                    s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    s.fill(HIGHLIGHT)
                    screen.blit(s, (MARGIN + col*SQUARE_SIZE, MARGIN + row*SQUARE_SIZE))
                
                # Highlight possible moves
                for move in self.possible_moves:
                    if move.from_square == self.selected_square and move.to_square == chess.square(col, 7-row):
                        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                        s.fill(MOVE_HINT)
                        screen.blit(s, (MARGIN + col*SQUARE_SIZE, MARGIN + row*SQUARE_SIZE))
        
        # Draw pieces
        for row in range(8):
            for col in range(8):
                piece = self.board.piece_at(chess.square(col, 7-row))
                if piece:
                    text_color = WHITE if piece.color == chess.WHITE else BLACK
                    text = font.render(PIECE_SYMBOLS[piece.symbol()], True, text_color)
                    screen.blit(text, 
                               (MARGIN + col*SQUARE_SIZE + SQUARE_SIZE//2 - text.get_width()//2,
                                MARGIN + row*SQUARE_SIZE + SQUARE_SIZE//2 - text.get_height()//2))
        
        # Draw coordinates
        for i in range(8):
            # Files (a-h)
            text = small_font.render(chr(97 + i), True, TEXT_COLOR)
            screen.blit(text, (MARGIN + i*SQUARE_SIZE + SQUARE_SIZE//2 - text.get_width()//2, MARGIN + BOARD_SIZE + 5))
            
            # Ranks (1-8)
            text = small_font.render(str(8 - i), True, TEXT_COLOR)
            screen.blit(text, (MARGIN - 20, MARGIN + i*SQUARE_SIZE + SQUARE_SIZE//2 - text.get_height()//2))
        
        # Draw game info
        turn_text = "Turn: White" if self.board.turn == chess.WHITE else "Turn: Black"
        text = font.render(turn_text, True, TEXT_COLOR)
        screen.blit(text, (20, 20))
        
        if self.message and time.time() - self.message_time < 3:
            text = small_font.render(self.message, True, TEXT_COLOR)
            screen.blit(text, (20, 60))
    
    def handle_click(self, pos):
        """Handle mouse clicks on the board"""
        x, y = pos
        if MARGIN <= x < MARGIN + BOARD_SIZE and MARGIN <= y < MARGIN + BOARD_SIZE:
            col = (x - MARGIN) // SQUARE_SIZE
            row = (y - MARGIN) // SQUARE_SIZE
            square = chess.square(col, 7-row)
            
            if self.board.turn == chess.BLACK:  # Human player's turn
                piece = self.board.piece_at(square)
                
                if piece and piece.color == chess.BLACK:
                    self.selected_square = square
                    self.possible_moves = [m for m in self.board.legal_moves if m.from_square == square]
                elif self.selected_square:
                    move = chess.Move(self.selected_square, square)
                    if move in self.board.legal_moves:
                        self.board.push(move)
                        self.selected_square = None
                        self.possible_moves = []
                        self.message = ""
                        return True  # Move made
                    else:
                        self.message = "Invalid move!"
                        self.message_time = time.time()
            else:
                self.message = "Wait for computer to move"
                self.message_time = time.time()
        
        return False
    
    def computer_move(self):
        """Make the computer's move"""
        if self.board.is_game_over():
            return False
            
        if self.board.turn == chess.WHITE:
            start_time = time.time()
            move = self.find_best_move(self.board, self.max_depth)
            end_time = time.time()
            
            if move:
                self.board.push(move)
                self.message = f"Computer moved: {self.board.san(move)} (in {end_time - start_time:.2f}s)"
                self.message_time = time.time()
                return True
        
        return False
    
    def run(self):
        """Main game loop"""
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("King and Rook vs. King - Chess Endgame Solver")
        
        # Setup initial position
        self.setup_custom_position(chess.E1, chess.A1, chess.E8)
        
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.handle_click(event.pos):
                        # Human made a move, now computer's turn
                        pygame.time.delay(500)  # Small delay before computer moves
                        self.computer_move()
            
            # Draw everything
            screen.fill(WHITE)
            self.draw_board(screen)
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = ChessEndgameSolver()
    game.run()