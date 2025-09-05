import socket
import threading
from utils import print_yellow

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345

active_connections = []
usernames = []

def send_to_all(msg_data):
    for sock in active_connections:
        try:
            sock.send(msg_data)
        except Exception:
            pass  # Optionally, log error or handle cleanup

def manage_single_client(sock):
    while True:
        try:
            recv_data = sock.recv(1024)
            if recv_data:
                send_to_all(recv_data)
        except Exception:
            idx = active_connections.index(sock)
            left_user = usernames[idx]
            send_to_all(f"{left_user} left the room.".encode('utf-8'))
            sock.close()
            del active_connections[idx]
            del usernames[idx]
            break

def accept_new_connections():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen()
    print_yellow(f"Chat server live at {SERVER_HOST}:{SERVER_PORT}\nReady for users...")
    while True:
        client_sock, addr = server_socket.accept()
        print_yellow(f"New arrival from {str(addr)}")
        client_sock.send("NICK".encode('utf-8'))
        new_name = client_sock.recv(1024).decode('utf-8')
        usernames.append(new_name)
        active_connections.append(client_sock)
        print_yellow(f"User identified: {new_name}")
        join_msg = f"{new_name} is now online.".encode('utf-8')
        send_to_all(join_msg)
        client_sock.send("You are now connected!".encode('utf-8'))
        threading.Thread(target=manage_single_client, args=(client_sock,)).start()

if __name__ == "__main__":
    accept_new_connections()

