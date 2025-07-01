#!/usr/bin/python
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

from __future__ import print_function

import sys
import os

from proton import Message, symbol
from proton.handlers import MessagingHandler
from proton.reactor import Container, SenderOption
from proton import SSLDomain, SSLException

class SecureSendHandler(MessagingHandler):
    def __init__(self, conn_url, address, message_body, auth_mode="ANONYMOUS"):
        super(SecureSendHandler, self).__init__()

        self.url = conn_url
        self.address = address
        self.auth_mode = auth_mode

        try:
            self.message_body = unicode(message_body)
        except NameError:
            self.message_body = message_body

    def on_start(self, event):
        try:
            print("SECURE-SEND: Starting SSL configuration...")

            # Configure SSL domain with client certificates
            ssl_domain = SSLDomain(SSLDomain.MODE_CLIENT)
            print("SECURE-SEND: Created SSL domain in CLIENT mode")

            # Set client credentials
            cert_file = './ssl/cert.pem'
            key_file = './ssl/key.pem'
            ca_file = './ssl/ca.pem'
            password = 'shalin'  # Change to 'solace123' if using new generated certificates

            print("SECURE-SEND: Setting SSL credentials...")
            print("  - Certificate: {0}".format(cert_file))
            print("  - Private key: {0}".format(key_file))
            print("  - CA file: {0}".format(ca_file))

            result = ssl_domain.set_credentials(cert_file=str(cert_file),
                                               key_file=str(key_file),
                                               password=str(password))
            print("SECURE-SEND: set_credentials() returned: {0}".format(result))

            result = ssl_domain.set_trusted_ca_db(certificate_db=str(ca_file))
            print("SECURE-SEND: set_trusted_ca_db() returned: {0}".format(result))

            # Use VERIFY_PEER for better Solace compatibility (less strict than VERIFY_PEER_NAME)
            result = ssl_domain.set_peer_authentication(SSLDomain.VERIFY_PEER)
            print("SECURE-SEND: set_peer_authentication(VERIFY_PEER) returned: {0}".format(result))

            self.container = event.container
            print("SECURE-SEND: Connecting to {0} with SSL and {1} auth...".format(self.url, self.auth_mode))

            # Try connection with specified authentication mechanism
            if self.auth_mode == "EXTERNAL":
                self.conn = event.container.connect(self.url, ssl_domain=ssl_domain, allowed_mechs="EXTERNAL")
            elif self.auth_mode == "PLAIN":
                # Use certificate CN as username for PLAIN authentication
                self.conn = event.container.connect(self.url, ssl_domain=ssl_domain,
                                                   user="jcsmp-client", password="",
                                                   allowed_mechs="PLAIN")
            elif self.auth_mode == "ANONYMOUS":
                self.conn = event.container.connect(self.url, ssl_domain=ssl_domain,
                                                   allowed_mechs="ANONYMOUS")
            else:
                # Auto-detect available mechanisms
                self.conn = event.container.connect(self.url, ssl_domain=ssl_domain)

            print("SECURE-SEND: Connection object created, creating sender...")

            self.sender = event.container.create_sender(self.conn, self.address, options=CapabilityOptions())
            print("SECURE-SEND: Sender created for address: {0}".format(self.address))

        except SSLException as e:
            print("SECURE-SEND: SSL Exception during setup: {0}".format(e))
            raise
        except Exception as e:
            print("SECURE-SEND: Unexpected error during setup: {0}".format(e))
            print("SECURE-SEND: Error type: {0}".format(type(e).__name__))
            raise

    def on_connection_opened(self, event):
        print("SECURE-SEND: SSL/TLS connection established to '{0}'".format(self.url))
        # Print SSL details if available
        if hasattr(event.connection, 'transport') and event.connection.transport:
            transport = event.connection.transport
            if hasattr(transport, 'ssl') and transport.ssl:
                ssl = transport.ssl()
                if ssl:
                    print("SECURE-SEND: SSL cipher: {0}".format(ssl.cipher_name()))
                    print("SECURE-SEND: SSL protocol: {0}".format(ssl.protocol_name()))

    def on_connection_init(self, event):
        print("SECURE-SEND: Connection initialization started")

    def on_connection_bound(self, event):
        print("SECURE-SEND: Connection bound to transport")

    def on_connection_unbound(self, event):
        print("SECURE-SEND: Connection unbound from transport")

    def on_link_opened(self, event):
        print("SECURE-SEND: Opened secure sender for target address '{0}'".format
              (event.sender.target.address))

    def on_sendable(self, event):
        message = Message(self.message_body)
        event.sender.send(message)

        print("SECURE-SEND: Sent message '{0}' over secure connection".format(message.body))

        event.sender.close()
        event.connection.close()

    def on_transport_error(self, event):
        print("SECURE-SEND: Transport error: {0}".format(event.transport.condition))
        print("SECURE-SEND: Transport error description: {0}".format(event.transport.condition.description if event.transport.condition else "No description"))
        if event.connection:
            event.connection.close()

    def on_connection_error(self, event):
        print("SECURE-SEND: Connection error: {0}".format(event.connection.condition))
        print("SECURE-SEND: Connection error description: {0}".format(event.connection.condition.description if event.connection.condition else "No description"))

    def on_session_error(self, event):
        print("SECURE-SEND: Session error: {0}".format(event.session.condition))

    def on_link_error(self, event):
        print("SECURE-SEND: Link error: {0}".format(event.link.condition))

    def on_disconnected(self, event):
        print("SECURE-SEND: Disconnected from broker")

    def on_transport_closed(self, event):
        print("SECURE-SEND: Transport closed")

class CapabilityOptions(SenderOption):
    def apply(self, sender):
        sender.target.capabilities.put_object(symbol("queue"))

def main():
    try:
        conn_url, address, message_body = sys.argv[1:4]
        auth_mode = sys.argv[4] if len(sys.argv) > 4 else "ANONYMOUS"
    except ValueError:
        print("Usage: secure-queue-send.py <connection-url> <address> <message-body> [auth-mode]")
        print("Auth modes: EXTERNAL, PLAIN, ANONYMOUS, AUTO")
        print("Default: ANONYMOUS (recommended for SSL/TLS encryption without client cert auth)")
        sys.exit(1)

    # Validate that SSL certificates exist
    ssl_files = ['./ssl/cert.pem', './ssl/key.pem', './ssl/ca.pem']
    for ssl_file in ssl_files:
        if not os.path.exists(ssl_file):
            print("ERROR: SSL certificate file not found: {0}".format(ssl_file))
            print("Please ensure all SSL certificate files are present in the ./ssl/ directory:")
            print("  - cert.pem (client certificate)")
            print("  - key.pem (private key)")
            print("  - ca.pem (trusted CA certificate)")
            sys.exit(1)

    print("SECURE-SEND: Using authentication mode: {0}".format(auth_mode))
    if auth_mode == "EXTERNAL":
        print("SECURE-SEND: WARNING - EXTERNAL auth requires broker support for client certificate authentication")

    handler = SecureSendHandler(conn_url, address, message_body, auth_mode)
    container = Container(handler)
    
    try:
        container.run()
    except Exception as e:
        print("SECURE-SEND: Error during execution: {0}".format(e))
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSECURE-SEND: Interrupted by user")
        pass
