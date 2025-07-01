#!/bin/bash
#
# Generate SSL certificates optimized for Solace PubSub+ broker
#

set -e

CERT_DIR="ssl"
BACKUP_DIR="ssl-backup-$(date +%Y%m%d-%H%M%S)"

echo "=== Solace SSL Certificate Generation ==="

# Create backup of existing certificates
if [ -d "$CERT_DIR" ]; then
    echo "Backing up existing certificates to $BACKUP_DIR..."
    cp -r "$CERT_DIR" "$BACKUP_DIR"
fi

# Create certificate directory
mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

echo "Generating Solace-compatible SSL certificates..."

# 1. Generate CA private key
echo "1. Generating CA private key..."
openssl genrsa -out solace-ca-key.pem 4096

# 2. Create CA certificate configuration
echo "2. Creating CA certificate configuration..."
cat > ca-config.conf << EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_ca
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Jose
O = Solace Systems
OU = Certificate Authority
CN = Solace Root CA

[v3_ca]
basicConstraints = critical,CA:TRUE,pathlen:0
keyUsage = critical,keyCertSign,cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer:always
EOF

# 3. Generate CA certificate
echo "3. Generating CA certificate..."
openssl req -new -x509 -days 3650 -key solace-ca-key.pem \
    -out solace-ca.pem -config ca-config.conf -extensions v3_ca

# 4. Generate server private key (for broker)
echo "4. Generating server private key..."
openssl genrsa -out solace-server-key.pem 2048

# 5. Create server certificate configuration
echo "5. Creating server certificate configuration..."
cat > server-config.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Jose
O = Solace Systems
OU = Servers
CN = localhost

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation,digitalSignature,keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = solace-broker
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

# 6. Generate server certificate signing request
echo "6. Generating server certificate signing request..."
openssl req -new -key solace-server-key.pem \
    -out solace-server.csr -config server-config.conf

# 7. Sign server certificate
echo "7. Signing server certificate..."
openssl x509 -req -in solace-server.csr \
    -CA solace-ca.pem -CAkey solace-ca-key.pem \
    -CAcreateserial -out solace-server.pem \
    -days 365 -extensions v3_req -extfile server-config.conf

# 8. Generate client private key
echo "8. Generating client private key..."
openssl genrsa -out solace-client-key.pem 2048

# 9. Create client certificate configuration
echo "9. Creating client certificate configuration..."
cat > client-config.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Jose
O = Solace Systems
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

# 10. Generate client certificate signing request
echo "10. Generating client certificate signing request..."
openssl req -new -key solace-client-key.pem \
    -out solace-client.csr -config client-config.conf

# 11. Sign client certificate
echo "11. Signing client certificate..."
openssl x509 -req -in solace-client.csr \
    -CA solace-ca.pem -CAkey solace-ca-key.pem \
    -CAcreateserial -out solace-client.pem \
    -days 365 -extensions v3_req -extfile client-config.conf

# 12. Create password-protected client key (for compatibility)
echo "12. Creating password-protected client key..."
openssl rsa -in solace-client-key.pem -out solace-client-key-protected.pem \
    -aes256 -passout pass:solace123

# 13. Create certificate bundles
echo "13. Creating certificate bundles..."
cat solace-client.pem solace-ca.pem > solace-client-bundle.pem
cat solace-server.pem solace-ca.pem > solace-server-bundle.pem

# 14. Create symbolic links for compatibility with existing scripts
echo "14. Creating compatibility links..."
ln -sf solace-ca.pem ca.pem
ln -sf solace-client.pem cert.pem
ln -sf solace-client-key-protected.pem key.pem

# 15. Clean up temporary files
echo "15. Cleaning up temporary files..."
rm -f *.csr *.conf *.srl

# 16. Set appropriate permissions
echo "16. Setting file permissions..."
chmod 600 *-key*.pem
chmod 644 *.pem

cd ..

echo ""
echo "=== Certificate Generation Complete ==="
echo ""
echo "Generated files in $CERT_DIR/:"
echo "  - solace-ca.pem (Root CA certificate)"
echo "  - solace-ca-key.pem (Root CA private key)"
echo "  - solace-server.pem (Server certificate for broker)"
echo "  - solace-server-key.pem (Server private key for broker)"
echo "  - solace-client.pem (Client certificate)"
echo "  - solace-client-key.pem (Client private key - no password)"
echo "  - solace-client-key-protected.pem (Client private key - password: solace123)"
echo "  - solace-client-bundle.pem (Client cert + CA bundle)"
echo "  - solace-server-bundle.pem (Server cert + CA bundle)"
echo ""
echo "Compatibility links (for existing scripts):"
echo "  - ca.pem -> solace-ca.pem"
echo "  - cert.pem -> solace-client.pem"
echo "  - key.pem -> solace-client-key-protected.pem (password: solace123)"
echo ""
echo "Next steps:"
echo "1. Upload solace-ca.pem to Solace broker as trusted CA"
echo "2. Configure Solace server with solace-server.pem and solace-server-key.pem"
echo "3. Update client scripts to use password 'solace123' for the private key"
echo "4. Test connection with: python solace-secure-send.py amqps://localhost:5671 my.queue 'Test' EXTERNAL"
echo ""

# Verify certificates
echo "=== Certificate Verification ==="
echo "Verifying certificate chain..."
if openssl verify -CAfile "$CERT_DIR/solace-ca.pem" "$CERT_DIR/solace-client.pem"; then
    echo "✅ Client certificate chain is valid"
else
    echo "❌ Client certificate chain verification failed"
fi

if openssl verify -CAfile "$CERT_DIR/solace-ca.pem" "$CERT_DIR/solace-server.pem"; then
    echo "✅ Server certificate chain is valid"
else
    echo "❌ Server certificate chain verification failed"
fi

echo ""
echo "Certificate details:"
echo "CA Subject: $(openssl x509 -in "$CERT_DIR/solace-ca.pem" -subject -noout)"
echo "Client Subject: $(openssl x509 -in "$CERT_DIR/solace-client.pem" -subject -noout)"
echo "Server Subject: $(openssl x509 -in "$CERT_DIR/solace-server.pem" -subject -noout)"
echo ""
echo "Certificate generation completed successfully!"
