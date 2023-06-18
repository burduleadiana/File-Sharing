import socket
import threading
import pickle

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = {}
        self.published_files = {}
        self.lock = threading.Lock()

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        print(f"Serverul rulează pe {self.host}:{self.port}")

        while True:
            client_socket, address = self.socket.accept()
            thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            thread.start()

    def handle_client(self, client_socket):
        while True:
            try:
                data = client_socket.recv(1024)
                if data:
                    request = pickle.loads(data)
                    if request["type"] == "login":
                        username = request["username"]
                        files = request["files"]
                        self.add_client(username, client_socket, files)
                    elif request["type"] == "logout":
                        username = request["username"]
                        self.remove_client(username)
                    elif request["type"] == "get_files":
                        files = self.get_published_files()
                        response = {"files": files}
                        client_socket.sendall(pickle.dumps(response))
                    elif request["type"] == "download_file":
                        username = request["username"]
                        files = self.get_published_files(username)
                        response = {"files": files}
                        client_socket.sendall(pickle.dumps(response))
                    elif request["type"] == "file_request":
                        username = request["username"]
                        filename = request["filename"]
                        file_content = self.get_file_content(username, filename)
                        if file_content is not None:
                            response = {"content": file_content}
                        else:
                            response = {"content": None}
                        client_socket.sendall(pickle.dumps(response))
                    elif request["type"] == "file_content":
                        username = request["username"]
                        filename = request["filename"]
                        content = request["content"]
                        self.save_file_content(username, filename, content)
                        files = self.get_published_files(username)  # Actualizare lista de fișiere publicate
                        response = {"files": files}
                        client_socket.sendall(pickle.dumps(response))
                    elif request["type"] == "disconnect":
                        client_socket.close()
                        break
            except:
                break

    def save_file_content(self, username, filename, content):
        with self.lock:
            if username in self.published_files:
                self.published_files[username].append(filename)
            else:
                self.published_files[username] = [filename]
            with open(filename, "wb") as file:
                file.write(content)
            print(f"Fișierul {filename} a fost salvat în sistemul de fișiere.")
            self.notify_clients(username)

    def add_client(self, username, client_socket, files):
        with self.lock:
            self.clients[username] = {"socket": client_socket, "files": files}
            self.published_files[username] = files
            print(f"Nou client adăugat: {username}")
            self.notify_clients(username)

    def remove_client(self, username):
        with self.lock:
            del self.clients[username]
            del self.published_files[username]
            print(f"Client deconectat: {username}")
            self.notify_clients(username)

    def notify_clients(self, username):
        for client in self.clients.values():
            client_socket = client["socket"]
            files = self.published_files.get(client_socket.getpeername()[1], [])
            notification = {"type": "client_update", "username": username, "files": files}
            client_socket.sendall(pickle.dumps(notification))
        print(f"Notificare trimisă celorlalți clienți: {username} s-a {notification['type']}. Fișierele sale: {files}")

    def get_published_files(self, username=None):
        if username:
            files = self.published_files.get(username, [])
        else:
            files = []
            for client_files in self.published_files.values():
                files.extend(client_files)
        return files

    def get_file_content(self, requesting_username, filename):
        for client in self.clients.values():
            if filename in client["files"]:
                client_socket = client["socket"]
                request = {"type": "file_request", "filename": filename}
                client_socket.sendall(pickle.dumps(request))
                response = client_socket.recv(1024)
                if response:
                    file_content = pickle.loads(response)["content"]
                    return file_content
        return None

if __name__ == "__main__":
    server = Server("localhost", 8000)
    server.start()