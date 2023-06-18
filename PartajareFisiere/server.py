import socket
import threading
import os


class Server:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 5555
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []
        self.file_list = {}

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print('Serverul asculta pe adresa {}:{}'.format(self.host, self.port))

        while True:
            client_socket, client_address = self.server_socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

    def handle_client(self, client_socket):
        try:
            username = client_socket.recv(1024).decode('utf-8')
            self.clients.append((username, client_socket))
            self.send_file_list(client_socket)
            self.receive_file_list(client_socket)
            self.notify_clients(username)  # Notificăm clienții despre noua conexiune
            print('Utilizatorul "{}" s-a conectat.'.format(username))

            while True:
                try:
                    data = client_socket.recv(1024).decode('utf-8')
                    if data:
                        if data == 'EXIT':
                            self.remove_client(client_socket, username)
                            print('Utilizatorul "{}" a încheiat sesiunea.'.format(username))
                            break
                        elif data.startswith('DOWNLOAD'):
                            self.send_file(client_socket, data.split()[1])
                            print('Utilizatorul "{}" a descărcat fișierul "{}".'.format(username, data.split()[1]))
                        elif data.startswith('REQUEST'):
                            self.request_file(client_socket, username, data.split()[1])
                        else:
                            self.handle_command(client_socket, username, data)
                except ConnectionAbortedError:
                    # Conexiunea a fost întreruptă brusc, tratăm eroarea și ieșim din buclă
                    self.remove_client(client_socket, username)
                    print('Conexiunea cu utilizatorul "{}" a fost întreruptă brusc.'.format(username))
                    break
        except ConnectionAbortedError:
            # Conexiunea a fost întreruptă brusc la momentul autentificării, închidem socket-ul
            client_socket.close()

    def send_file_list(self, client_socket):
        file_list = ', '.join(self.file_list.keys())
        client_socket.send(file_list.encode('utf-8'))

    def receive_file_list(self, client_socket):
        data = client_socket.recv(1024).decode('utf-8')
        file_list = data.split(',')
        for file in file_list:
            self.file_list[file.strip()] = client_socket

    def handle_command(self, client_socket, username, command):
        if command.startswith('PUBLISH'):
            filename = command.split()[1]
            self.file_list[filename] = username
            self.notify_clients(username, filename)
            print('Utilizatorul "{}" a publicat fișierul "{}".'.format(username, filename))
        elif command == 'GET_FILES':
            self.send_file_list(client_socket)
        elif command == 'GET_ALL_FILES':
            all_files = self.get_all_files()
            client_socket.send(all_files.encode('utf-8'))
        else:
            client_socket.send('Comanda nevalida.'.encode('utf-8'))


    def download_files(self, client_socket, username):
        client_files = [file for file, owner in self.file_list.items() if owner == username]
        for file in client_files:
            self.send_file(client_socket, file)

    def request_file(self, client_socket, username, filename):
        if filename in self.file_list:
            owner_socket = self.file_list[filename]
            owner_socket.send(('REQUEST ' + filename).encode('utf-8'))
            file_data = owner_socket.recv(1024)
            client_socket.send(file_data)
            print('Utilizatorul "{}" a descărcat fișierul "{}" de la utilizatorul "{}".'.format(username, filename, self.file_list[filename]))
        else:
            client_socket.send('Fisierul nu exista.'.encode('utf-8'))

    def send_file(self, client_socket, filename):
        if filename in self.file_list:
            with open(filename, 'rb') as file:
                file_data = file.read(1024)
                while file_data:
                    client_socket.send(file_data)
                    file_data = file.read(1024)
        else:
            client_socket.send('Fisierul nu exista.'.encode('utf-8'))

    def notify_clients(self, username, filename=None, disconnect=False):
        if disconnect:
            message = 'Utilizatorul {} s-a deconectat.'.format(username)
        else:
            message = 'Adaugat fisierul "{}" de catre {}'.format(filename, username) if filename else 'S-a conectat utilizatorul {}'.format(username)
        print('Notificare trimisă:', message)
        for client in self.clients:
            if client[0] != username:
                client[1].send(message.encode('utf-8'))

    def remove_client(self, client_socket, username):
        for client in self.clients:
            if client[1] == client_socket:
                self.clients.remove(client)
                self.notify_clients(username, disconnect=True)  # Notificăm clienții despre deconectarea utilizatorului
                break

        client_socket.send('EXIT'.encode('utf-8'))
        client_socket.close()

    def get_all_files(self):
        return ', '.join(self.file_list.keys())
server = Server()
server.start()
