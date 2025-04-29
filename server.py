from socket import *
import threading

server_socket = socket(AF_INET, SOCK_STREAM)
server_socket.bind(('localhost', 8080))  # Use a fixed port
server_socket.listen(5)
print("Server running...")

clients = []


def broadcast(message):
    for client in clients:
        try:
            client.send(f"{message}\n".encode())
        except:
            pass


def handle_client(client_socket):
    name = client_socket.recv(1024).decode().strip()
    broadcast(f"{name} joined!")

    while True:
        try:
            message = client_socket.recv(1024).decode().strip()
            broadcast(f"{name}: {message}")
        except:
            clients.remove(client_socket)
            broadcast(f"{name} left!")
            client_socket.close()
            break


while True:
    client_socket, addr = server_socket.accept()
    clients.append(client_socket)
    threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()
