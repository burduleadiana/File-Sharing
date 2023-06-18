import socket
import os

class Client:
    def __init__(self):
        self.server_host = '127.0.0.1'
        self.server_port = 5555
        self.username = ''
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.client_socket.connect((self.server_host, self.server_port))
        self.username = input('Introduceti numele de utilizator: ')
        self.client_socket.send(self.username.encode('utf-8'))

    def publish_files(self):
        file_count = int(input('Introduceti numarul de fisiere pe care doriti sa le publicati: '))
        for _ in range(file_count):
            filename = input('Introduceti numele fisierului: ')
            command = 'PUBLISH {}'.format(filename)
            self.client_socket.send(command.encode('utf-8'))
            print('Ati publicat fisierul "{}".'.format(filename))

    def get_files(self):
        self.client_socket.send('GET_FILES'.encode('utf-8'))
        file_list = self.client_socket.recv(1024).decode('utf-8')
        print('Lista fisierelor publicate: {}'.format(file_list))

    def request_file(self, filename):
        self.client_socket.send(('REQUEST ' + filename).encode('utf-8'))
        file_data = self.client_socket.recv(1024)

        if file_data.decode('utf-8') == 'Fisierul nu exista.':
            print('Fisierul "{}" nu exista.'.format(filename))
        else:
            with open(filename, 'wb') as file:
                file.write(file_data)
                print('Ati descarcat fisierul "{}".'.format(filename))

    def download_files(self):
        self.get_files()
        file_count = int(input('Introduceti numarul de fisiere pe care doriti sa le descarcati: '))
        for _ in range(file_count):
            filename = input('Introduceti numele fisierului: ')
            self.request_file(filename)

    def exit(self):
        self.client_socket.send('EXIT'.encode('utf-8'))
        self.client_socket.close()


    def display_files(self):
        self.client_socket.send('GET_ALL_FILES'.encode('utf-8'))
        file_list = self.client_socket.recv(1024).decode('utf-8')
        print('Lista cu toate fișierele disponibile:')
        print(file_list)


client = Client()
client.connect()

while True:
    print('\nComenzi disponibile:')
    print('1. Publicare fișiere')
    print('2. Descărcare fișiere')
    print('3. Afișare fișiere')
    print('4. Ieșire')

    choice = input('Introduceți numărul comenzii dorite: ')

    if choice == '1':
        client.publish_files()
    elif choice == '2':
        client.download_files()
    elif choice == '3':
        client.display_files()
    elif choice == '4':
        client.exit()
        break
    else:
        print('Comandă nevalidă. Încercați din nou.')