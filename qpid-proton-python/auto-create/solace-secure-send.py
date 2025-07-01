#!/usr/bin/python
#
# Solace PubSub+ optimized secure queue sender with SSL/TLS client certificate authentication
#

from __future__ import print_function

import sys
import os

from proton import Message, symbol
from proton.handlers import MessagingHandler
from proton.reactor import Container, SenderOption
from proton import SSLDomain, SSLException

class SolaceSecureSendHandler(MessagingHandler):
    def __init__(self, conn_url, address, message_body, auth_mode="EXTERNAL"):
        super(SolaceSecureSendHandler, self).__init__()

        self.url = conn_url
        self.address = address
        self.auth_mode = auth_mode

        try:
            self.message_body = unicode(message_body)
        except NameError:
            self.message_body = message_body

    def on_start(self, event):
        try:
            print("SOLACE-SEND: Starting Solace-optimized SSL configuration...")
            
            # Configure SSL domain with Solace-specific settings
            ssl_domain = SSLDomain(SSLDomain.MODE_CLIENT)
            print("SOLACE-SEND: Created SSL domain in CLIENT mode")
            
            # Set client credentials
            cert_file = './ssl/cert.pem'
            key_file = './ssl/key.pem'
            ca_file = './ssl/ca.pem'
            password = 'shalin'
            
            print("SOLACE-SEND: Setting SSL credentials for Solace...")
            print("  - Certificate: {0}".format(cert_file))
            print("  - Private key: {0}".format(key_file))
            print("  - CA file: {0}".format(ca_file))
            
            result = ssl_domain.set_credentials(cert_file=str(cert_file),
                                               key_file=str(key_file),
                                               password=str(password))
            print("SOLACE-SEND: set_credentials() returned: {0}".format(result))
            
            result = ssl_domain.set_trusted_ca_db(certificate_db=str(ca_file))
            print("SOLACE-SEND: set_trusted_ca_db() returned: {0}".format(result))
            
            # Use VERIFY_PEER for Solace (less strict than VERIFY_PEER_NAME)
            result = ssl_domain.set_peer_authentication(SSLDomain.VERIFY_PEER)
            print("SOLACE-SEND: set_peer_authentication(VERIFY_PEER) returned: {0}".format(result))

            self.container = event.container
            print("SOLACE-SEND: Connecting to Solace broker at {0} with {1} auth...".format(self.url, self.auth_mode))
            
            # Solace-specific connection properties
            connection_properties = {
                'product': 'qpid-proton-python',
                'version': '1.0',
                'platform': 'Python'
            }
            
            # Try connection with specified authentication mechanism
            if self.auth_mode == "EXTERNAL":
                self.conn = event.container.connect(
                    self.url, 
                    ssl_domain=ssl_domain, 
                    allowed_mechs="EXTERNAL",
                    properties=connection_properties
                )
            elif self.auth_mode == "PLAIN":
                # Use certificate CN as username for PLAIN authentication
                self.conn = event.container.connect(
                    self.url, 
                    ssl_domain=ssl_domain, 
                    user="jcsmp-client", 
                    password="", 
                    allowed_mechs="PLAIN",
                    properties=connection_properties
                )
            elif self.auth_mode == "ANONYMOUS":
                self.conn = event.container.connect(
                    self.url, 
                    ssl_domain=ssl_domain, 
                    allowed_mechs="ANONYMOUS",
                    properties=connection_properties
                )
            else:
                # Auto-detect available mechanisms
                self.conn = event.container.connect(
                    self.url, 
                    ssl_domain=ssl_domain,
                    properties=connection_properties
                )
            
            print("SOLACE-SEND: Connection object created, creating sender...")
            
            self.sender = event.container.create_sender(self.conn, self.address, options=SolaceCapabilityOptions())
            print("SOLACE-SEND: Sender created for address: {0}".format(self.address))
            
        except SSLException as e:
            print("SOLACE-SEND: SSL Exception during setup: {0}".format(e))
            raise
        except Exception as e:
            print("SOLACE-SEND: Unexpected error during setup: {0}".format(e))
            print("SOLACE-SEND: Error type: {0}".format(type(e).__name__))
            raise

    def on_connection_opened(self, event):
        print("SOLACE-SEND: SSL/TLS connection established to Solace broker '{0}'".format(self.url))
        # Print SSL details if available
        if hasattr(event.connection, 'transport') and event.connection.transport:
            transport = event.connection.transport
            if hasattr(transport, 'ssl') and transport.ssl:
                ssl = transport.ssl()
                if ssl:
                    print("SOLACE-SEND: SSL cipher: {0}".format(ssl.cipher_name()))
                    print("SOLACE-SEND: SSL protocol: {0}".format(ssl.protocol_name()))

    def on_connection_init(self, event):
        print("SOLACE-SEND: Connection initialization started")

    def on_connection_bound(self, event):
        print("SOLACE-SEND: Connection bound to transport")

    def on_link_opened(self, event):
        print("SOLACE-SEND: Opened secure sender for Solace queue '{0}'".format
              (event.sender.target.address))

    def on_sendable(self, event):
        # Create message with Solace-friendly properties
        message = Message(self.message_body)
        message.properties = {
            'sender': 'qpid-proton-python',
            'timestamp': str(event.container.now())
        }
        
        event.sender.send(message)
        print("SOLACE-SEND: Sent message '{0}' to Solace broker over secure connection".format(message.body))

        event.sender.close()
        event.connection.close()

    def on_transport_error(self, event):
        print("SOLACE-SEND: Transport error: {0}".format(event.transport.condition))
        print("SOLACE-SEND: Transport error description: {0}".format(
            event.transport.condition.description if event.transport.condition else "No description"))
        print("SOLACE-SEND: This may indicate Solace broker SSL configuration issues")
        if event.connection:
            event.connection.close()

    def on_connection_error(self, event):
        print("SOLACE-SEND: Connection error: {0}".format(event.connection.condition))
        print("SOLACE-SEND: Connection error description: {0}".format(
            event.connection.condition.description if event.connection.condition else "No description"))

    def on_session_error(self, event):
        print("SOLACE-SEND: Session error: {0}".format(event.session.condition))

    def on_link_error(self, event):
        print("SOLACE-SEND: Link error: {0}".format(event.link.condition))

    def on_disconnected(self, event):
        print("SOLACE-SEND: Disconnected from Solace broker")

    def on_transport_closed(self, event):
        print("SOLACE-SEND: Transport closed")

class SolaceCapabilityOptions(SenderOption):
    def apply(self, sender):
        # Solace-specific queue capabilities
        sender.target.capabilities.put_object(symbol("queue"))
        sender.target.capabilities.put_object(symbol("topic"))

def main():
    try:
        conn_url, address, message_body = sys.argv[1:4]
        auth_mode = sys.argv[4] if len(sys.argv) > 4 else "EXTERNAL"
    except ValueError:
        print("Usage: solace-secure-send.py <connection-url> <address> <message-body> [auth-mode]")
        print("Auth modes: EXTERNAL, PLAIN, ANONYMOUS, AUTO")
        print("Default: EXTERNAL (for Solace client certificate authentication)")
        print("\nExample:")
        print("  python solace-secure-send.py amqps://localhost:5671 my.queue 'Hello Solace!' EXTERNAL")
        sys.exit(1)

    # Validate that SSL certificates exist
    ssl_files = ['./ssl/cert.pem', './ssl/key.pem', './ssl/ca.pem']
    for ssl_file in ssl_files:
        if not os.path.exists(ssl_file):
            print("ERROR: SSL certificate file not found: {0}".format(ssl_file))
            print("Please ensure all SSL certificate files are present in the ./ssl/ directory")
            print("See SOLACE-SSL-SETUP.md for certificate configuration instructions")
            sys.exit(1)

    print("SOLACE-SEND: Using authentication mode: {0}".format(auth_mode))
    if auth_mode == "EXTERNAL":
        print("SOLACE-SEND: Ensure Solace broker is configured for client certificate authentication")
        print("SOLACE-SEND: See SOLACE-SSL-SETUP.md for broker configuration steps")
    
    handler = SolaceSecureSendHandler(conn_url, address, message_body, auth_mode)
    container = Container(handler)
    
    try:
        container.run()
    except Exception as e:
        print("SOLACE-SEND: Error during execution: {0}".format(e))
        print("SOLACE-SEND: Check Solace broker logs and SSL configuration")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSOLACE-SEND: Interrupted by user")
        pass
