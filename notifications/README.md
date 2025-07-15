## Notifications
The backend handler for notifications is a simple HTTP server that listens for incoming notifications from the RabbitMQ server. It is designed to be lightweight and efficient, allowing for quick processing of notifications without the need for complex setup or configuration.

### What you want to notify
- New messages -> notify recipient user
- New items in category -> notify subscribers/interested users


