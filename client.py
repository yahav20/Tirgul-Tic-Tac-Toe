import socket
import json
import threading
import time

HOST = "127.0.0.1"
PORT = 5000
FORMAT = "utf-8"

class Client:
    def __init__(self):
        # Initialize client state and network socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.game_id = None
        self.player_id = None
        self.symbol = None
        self.my_turn = False
        self.game_over = False

    def connect(self):
        # Establish connection to the server
        try:
            self.sock.connect((HOST, PORT))
        except:
            print("Connection failed.")
            exit(1)

    def send(self, obj):
        # Helper to send JSON-encoded data
        self.sock.send(json.dumps(obj).encode(FORMAT))

    def listen(self):
        # Background thread to listen for server updates
        while not self.game_over:
            try:
                data = self.sock.recv(4096).decode(FORMAT)
                if not data: break
                msg = json.loads(data)
                
                # Handle board updates or move errors
                if msg.get("type") == "board_update":
                    self.display_game(msg)
                elif msg.get("type") == "move_response" and msg.get("status") == "failed":
                    print(f"\n[!] Error: {msg.get('msg')}")
                    self.my_turn = True
            except:
                break

    def display_game(self, msg):
        # Render the board and check for game-ending conditions
        board = msg.get("board")
        print("\n" + "="*10)
        for row in board:
            print("| " + " | ".join(c if c else " " for c in row) + " |")
        print("="*10)
        
        # Check for winner or tie
        winner = msg.get("winner")
        if winner:
            print(f"GAME OVER! Winner is {winner}")
            self.game_over = True
        elif msg.get("tie"):
            print("GAME OVER! It's a tie!")
            self.game_over = True
        else:
            # Update turn status based on server response
            self.my_turn = (msg.get("current_turn") == self.player_id)
            if self.my_turn:
                print("Your turn!")

    def play(self):
        # Main game loop for handling user input
        threading.Thread(target=self.listen, daemon=True).start()
        while not self.game_over:
            if self.my_turn:
                try:
                    r = int(input("Enter Row (0-2): "))
                    c = int(input("Enter Col (0-2): "))
                    self.send({"command": "MOVE", "game_id": self.game_id, "player_id": self.player_id, "row": r, "col": c})
                    self.my_turn = False
                except ValueError:
                    print("Invalid input.")
            else:
                time.sleep(0.5)

    def start(self):
        # Main menu for the client
        self.connect()
        while True:
            print("\n1. List Games\n2. Create Game\n3. Join Game\n4. Quit")
            choice = input("Select: ")
            if choice == "1":
                self.send({"command": "LIST"})
                print(self.sock.recv(1024).decode(FORMAT))
            elif choice == "2":
                self.send({"command": "CREATE"})
                res = json.loads(self.sock.recv(1024).decode(FORMAT))
                self.game_id, self.player_id, self.symbol = res['game_id'], res['player_id'], res['symbol']
                print(f"Created game {self.game_id} as {self.symbol}. Waiting for opponent...")
                self.play()
            elif choice == "3":
                gid = int(input("Enter Game ID: "))
                self.send({"command": "JOIN", "game_id": gid})
                res = json.loads(self.sock.recv(1024).decode(FORMAT))
                if res.get("status") == "success":
                    self.game_id, self.player_id, self.symbol = res['game_id'], res['player_id'], res['symbol']
                    print(f"Joined game {self.game_id} as {self.symbol}")
                    self.play()
            elif choice == "4":
                break

if __name__ == "__main__":
    Client().start()