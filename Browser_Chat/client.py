import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox

HOST = '127.0.0.1'
PORT = 12345

class ChatServer:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.clients = []
        self.nicknames = []
        print(f"Server started on {self.host}:{self.port}")

    def broadcast(self, message, _client):
        for client in self.clients:
            if client != _client:
                try:
                    client.send(message)
                except:
                    client.close()
                    if client in self.clients:
                        self.clients.remove(client)

    def handle_client(self, client):
        while True:
            try:
                message = client.recv(1024)
                if not message:
                    raise ConnectionResetError
                self.broadcast(message, client)
            except:
                index = self.clients.index(client)
                client.close()
                self.clients.remove(client)
                nickname = self.nicknames[index]
                self.nicknames.remove(nickname)
                self.broadcast(f'{nickname} left the chat.'.encode('utf-8'), client)
                break

    def receive(self):
        while True:
            client, address = self.server_socket.accept()
            print(f"Connected with {str(address)}")
            client.send('NICK'.encode('utf-8'))
            nickname = client.recv(1024).decode('utf-8')
            self.nicknames.append(nickname)
            self.clients.append(client)

            print(f"Nickname of the client is {nickname}")
            self.broadcast(f'{nickname} joined the chat!'.encode('utf-8'), client)
            client.send('Connected to the server!'.encode('utf-8'))

            thread = threading.Thread(target=self.handle_client, args=(client,))
            thread.start()

class ChatClient:
    def __init__(self, master):
        self.master = master
        self.master.title("Chat Application - GUI")
        self.master.configure(bg='black')

        self.chat_area = scrolledtext.ScrolledText(master, bg='black', fg='yellow', state='disabled')
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.entry_msg = tk.Entry(master, bg='black', fg='yellow')
        self.entry_msg.pack(padx=10, pady=(0,10), fill=tk.X, side=tk.LEFT, expand=True)

        self.send_btn = tk.Button(master, text="Send", command=self.send_message, bg='yellow', fg='black')
        self.send_btn.pack(padx=(0,10), pady=(0,10), side=tk.RIGHT)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((HOST, PORT))

        self.nickname = simpledialog.askstring("Nickname", "Choose your nickname", parent=self.master)

        threading.Thread(target=self.receive_messages, daemon=True).start()

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message == 'NICK':
                    self.client_socket.send(self.nickname.encode('utf-8'))
                else:
                    self.chat_area.configure(state='normal')
                    self.chat_area.insert(tk.END, message + "\n")
                    self.chat_area.configure(state='disabled')
                    self.chat_area.yview(tk.END)
            except:
                messagebox.showerror("Error", "Connection lost")
                self.client_socket.close()
                break

    def send_message(self):
        message = f'{self.nickname}: {self.entry_msg.get()}'
        self.client_socket.send(message.encode('utf-8'))
        self.entry_msg.delete(0, tk.END)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'server':
        server = ChatServer()
        server.receive()
    else:
        root = tk.Tk()
        client_app = ChatClient(root)
        root.mainloop()
