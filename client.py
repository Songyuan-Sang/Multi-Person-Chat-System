import grpc
import chat_pb2
import chat_pb2_grpc
import threading
from google.protobuf.empty_pb2 import Empty
import sys
import signal

message_history = {}
exit_requested = False


def send_history(stub):
    history_request = chat_pb2.SendHistoryRequest()
    for user, messages in message_history.items():
        history_request.messageHistory[user].values.extend(messages)
    
    response = stub.SendHistory(history_request)
    print(response.ack)
    


def log_operation(filename, user, message):
    if user in message_history:
        message_history[user].append(message)
    else:
        message_history[user] = [message]
    with open(filename, 'a') as log_file:
        log_file.write(f"{user}: {message}\n")




def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    sys.exit(0)



def listen_for_messages(stub, name):
    global exit_requested
    request = chat_pb2.StreamRequest(sender=name)
    try:
        for message in stub.ChatStream(request):
            print(f"{message.sender}: {message.message}")
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.UNAVAILABLE:
            print("Server is currently unavailable. Please try connecting again later.")
            exit_requested = True
        else:
            print(f"An RPC error occurred: {e.details()}")



def run():
    global exit_requested
    signal.signal(signal.SIGINT, signal_handler)
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = chat_pb2_grpc.ChatServiceStub(channel)
        
        auth_status = "NAK"
        while auth_status == "NAK":
            username = input("Enter your username: ")
            password = input("Enter your password: ")

            if username == "":
                print("username cannot be empty.")
                continue
            if len(password) < 6 or password == "":
                print("Password must be at least six characters and cannot be empty.")
                continue

            response = stub.Authenticate(chat_pb2.AuthRequest(username=username, password=password))
            print(response.message)
            if response.message == "Registration successful. Please login again with your new credentials.":
                password = input("Enter your password: ")
                response = stub.Authenticate(chat_pb2.AuthRequest(username=username, password=password))
                print(response.message)
            auth_status = response.status
            if response.message == "User already logged in.":
                auth_status == "NAK"

        
        if auth_status == "ACK":
            join_response = stub.JoinChat(chat_pb2.JoinRequest(sender=username))
            print(join_response.message)

            show_history = input("Do you want to see the message history? (yes/no): ")
            if show_history.lower() == "yes":          
                history = stub.GetHistory(chat_pb2.HistoryRequest(sender=username))
                for message in history.messages:
                    print(f"{message.sender}: {message.message}")
            
            print('\n ---Type "list" to see active users\n ---"check" to see active users\n ---"backup" to backup chat history\n ---"exit" to leave the chat')

            listener_thread = threading.Thread(target=listen_for_messages, args=(stub, username), daemon=True)
            listener_thread.start()

        while True:
            if exit_requested:
                sys.exit(0)
            message = input()
            if message == 'exit' or exit_requested:
                sys.exit(0)
            elif message == 'check':
                response = stub.CheckUsers(chat_pb2.CheckUsersRequest(sender=username))
                print(f"Number of active users: {response.userCount}")
            elif message == 'list':
                response = stub.ListActiveUsers(chat_pb2.ListActiveUsersRequest())
                print("Active users:")
                for username in response.usernames:
                    print(username)
            elif message == 'backup':
                send_history(stub)
            stub.SendMessage(chat_pb2.ChatMessage(sender=username, message=message))
            log_operation("client.txt", username, message)
            
            
            

if __name__ == '__main__':
    run()
