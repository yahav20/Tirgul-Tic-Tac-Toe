import socket
import json
import threading

HOST = '127.0.0.1'
PORT = 5000
FORMAT = 'utf-8'
ADDR = (HOST, PORT)

class Game:
    def __init__(self):
        # Initialize game state: 2 players, 3x3 board, and turn tracking
        self.num_players = 2
        self.symbols = ['X', 'O']
        self.board_size = 3
        self.board = [['' for _ in range(3)] for _ in range(3)]
        self.current_turn = 0
        self.game_over = False
        self.started = False

    def make_move(self, player: int, row: int, col: int) -> tuple:
        # Validate move: check if game started, bounds, and if it's the player's turn
        if not self.started:
            return False, "The game has not started yet"
        if not (0 <= row < 3 and 0 <= col < 3):
            return False, "Out of bounds"
        if player != self.current_turn:
            return False, "Not your turn"
        if self.board[row][col] != '':
            return False, "Cell already occupied"
        self.board[row][col] = self.symbols[player]
        self.current_turn = (self.current_turn + 1) % self.num_players
        return True, ""

    def check_winner(self) -> str:
        # Check all possible winning combinations (rows, columns, diagonals)
        b = self.board
        lines = [
            [b[0][0], b[0][1], b[0][2]], [b[1][0], b[1][1], b[1][2]], [b[2][0], b[2][1], b[2][2]], # lines
            [b[0][0], b[1][0], b[2][0]], [b[0][1], b[1][1], b[2][1]], [b[0][2], b[1][2], b[2][2]], # columns
            [b[0][0], b[1][1], b[2][2]], [b[0][2], b[1][1], b[2][0]] # diagonals
        ]
        for line in lines:
            if line[0] == line[1] == line[2] and line[0] != '':
                self.game_over = True
                return line[0]
        return None

    def check_tie(self):
        # A tie occurs if the board is full and there is no winner
        board_full = all(cell != '' for row in self.board for cell in row)
        return board_full and not self.check_winner()

class Server:
    def __init__(self):
        # Setup TCP server and storage for active games and players
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(ADDR)
        self.server.listen()
        self.games = {}
        self.game_players = {}
        self.game_counter = 0
        print(f"Server started on {HOST}:{PORT}")

    def handle_client(self, client: socket.socket):
        # Main loop to handle incoming JSON commands from a specific client
        while True:
            try:
                message = client.recv(1024).decode(FORMAT)
                if not message: break
                data = json.loads(message)
                command = data.get('command')

                # Return a list of available game rooms
                if command == 'LIST':
                    rooms = [{'game_id': i, 'players': len(p)} for i, p in self.game_players.items() if not self.games[i].game_over]
                    client.send(json.dumps({'rooms': rooms}).encode(FORMAT))
                
                # Create a new game instance and assign the creator as Player 0 (X)
                elif command == 'CREATE':
                    gid = self.game_counter
                    self.game_counter += 1
                    self.games[gid] = Game()
                    self.game_players[gid] = [client]
                    client.send(json.dumps({"status": "success", "game_id": gid, "player_id": 0, "symbol": "X"}).encode(FORMAT))
                
                # Join an existing game and start it if two players are present
                elif command == 'JOIN':
                    gid = data.get('game_id')
                    if gid in self.games and len(self.game_players[gid]) < 2:
                        self.game_players[gid].append(client)
                        game = self.games[gid]
                        game.started = True
                        client.send(json.dumps({"status": "success", "game_id": gid, "player_id": 1, "symbol": "O"}).encode(FORMAT))
                        self.broadcast_board(gid)
                    else:
                        client.send(json.dumps({"status": "error", "msg": "Cannot join"}).encode(FORMAT))

                # Process a move request and broadcast the updated board to all players in the game
                elif command == 'MOVE':
                    gid, pid = data.get('game_id'), data.get('player_id')
                    moved, msg = self.games[gid].make_move(pid, data['row'], data['col'])
                    if moved:
                        self.broadcast_board(gid)
                    else:
                        client.send(json.dumps({"type": "move_response", "status": "failed", "msg": msg}).encode(FORMAT))
            except:
                break

    def broadcast_board(self, gid):
        # Send the current board state and game status to both players in a room
        game = self.games[gid]
        msg = json.dumps({
            "type": "board_update",
            "board": game.board,
            "current_turn": game.current_turn,
            "winner": game.check_winner(),
            "tie": game.check_tie()
        })
        for sock in self.game_players[gid]:
            sock.send(msg.encode(FORMAT))

    def start(self):
        # Accept new connections and spawn a thread for each client
        while True:
            conn, _ = self.server.accept()
            threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()

if __name__ == '__main__':
    Server().start()