import socket
import threading
import pickle

class Client:
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port
        self.username = None
        self.files = []
        self.connected = False

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server_host, self.server_port))
        self.connected = True
        print("Conectat la server.")

        while self.connected:
            self.show_menu()

    def show_menu(self):
        print("1. Autentificare")
        print("2. Listă fișiere publicate")
        print("3. Descarcă fișier")
        print("4. Deconectare")

        choice = input("Alege o opțiune: ")
        if choice == "1":
            self.login()
        elif choice == "2":
            self.get_published_files()
        elif choice == "3":
            self.download_file()
        elif choice == "4":
            self.logout()
        else:
            print("Opțiune invalidă.")

    def login(self):
        if self.username:
            print("Ești deja autentificat.")
            return

        self.username = input("Introdu numele de utilizator: ")
        self.files = input("Introdu lista de fișiere separate prin virgulă: ").split(",")

        request = {"type": "login", "username": self.username, "files": self.files}
        self.socket.sendall(pickle.dumps(request))
        print(f"Autentificat cu succes ca {self.username}. Fișierele tale publicate: {self.files}")

    def logout(self):
        if not self.username:
            print("Nu ești autentificat.")
            return

        request = {"type": "logout", "username": self.username}
        self.socket.sendall(pickle.dumps(request))
        self.username = None
        self.files = []
        self.connected = False
        print("Deconectare.")

    def get_published_files(self):
        if not self.username:
            print("Nu ești autentificat.")
            return

        request = {"type": "get_files", "username": self.username}
        self.socket.sendall(pickle.dumps(request))

        response = self.socket.recv(1024)
        if response:
            files = pickle.loads(response)["files"]
            print("Fișiere publicate:")
            for file in files:
                print(file)

    def download_file(self):
        if not self.username:
            print("Nu esti autentificat.")
            return

        request = {"type": "download_file", "username": self.username}
        self.socket.sendall(pickle.dumps(request))

        response = self.socket.recv(1024)
        if response:
            response_data = pickle.loads(response)
            files = response_data.get("files")
            if files:
                print("Fisiere disponibile pentru descarcare:")
                for i, file in enumerate(files):
                    print(f"{i + 1}. {file}")
                file_number = input("Introdu numarul fisierului pe care doresti sa-l descarci: ")
                try:
                    file_number = int(file_number)
                    if file_number >= 1 and file_number <= len(files):
                        filename = files[file_number - 1]
                        self.request_file(filename)
                    else:
                        print("Numarul fisierului este invalid.")
                except ValueError:
                    print("Numarul fisierului este invalid.")
            else:
                print("Nu exista fisiere disponibile pentru descarcare.")
        else:
            print("Nu s-a primit niciun raspuns de la server.")

    def request_file(self, filename):
        request = {"type": "file_request", "username": self.username, "filename": filename}
        self.socket.sendall(pickle.dumps(request))

        response = self.socket.recv(1024)
        if response:
            response_data = pickle.loads(response)
            file_content = response_data.get("content")
            if file_content:
                self.save_file(filename, file_content)
                print("Fisierul a fost descarcat cu succes.")
            else:
                print("Nu s-a putut gasi fisierul.")
        else:
            print("Nu s-a primit niciun raspuns de la server.")

    def save_file(self, filename, content):
        with open(filename, "wb") as file:
            file.write(content)
        print(f"Fisierul {filename} a fost salvat in sistemul de fisiere.")

    def send_file_content(self, filename):
        with open(filename, "rb") as file:
            content = file.read()
        request = {"type": "file_content", "username": self.username, "filename": filename, "content": content}
        self.socket.sendall(pickle.dumps(request))
        print(f"Fișierul {filename} a fost trimis către server.")


if __name__ == "__main__":
    client = Client("localhost", 8000)
    client.connect()