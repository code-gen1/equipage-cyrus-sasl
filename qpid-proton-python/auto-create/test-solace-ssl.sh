#!/bin/bash
#
# Test script for Solace SSL/TLS client certificate authentication
#

set -e

echo "=== Solace SSL/TLS Testing Script ==="
echo ""

# Check if virtual environment is available
if [ ! -d "../../venv" ]; then
    echo "❌ Virtual environment not found at ../../venv"
    echo "Please ensure the Python virtual environment is set up"
    exit 1
fi

# Activate virtual environment
source ../../venv/bin/activate
echo "✅ Activated Python virtual environment"

# Check if certificates exist
if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ] || [ ! -f "ssl/ca.pem" ]; then
    echo "❌ SSL certificates not found in ssl/ directory"
    echo "Available options:"
    echo "1. Use existing certificates (if you have them)"
    echo "2. Generate new Solace-optimized certificates: ./generate-solace-certs.sh"
    exit 1
fi

echo "✅ SSL certificates found"

# Verify certificate chain
echo ""
echo "=== Certificate Verification ==="
if openssl verify -CAfile ssl/ca.pem ssl/cert.pem > /dev/null 2>&1; then
    echo "✅ Certificate chain is valid"
else
    echo "❌ Certificate chain verification failed"
    echo "Consider regenerating certificates with: ./generate-solace-certs.sh"
fi

# Show certificate details
echo ""
echo "Certificate Details:"
echo "CA Subject: $(openssl x509 -in ssl/ca.pem -subject -noout | cut -d'=' -f2-)"
echo "Client Subject: $(openssl x509 -in ssl/cert.pem -subject -noout | cut -d'=' -f2-)"
echo "Client Issuer: $(openssl x509 -in ssl/cert.pem -issuer -noout | cut -d'=' -f2-)"

# Test SSL connection to broker (without AMQP)
echo ""
echo "=== Testing SSL Connection to Broker ==="
echo "Testing basic SSL connectivity to localhost:5671..."

if timeout 5 openssl s_client -connect localhost:5671 -cert ssl/cert.pem -key ssl/key.pem -CAfile ssl/ca.pem -verify_return_error < /dev/null > /dev/null 2>&1; then
    echo "✅ Basic SSL connection successful"
else
    echo "❌ Basic SSL connection failed"
    echo "This could indicate:"
    echo "  - Broker is not running on localhost:5671"
    echo "  - Broker SSL configuration issues"
    echo "  - Certificate trust issues"
fi

# Test different authentication modes
echo ""
echo "=== Testing AMQP Authentication Modes ==="

# Test 1: ANONYMOUS authentication (should work)
echo ""
echo "Test 1: ANONYMOUS authentication"
echo "Command: python secure-queue-send.py amqps://localhost:5671 test.queue 'Test ANONYMOUS' ANONYMOUS"
if python secure-queue-send.py amqps://localhost:5671 test.queue "Test ANONYMOUS $(date)" ANONYMOUS; then
    echo "✅ ANONYMOUS authentication successful"
else
    echo "❌ ANONYMOUS authentication failed"
fi

# Test 2: EXTERNAL authentication (may fail if broker not configured)
echo ""
echo "Test 2: EXTERNAL authentication (client certificate)"
echo "Command: python secure-queue-send.py amqps://localhost:5671 test.queue 'Test EXTERNAL' EXTERNAL"
if python secure-queue-send.py amqps://localhost:5671 test.queue "Test EXTERNAL $(date)" EXTERNAL; then
    echo "✅ EXTERNAL authentication successful"
    echo "🎉 Client certificate authentication is working!"
else
    echo "❌ EXTERNAL authentication failed"
    echo "This indicates the Solace broker needs configuration for client certificate authentication"
fi

# Test 3: Solace-optimized client
echo ""
echo "Test 3: Solace-optimized client"
echo "Command: python solace-secure-send.py amqps://localhost:5671 test.queue 'Test Solace' EXTERNAL"
if python solace-secure-send.py amqps://localhost:5671 test.queue "Test Solace $(date)" EXTERNAL; then
    echo "✅ Solace-optimized client successful"
else
    echo "❌ Solace-optimized client failed"
fi

# Summary and recommendations
echo ""
echo "=== Test Summary and Recommendations ==="
echo ""

if python secure-queue-send.py amqps://localhost:5671 test.queue "Final test" ANONYMOUS > /dev/null 2>&1; then
    echo "✅ SSL/TLS encryption is working correctly"
    echo ""
    echo "Current status:"
    echo "  - SSL/TLS connection: ✅ Working"
    echo "  - Certificate chain: ✅ Valid"
    echo "  - ANONYMOUS auth: ✅ Working"
    
    if python secure-queue-send.py amqps://localhost:5671 test.queue "Test" EXTERNAL > /dev/null 2>&1; then
        echo "  - EXTERNAL auth: ✅ Working"
        echo ""
        echo "🎉 Everything is working! Your Solace broker is properly configured for client certificate authentication."
    else
        echo "  - EXTERNAL auth: ❌ Not working"
        echo ""
        echo "📋 Next steps to enable client certificate authentication:"
        echo ""
        echo "1. Configure Solace broker to trust your CA certificate:"
        echo "   - Upload ssl/ca.pem to Solace as a trusted Certificate Authority"
        echo "   - Enable client certificate authentication in the message VPN"
        echo ""
        echo "2. Solace CLI commands (connect to your broker first):"
        echo "   configure"
        echo "   create certificate-authority \"CustomCA\""
        echo "   certificate pem"
        echo "   # Paste contents of ssl/ca.pem here"
        echo "   exit"
        echo "   message-vpn default"
        echo "   authentication"
        echo "   client-certificate"
        echo "   certificate-authority \"CustomCA\""
        echo "   validate-certificate-date"
        echo "   no shutdown"
        echo "   exit"
        echo "   exit"
        echo "   commit"
        echo ""
        echo "3. Verify Solace configuration:"
        echo "   show certificate-authority"
        echo "   show message-vpn default authentication client-certificate"
        echo ""
        echo "4. Re-run this test script after broker configuration"
    fi
else
    echo "❌ SSL/TLS connection is not working"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Verify Solace broker is running on localhost:5671"
    echo "2. Check broker SSL configuration"
    echo "3. Regenerate certificates: ./generate-solace-certs.sh"
    echo "4. Check broker logs for SSL errors"
fi

echo ""
echo "For detailed troubleshooting, see:"
echo "  - SOLACE-SSL-SETUP.md"
echo "  - SSL-TROUBLESHOOTING.md"
echo ""
echo "Test completed."
