# Cyrus SASL Authentication with qpid-proton-python

This document explains the Cyrus SASL authentication integration in the `secure-queue-send.py` script for use with Solace PubSub+ brokers.

## Overview

The script has been modified to use Cyrus SASL authentication instead of the basic SASL mechanisms. This provides better compatibility with enterprise messaging systems like Solace PubSub+ and supports more authentication mechanisms.

## Key Changes

### 1. Import Changes
- Added `SASL` import from proton module
- Enables access to Cyrus SASL configuration methods

### 2. SASL Configuration
- **config_name()**: Sets SASL configuration name to "proton-client"
- **config_path()**: Configures SASL library search path
- **allowed_mechs()**: Specifies allowed authentication mechanisms
- **allow_insecure_mechs**: Allows PLAIN over SSL/TLS

### 3. Authentication Modes

#### EXTERNAL Authentication
- Uses SSL/TLS client certificates for authentication
- Identity derived from certificate subject
- Requires broker configuration to trust the CA certificate

#### PLAIN Authentication  
- Username/password authentication over SSL/TLS
- Uses certificate CN as username by default
- Secure when used over encrypted connections

#### ANONYMOUS Authentication
- No authentication required
- Provides SSL/TLS encryption only
- Recommended for testing and non-sensitive environments

## Configuration Files

### SASL Configuration
The script looks for SASL configuration in:
- `/etc/sasl2/proton-client.conf`
- `/usr/lib/sasl2/proton-client.conf`
- Custom path via `PN_SASL_CONFIG_PATH` environment variable

### Sample proton-client.conf
```
# Cyrus SASL configuration for qpid-proton client
mech_list: EXTERNAL PLAIN ANONYMOUS
pwcheck_method: auxprop
```

## Environment Variables

### PN_SASL_CONFIG_PATH
Set custom SASL configuration directory:
```bash
export PN_SASL_CONFIG_PATH="/path/to/sasl/config:/etc/sasl2"
```

## Usage Examples

### EXTERNAL Authentication (Client Certificate)
```bash
python secure-queue-send.py amqps://localhost:5671 my.queue "Hello World!" EXTERNAL
```

### PLAIN Authentication over SSL/TLS
```bash
python secure-queue-send.py amqps://localhost:5671 my.queue "Hello World!" PLAIN
```

### ANONYMOUS Authentication (SSL/TLS only)
```bash
python secure-queue-send.py amqps://localhost:5671 my.queue "Hello World!" ANONYMOUS
```

### Auto-detect Mechanisms
```bash
python secure-queue-send.py amqps://localhost:5671 my.queue "Hello World!" AUTO
```

## Solace PubSub+ Broker Requirements

### For EXTERNAL Authentication
1. Upload CA certificate to Solace broker
2. Configure client certificate authentication
3. Create client username matching certificate CN
4. Configure appropriate ACL profiles

### For PLAIN Authentication
1. Configure username/password authentication
2. Ensure SSL/TLS is enabled
3. Create user accounts in Solace

## Debugging

The script provides detailed logging for:
- SSL/TLS connection details
- SASL mechanism negotiation
- Authentication outcomes
- Transport security status

### Extended SASL Support
Check if Cyrus SASL is available:
```python
from proton import SASL
if SASL.extended():
    print("Cyrus SASL extended support available")
```

## Security Considerations

1. **Certificate Security**: Protect private keys and certificates
2. **SASL Configuration**: Secure SASL configuration files
3. **Network Security**: Always use SSL/TLS for PLAIN authentication
4. **Broker Configuration**: Properly configure broker authentication

## Troubleshooting

### Common Issues
1. **SASL Configuration Not Found**: Check `PN_SASL_CONFIG_PATH`
2. **Authentication Failed**: Verify broker configuration
3. **Certificate Issues**: Check certificate chain and CA trust
4. **Mechanism Not Available**: Verify Cyrus SASL installation

### Debug Output
The script provides detailed debug information including:
- SASL mechanism used
- Authentication outcome
- User identity information
- Transport security status
