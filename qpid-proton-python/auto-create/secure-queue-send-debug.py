#!/usr/bin/python
#
# Enhanced SSL debugging version of secure queue sender
#

from __future__ import print_function

import sys
import os

from proton import Message, symbol
from proton.handlers import MessagingHandler
from proton.reactor import Container, SenderOption
from proton import SSLDomain, SSLException

class DebugSecureSendHandler(MessagingHandler):
    def __init__(self, conn_url, address, message_body, auth_mode="EXTERNAL"):
        super(DebugSecureSendHandler, self).__init__()

        self.url = conn_url
        self.address = address
        self.auth_mode = auth_mode

        try:
            self.message_body = unicode(message_body)
        except NameError:
            self.message_body = message_body

    def on_start(self, event):
        try:
            print("DEBUG-SEND: Starting SSL configuration...")
            
            # Configure SSL domain with client certificates
            ssl_domain = SSLDomain(SSLDomain.MODE_CLIENT)
            print("DEBUG-SEND: Created SSL domain in CLIENT mode")
            
            # Set client credentials
            cert_file = './ssl/cert.pem'
            key_file = './ssl/key.pem'
            ca_file = './ssl/ca.pem'
            password = 'shalin'
            
            print("DEBUG-SEND: Setting SSL credentials...")
            print("  - Certificate: {0}".format(cert_file))
            print("  - Private key: {0}".format(key_file))
            print("  - CA file: {0}".format(ca_file))
            
            result = ssl_domain.set_credentials(cert_file=str(cert_file),
                                               key_file=str(key_file),
                                               password=str(password))
            print("DEBUG-SEND: set_credentials() returned: {0}".format(result))
            
            result = ssl_domain.set_trusted_ca_db(certificate_db=str(ca_file))
            print("DEBUG-SEND: set_trusted_ca_db() returned: {0}".format(result))
            
            # Try with less strict peer verification first
            result = ssl_domain.set_peer_authentication(SSLDomain.VERIFY_PEER)
            print("DEBUG-SEND: set_peer_authentication(VERIFY_PEER) returned: {0}".format(result))

            self.container = event.container
            print("DEBUG-SEND: Connecting to {0} with SSL and {1} auth...".format(self.url, self.auth_mode))
            
            # Try different authentication approaches
            if self.auth_mode == "EXTERNAL":
                self.conn = event.container.connect(self.url, ssl_domain=ssl_domain, allowed_mechs="EXTERNAL")
            elif self.auth_mode == "PLAIN":
                # Extract CN from certificate for username
                self.conn = event.container.connect(self.url, ssl_domain=ssl_domain, 
                                                   user="jcsmp-client", password="", 
                                                   allowed_mechs="PLAIN")
            elif self.auth_mode == "ANONYMOUS":
                self.conn = event.container.connect(self.url, ssl_domain=ssl_domain, 
                                                   allowed_mechs="ANONYMOUS")
            else:
                # Try without specifying allowed_mechs
                self.conn = event.container.connect(self.url, ssl_domain=ssl_domain)
            
            print("DEBUG-SEND: Connection object created, creating sender...")
            
            self.sender = event.container.create_sender(self.conn, self.address, options=CapabilityOptions())
            print("DEBUG-SEND: Sender created for address: {0}".format(self.address))
            
        except SSLException as e:
            print("DEBUG-SEND: SSL Exception during setup: {0}".format(e))
            raise
        except Exception as e:
            print("DEBUG-SEND: Unexpected error during setup: {0}".format(e))
            print("DEBUG-SEND: Error type: {0}".format(type(e).__name__))
            raise

    def on_connection_opened(self, event):
        print("DEBUG-SEND: SSL/TLS connection established to '{0}'".format(self.url))
        # Print SSL details if available
        if hasattr(event.connection, 'transport') and event.connection.transport:
            transport = event.connection.transport
            if hasattr(transport, 'ssl') and transport.ssl:
                ssl = transport.ssl()
                if ssl:
                    print("DEBUG-SEND: SSL cipher: {0}".format(ssl.cipher_name()))
                    print("DEBUG-SEND: SSL protocol: {0}".format(ssl.protocol_name()))

    def on_connection_init(self, event):
        print("DEBUG-SEND: Connection initialization started")

    def on_connection_bound(self, event):
        print("DEBUG-SEND: Connection bound to transport")

    def on_link_opened(self, event):
        print("DEBUG-SEND: Opened secure sender for target address '{0}'".format
              (event.sender.target.address))

    def on_sendable(self, event):
        message = Message(self.message_body)
        event.sender.send(message)

        print("DEBUG-SEND: Sent message '{0}' over secure connection".format(message.body))

        event.sender.close()
        event.connection.close()

    def on_transport_error(self, event):
        print("DEBUG-SEND: Transport error: {0}".format(event.transport.condition))
        print("DEBUG-SEND: Transport error description: {0}".format(
            event.transport.condition.description if event.transport.condition else "No description"))
        if event.connection:
            event.connection.close()

    def on_connection_error(self, event):
        print("DEBUG-SEND: Connection error: {0}".format(event.connection.condition))
        print("DEBUG-SEND: Connection error description: {0}".format(
            event.connection.condition.description if event.connection.condition else "No description"))

    def on_session_error(self, event):
        print("DEBUG-SEND: Session error: {0}".format(event.session.condition))

    def on_link_error(self, event):
        print("DEBUG-SEND: Link error: {0}".format(event.link.condition))

    def on_disconnected(self, event):
        print("DEBUG-SEND: Disconnected from broker")

    def on_transport_closed(self, event):
        print("DEBUG-SEND: Transport closed")

class CapabilityOptions(SenderOption):
    def apply(self, sender):
        sender.target.capabilities.put_object(symbol("queue"))

def main():
    try:
        conn_url, address, message_body = sys.argv[1:4]
        auth_mode = sys.argv[4] if len(sys.argv) > 4 else "EXTERNAL"
    except ValueError:
        print("Usage: secure-queue-send-debug.py <connection-url> <address> <message-body> [auth-mode]")
        print("Auth modes: EXTERNAL, PLAIN, ANONYMOUS, AUTO")
        sys.exit(1)

    # Validate that SSL certificates exist
    ssl_files = ['./ssl/cert.pem', './ssl/key.pem', './ssl/ca.pem']
    for ssl_file in ssl_files:
        if not os.path.exists(ssl_file):
            print("ERROR: SSL certificate file not found: {0}".format(ssl_file))
            sys.exit(1)

    print("DEBUG-SEND: Using authentication mode: {0}".format(auth_mode))
    
    handler = DebugSecureSendHandler(conn_url, address, message_body, auth_mode)
    container = Container(handler)
    
    try:
        container.run()
    except Exception as e:
        print("DEBUG-SEND: Error during execution: {0}".format(e))
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nDEBUG-SEND: Interrupted by user")
        pass
