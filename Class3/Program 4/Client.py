import socket

# Replace 'SERVER_IP_ADDRESS' with the actual IP address of the server
SERVER_IP = '192.168.X.X'  # Example: '192.168.1.100'
PORT = 5555

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, PORT))

try:
    while True:
        # Send a message to the server (you could replace this with game-specific data)
        message = input("Enter message to send to the server: ")
        client_socket.send(message.encode('utf-8'))

        # Optionally receive a response
        response = client_socket.recv(1024).decode('utf-8')
        print(f"Server: {response}")

except KeyboardInterrupt:
    print("\nDisconnecting from server...")
    client_socket.close()
