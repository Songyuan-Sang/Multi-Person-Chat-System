# Multi-Person-Chat-System

The goal of this project is to create a simple chat system that allows multiple users to communicate in real-time. The system should support user authentication, joining the chat, sending messages, viewing message history, checking active users, and backing up chat history. We aim to build a scalable, efficient, and reliable system using gRPC and Python. 

A chat system consisting of the following components was built: 

- ChatService (Server): Manages user authentication, chat operations, and message broadcasting. 

- Client: Interacts with the server to send/receive messages and perform other actions. 

- BackupService: Responsible for storing backups of the chat history. 
