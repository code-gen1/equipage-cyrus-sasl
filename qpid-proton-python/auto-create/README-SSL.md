# Secure Queue Send with SSL/TLS Authentication

This directory contains `secure-queue-send.py`, a secure version of the original `queue-send.py` that implements SSL/TLS authentication using client certificates.

## Features

- **SSL/TLS Encryption**: All communication is encrypted using SSL/TLS
- **Client Certificate Authentication**: Uses client certificates for authentication with the AMQP broker
- **Peer Verification**: Verifies the broker's certificate and hostname
- **Enhanced Error Handling**: Provides detailed error messages for SSL/TLS related issues
- **Certificate Validation**: Checks for the presence of required SSL certificate files before attempting connection

## Requirements

### SSL Certificate Files

The following SSL certificate files must be present in the `./ssl/` directory relative to the script:

- `cert.pem` - Client certificate file (PEM format)
- `key.pem` - Private key file (PEM format) 
- `ca.pem` - Trusted Certificate Authority (CA) certificate file (PEM format)

### Directory Structure
```
qpid-proton-python/auto-create/
├── secure-queue-send.py
├── ssl/
│   ├── cert.pem
│   ├── key.pem
│   └── ca.pem
└── README-SSL.md
```

## Usage

```bash
python secure-queue-send.py <connection-url> <address> <message-body> [auth-mode]
```

### Parameters

- `connection-url`: The AMQP broker URL (should use `amqps://` for SSL/TLS)
- `address`: The queue address to send the message to
- `message-body`: The message content to send
- `auth-mode`: Authentication mode (EXTERNAL, PLAIN, ANONYMOUS, AUTO) - Default: ANONYMOUS

### Examples

```bash
# Recommended: SSL/TLS encryption with ANONYMOUS authentication
python secure-queue-send.py amqps://localhost:5671 my.queue "Hello, secure world!"

# Explicit ANONYMOUS authentication
python secure-queue-send.py amqps://localhost:5671 my.queue "Hello, secure world!" ANONYMOUS

# Client certificate authentication (requires broker configuration)
python secure-queue-send.py amqps://localhost:5671 my.queue "Hello, secure world!" EXTERNAL

# PLAIN authentication with SSL
python secure-queue-send.py amqps://localhost:5671 my.queue "Hello, secure world!" PLAIN
```

## SSL Configuration Details

The script configures SSL with the following settings:

- **Mode**: Client mode (`SSLDomain.MODE_CLIENT`)
- **Authentication**: Uses EXTERNAL SASL mechanism with client certificates
- **Peer Verification**: `VERIFY_PEER_NAME` - verifies both certificate and hostname
- **Private Key Password**: Currently set to `QWErty123` (modify as needed)

## Differences from Original queue-send.py

1. **SSL/TLS Support**: Added comprehensive SSL/TLS configuration
2. **Enhanced Error Handling**: Added specific error handlers for transport, connection, session, and link errors
3. **Certificate Validation**: Pre-flight check for required SSL certificate files
4. **Secure Connection**: Uses `ssl_domain` parameter and `allowed_mechs="EXTERNAL"`
5. **Improved Logging**: More detailed status messages indicating secure operations

## Security Notes

- The private key password is currently hardcoded as `QWErty123`. In production, consider:
  - Using environment variables
  - Prompting for password input
  - Using password-protected key files
- Ensure certificate files have appropriate file permissions (readable only by the application user)
- Regularly rotate certificates according to your security policy

## Troubleshooting

### Common Issues

1. **Certificate files not found**: Ensure all three certificate files exist in the `./ssl/` directory
2. **Permission denied**: Check file permissions on certificate files
3. **SSL handshake failure**: Verify that the CA certificate matches the broker's certificate
4. **Authentication failure**: Ensure the client certificate is properly signed and trusted by the broker

### Error Messages

The script provides detailed error messages for various failure scenarios:
- Missing certificate files
- SSL/TLS transport errors
- Connection authentication failures
- Link establishment errors
