
import grpc
from concurrent import futures
import chat_pb2
import chat_pb2_grpc

class BackupService(chat_pb2_grpc.BackupServiceServicer):
    def BackupHistory(self, request, context):
     
        with open("backup.txt", "a") as f:
           
            for sender, messages in request.messageHistory.items():
                f.write(f"{sender}: {', '.join(messages.values)}\n")
        return chat_pb2.AckResponse(ack="Backup successful")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_BackupServiceServicer_to_server(BackupService(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
