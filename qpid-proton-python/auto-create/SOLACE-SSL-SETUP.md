# Solace PubSub+ SSL/TLS Client Certificate Authentication Setup

## Problem Analysis

Your Solace PubSub+ broker is rejecting the SSL connection due to:
1. **Self-signed certificate in chain**: Solace requires proper certificate chain validation
2. **Untrusted Certificate**: The broker doesn't have your custom CA in its trust store

## Solution Overview

We need to:
1. Configure Solace to trust your custom CA certificate
2. Ensure proper certificate chain structure
3. Configure client certificate authentication
4. Update the client code for Solace-specific requirements

## Step 1: Solace Broker Configuration

### 1.1 Upload CA Certificate to Solace

```bash
# Connect to Solace CLI (replace with your broker details)
ssh admin@<solace-broker-ip>

# Enter configuration mode
configure

# Create a certificate authority
create certificate-authority "CustomCA"
certificate pem
# Paste the contents of your ca.pem file here
exit

# Apply the configuration
commit
```

### 1.2 Configure SSL Server Certificate

```bash
# Create server certificate (if not already configured)
create server-certificate "BrokerServerCert"
certificate pem
# Paste your broker's server certificate here
private-key pem
# Paste your broker's private key here
exit

# Configure the SSL service
ssl
server-certificate "BrokerServerCert"
exit
```

### 1.3 Enable Client Certificate Authentication

```bash
# Configure the message VPN for client certificate authentication
message-vpn "default"
authentication
client-certificate
certificate-authority "CustomCA"
validate-certificate-date
no shutdown
exit
exit

# Configure the SSL listen port
service msg-backbone
ssl
listen-port 5671 ssl
exit
exit

# Apply configuration
commit
```

## Step 2: Alternative Certificate Generation (If Needed)

If your current certificates don't work, generate a new set:

### 2.1 Create Enhanced CA Certificate

```bash
# Create CA private key
openssl genrsa -out ssl/enhanced-ca-key.pem 4096

# Create CA certificate with proper extensions
cat > ssl/ca-config.conf << EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_ca
prompt = no

[req_distinguished_name]
C = US
ST = State
L = City
O = Organization
OU = Certificate Authority
CN = Enhanced Root CA

[v3_ca]
basicConstraints = critical,CA:TRUE
keyUsage = critical,keyCertSign,cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer:always
EOF

openssl req -new -x509 -days 3650 -key ssl/enhanced-ca-key.pem \
    -out ssl/enhanced-ca.pem -config ssl/ca-config.conf -extensions v3_ca
```

### 2.2 Create Client Certificate

```bash
# Create client private key
openssl genrsa -out ssl/enhanced-client-key.pem 2048

# Create client certificate signing request
cat > ssl/client-config.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = State
L = City
O = Organization
OU = Clients
CN = solace-client

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation,digitalSignature,keyEncipherment
extendedKeyUsage = clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = solace-client
DNS.2 = localhost
EOF

openssl req -new -key ssl/enhanced-client-key.pem \
    -out ssl/enhanced-client.csr -config ssl/client-config.conf

# Sign the client certificate
openssl x509 -req -in ssl/enhanced-client.csr \
    -CA ssl/enhanced-ca.pem -CAkey ssl/enhanced-ca-key.pem \
    -CAcreateserial -out ssl/enhanced-client.pem \
    -days 365 -extensions v3_req -extfile ssl/client-config.conf

# Clean up
rm ssl/enhanced-client.csr
```

## Step 3: Solace-Specific Client Configuration

### 3.1 Update SSL Configuration for Solace

Solace requires specific SSL settings. Update your script:

```python
def on_start(self, event):
    try:
        ssl_domain = SSLDomain(SSLDomain.MODE_CLIENT)

        # Solace-specific SSL configuration
        ssl_domain.set_credentials(cert_file=str('./ssl/cert.pem'),
                                   key_file=str('./ssl/key.pem'),
                                   password=str('shalin'))
        ssl_domain.set_trusted_ca_db(certificate_db=str('./ssl/ca.pem'))

        # Use VERIFY_PEER instead of VERIFY_PEER_NAME for Solace
        ssl_domain.set_peer_authentication(SSLDomain.VERIFY_PEER)

        # Solace connection with specific options
        self.conn = event.container.connect(
            self.url,
            ssl_domain=ssl_domain,
            allowed_mechs="EXTERNAL",
            # Add Solace-specific properties
            properties={
                'product': 'qpid-proton-python',
                'version': '1.0'
            }
        )
```

### 3.2 Verification Commands

```bash
# Verify certificate chain
openssl verify -CAfile ./ssl/ca.pem ./ssl/cert.pem

# Check certificate details for Solace compatibility
openssl x509 -in ./ssl/cert.pem -text -noout | grep -E "(Subject|Issuer|Extended Key Usage)"

# Test SSL connection to Solace
openssl s_client -connect localhost:5671 -cert ./ssl/cert.pem -key ./ssl/key.pem -CAfile ./ssl/ca.pem

# Check certificate fingerprint (useful for Solace logs)
openssl x509 -in ./ssl/cert.pem -fingerprint -sha256 -noout
```

## Step 4: Solace CLI Configuration Commands

### 4.1 Complete Solace Configuration Script

```bash
#!/bin/bash
# Save as configure-solace-ssl.sh

# Connect to Solace and configure SSL
solace_cli_commands="
configure
create certificate-authority CustomCA
certificate pem
$(cat ssl/ca.pem)
exit

message-vpn default
authentication
client-certificate
certificate-authority CustomCA
validate-certificate-date
no shutdown
exit
exit

service msg-backbone
ssl
listen-port 5671 ssl
exit
exit

commit
"

echo "$solace_cli_commands" | ssh admin@localhost
```

### 4.2 Verify Solace Configuration

```bash
# Check SSL service status
show service
show ssl
show certificate-authority
show message-vpn default authentication client-certificate
```

## Step 5: Troubleshooting

### 5.1 Common Issues and Solutions

**Issue**: "self-signed certificate in certificate chain"
**Solution**: Ensure CA certificate is properly uploaded to Solace trust store

**Issue**: "Untrusted Certificate"
**Solution**: Verify certificate-authority is configured and enabled in message-vpn

**Issue**: "Certificate validation failed"
**Solution**: Check certificate dates and ensure proper certificate chain

### 5.2 Debug Commands

```bash
# Enable SSL debugging in Solace
configure
logging
event ssl info
exit
commit

# Monitor SSL events
show log events level info | include SSL
```

## Step 6: Testing the Solution

```bash
# Test with enhanced certificates (if generated)
python secure-queue-send.py amqps://localhost:5671 my.queue "Test message" EXTERNAL

# Test with original certificates after Solace configuration
python secure-queue-send.py amqps://localhost:5671 my.queue "Test message" EXTERNAL
```
