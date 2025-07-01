# Solace PubSub+ Broker Configuration for Client Certificate Authentication

## Current Problem Analysis

Your Solace PubSub+ broker is rejecting client certificate authentication with these errors:
- `SSL Connection rejected: reason (certificate verify failed: self-signed certificate in certificate chain)`
- `Sol Client username authentication failed - Unauthorized: Untrusted Certificate`

## Root Cause

The Solace broker is **NOT configured** to:
1. Trust your custom CA certificate
2. Enable client certificate authentication
3. Map client certificates to user identities

## Complete Solution

### Step 1: Access Solace Management

#### Option A: Solace CLI (SSH)
```bash
ssh admin@localhost -p 2222
# Default password is usually 'admin'
```

#### Option B: Solace Web Management (SEMP)
```
http://localhost:8080
Username: admin
Password: admin
```

#### Option C: Docker Solace (if using container)
```bash
docker exec -it <solace-container> cli
```

### Step 2: Upload CA Certificate to Solace

#### Via CLI:
```bash
# Enter configuration mode
configure

# Create certificate authority
create certificate-authority "CustomCA"
certificate pem
# Paste the ENTIRE contents of ssl/ca.pem here, including:
# -----BEGIN CERTIFICATE-----
# ... certificate data ...
# -----END CERTIFICATE-----
exit

# Verify CA was created
show certificate-authority "CustomCA"
```

#### Via SEMP REST API:
```bash
# Upload CA certificate via REST API
curl -X POST "http://localhost:8080/SEMP/v2/config/certAuthorities" \
  -H "Content-Type: application/json" \
  -u admin:admin \
  -d '{
    "certAuthorityName": "CustomCA",
    "certContent": "'$(cat ssl/ca.pem | tr -d '\n')'"
  }'
```

### Step 3: Configure Message VPN for Client Certificate Authentication

#### Via CLI:
```bash
# Configure message VPN (usually "default")
message-vpn "default"

# Enable client certificate authentication
authentication
client-certificate
certificate-authority "CustomCA"
validate-certificate-date
no shutdown
exit
exit

# Configure authorization based on certificate subject
authorization
ldap-group-membership-attribute-name "memberOf"
exit

# Create ACL profile for certificate users
create acl-profile "CertificateUsers"
client-connect-default-action allow
publish-topic-default-action allow
subscribe-topic-default-action allow
exit

# Create client profile
create client-profile "CertificateClients"
allow-guaranteed-msg-send
allow-guaranteed-msg-receive
allow-guaranteed-endpoint-create
allow-transacted-session
exit

# Create client username based on certificate CN
create client-username "jcsmp-client"
acl-profile "CertificateUsers"
client-profile "CertificateClients"
no shutdown
exit

# Exit message-vpn configuration
exit
```

### Step 4: Configure SSL Service

#### Via CLI:
```bash
# Configure SSL service
service msg-backbone
ssl
# Enable SSL on port 5671
listen-port 5671 ssl
exit
exit

# Commit all changes
commit
```

### Step 5: Verify Configuration

#### Check Certificate Authority:
```bash
show certificate-authority "CustomCA"
```

#### Check Message VPN Authentication:
```bash
show message-vpn "default" authentication client-certificate
```

#### Check SSL Service:
```bash
show service msg-backbone ssl
```

#### Check Client Username:
```bash
show message-vpn "default" client-username "jcsmp-client"
```

### Step 6: Alternative Configuration (If Above Doesn't Work)

#### Create Certificate-Based User Mapping:
```bash
# Configure certificate-to-username mapping
message-vpn "default"
authentication
client-certificate
certificate-matching-rule "CN-Rule"
condition certificate-thumbprint
expression "jcsmp-client"
attribute-name "cn"
exit
exit
exit
```

### Step 7: Test Configuration

#### Test 1: Verify SSL Connection
```bash
# From your client machine
openssl s_client -connect localhost:5671 \
  -cert ssl/cert.pem -key ssl/key.pem -CAfile ssl/ca.pem
```

#### Test 2: Test AMQP Connection
```bash
# Use the updated client
source ../../venv/bin/activate
python secure-queue-send.py amqps://localhost:5671 my.queue "Test message" EXTERNAL
```

### Step 8: Troubleshooting Commands

#### Enable Debug Logging:
```bash
configure
logging
event ssl debug
event authentication debug
event authorization debug
exit
commit
```

#### Monitor Events:
```bash
show log events level debug | include "SSL\|AUTH"
```

#### Check Current Connections:
```bash
show client "jcsmp-client" detail
show message-vpn "default" connections
```

## Alternative: Generate Solace-Compatible Certificates

If the current certificates still don't work, generate new ones:

```bash
# Run the certificate generation script
./generate-solace-certs.sh

# Update the password in your Python script to 'solace123'
# Test with new certificates
python secure-queue-send.py amqps://localhost:5671 my.queue "Test" EXTERNAL
```

## Expected Successful Output

When properly configured, you should see:
```
SECURE-SEND: SSL/TLS connection established to 'amqps://localhost:5671'
SECURE-SEND: SSL cipher: TLS_AES_256_GCM_SHA384
SECURE-SEND: SSL protocol: TLSv1.3
SECURE-SEND: Opened secure sender for target address 'my.queue'
SECURE-SEND: Sent message 'Test message' over secure connection
```

## Common Issues and Solutions

### Issue: "Certificate verify failed"
**Solution**: Ensure CA certificate is properly uploaded and contains the complete certificate chain

### Issue: "Untrusted Certificate"
**Solution**: Verify certificate-authority is configured in the message-vpn authentication settings

### Issue: "Authentication failed [mech=EXTERNAL]"
**Solution**: Ensure client-username exists and matches the certificate CN

### Issue: "Connection refused"
**Solution**: Verify SSL service is enabled on port 5671

## Verification Script

Run the comprehensive test:
```bash
./test-solace-ssl.sh
```

This will test all authentication modes and provide specific guidance based on the results.

## Summary

The key steps are:
1. ✅ **Upload CA certificate** to Solace as trusted authority
2. ✅ **Enable client certificate authentication** in message-vpn
3. ✅ **Create client username** matching certificate CN
4. ✅ **Configure SSL service** on port 5671
5. ✅ **Test connection** with EXTERNAL authentication

After completing these steps, your client certificate authentication should work successfully with the Solace PubSub+ broker.
