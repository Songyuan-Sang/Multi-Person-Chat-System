import time
from concurrent import futures
import grpc
import chat_pb2
import chat_pb2_grpc
from google.protobuf.empty_pb2 import Empty
import threading
import signal


def handle_shutdown_signal(server, signum, frame):
    print("Shutting down server...")
    # Broadcast "server down" message
    shutdown_message = chat_pb2.ChatMessage(sender="Server", message="Server is shutting down.")
    service = ChatService()
    service.broadcast_message(shutdown_message)
    # Stop the server after sending the message
    server.stop(0)


class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.clients = {}
        self.user_passwords = {}
        self.message_history = []



    def SendHistory(self, request, context):
        with open('server.txt', 'a') as file:
            for user, string_list in request.messageHistory.items():
                for message in string_list.values:
                    file.write(f"{user}: {message}\n")
        channel = grpc.insecure_channel('localhost:50052')
        backup_stub = chat_pb2_grpc.BackupServiceStub(channel)
        backup_stub.BackupHistory(request)
        return chat_pb2.AckResponse(ack="History saved successfully.")
    



    def broadcast_message(self, message):
        for client in self.clients:
            self.clients[client].messages.append(message)
        self.message_history.append(message)



    def JoinChat(self, request, context):
        if request.sender in self.clients:
            return chat_pb2.JoinResponse(status=f"NAK", message=f"User Name Exists Already\n")
        self.clients[request.sender] = Client()
        join_message = chat_pb2.ChatMessage(sender="Server", message=f"User {request.sender} has joined the chat.")
        self.broadcast_message(join_message)
        return chat_pb2.JoinResponse(status=f"ACK", message=f"Welcome, {request.sender}.\nYou can start sending messages. Type 'exit' to quit.\n")
        



    def SendMessage(self, request, context):
        message = chat_pb2.ChatMessage(sender=request.sender, message=request.message)
        self.broadcast_message(message)
        return Empty()



    def ChatStream(self, request, context):
        client_id = request.sender
        try:
            while context.is_active():
                # Assuming clients[client_id] holds messages for the client
                if client_id in self.clients and len(self.clients[client_id].messages) > 0:
                    message = self.clients[client_id].messages.pop(0)
                    yield message
                else:
                    # If there are no messages, wait a bit before checking again to avoid busy waiting
                    time.sleep(0.01)
        finally:
            # Broadcast a message when a user leaves
            leave_message = chat_pb2.ChatMessage(sender="Server", message=f"User {client_id} has left the chat.")
            self.broadcast_message(leave_message)
            del self.clients[client_id]



    def CheckUsers(self, request, context):
        user_count = len(self.clients)  # Count the number of active users
        return chat_pb2.CheckUsersResponse(userCount=user_count)
    

    def ListActiveUsers(self, request, context):
        usernames = [username for username in self.clients.keys()]
        return chat_pb2.ListActiveUsersResponse(usernames=usernames)



    def Authenticate(self, request, context):
        if request.username in self.user_passwords:
            if self.user_passwords[request.username] == request.password:
                if request.username in self.clients:
                    return chat_pb2.AuthResponse(status="NAK", message="User already logged in.")
                else:
                    return chat_pb2.AuthResponse(status="ACK", message="Login successful.")
            else:
                return chat_pb2.AuthResponse(status="NAK", message="Invalid password.")
        else:
            self.user_passwords[request.username] = request.password
            return chat_pb2.AuthResponse(status="ACK", message="Registration successful. Please login again with your new credentials.")
    


    def GetHistory(self, request, context):
        self.message_history = [message for message in self.message_history if "has joined the chat." not in message.message]
        return chat_pb2.HistoryResponse(messages=self.message_history)



class Client:
    def __init__(self):
        self.messages = []



def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port('[::]:50051')
    
    # Register signal handler
    signal.signal(signal.SIGINT, lambda signum, frame: handle_shutdown_signal(server, signum, frame))

    server.start()
    print("Starting server. Listening on port 50051.")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Server stopped manually.")


    
if __name__ == '__main__':
    serve()
