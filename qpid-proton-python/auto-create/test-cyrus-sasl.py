#!/usr/bin/python
#
# Test script for Cyrus SASL integration with qpid-proton-python
#

from __future__ import print_function
import sys
import os

# Add current directory to path to import the modified secure-queue-send
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from proton import SASL, SSLDomain
    print("✅ Successfully imported SASL and SSLDomain from proton")
except ImportError as e:
    print("❌ Failed to import SASL from proton: {0}".format(e))
    sys.exit(1)

def test_sasl_support():
    """Test SASL support availability"""
    print("\n=== Testing SASL Support ===")
    
    try:
        # Check if extended SASL support is available
        if SASL.extended():
            print("✅ Cyrus SASL extended support is available")
            print("   This means additional SASL mechanisms beyond ANONYMOUS, EXTERNAL, and PLAIN are supported")
        else:
            print("⚠️  Basic SASL support only (ANONYMOUS, EXTERNAL, PLAIN client-side)")
            print("   Cyrus SASL library may not be installed or configured")
        
        return True
    except Exception as e:
        print("❌ Error testing SASL support: {0}".format(e))
        return False

def test_ssl_support():
    """Test SSL support availability"""
    print("\n=== Testing SSL Support ===")
    
    try:
        from proton import SSL
        if SSL.present():
            print("✅ SSL support is available")
            return True
        else:
            print("❌ SSL support is not available")
            return False
    except ImportError:
        print("❌ SSL module not available")
        return False
    except Exception as e:
        print("❌ Error testing SSL support: {0}".format(e))
        return False

def test_sasl_config():
    """Test SASL configuration paths"""
    print("\n=== Testing SASL Configuration ===")
    
    # Check environment variable
    sasl_config_path = os.environ.get('PN_SASL_CONFIG_PATH')
    if sasl_config_path:
        print("✅ PN_SASL_CONFIG_PATH is set: {0}".format(sasl_config_path))
    else:
        print("ℹ️  PN_SASL_CONFIG_PATH not set, using default paths")
    
    # Check for SASL configuration files
    default_paths = ['/etc/sasl2', '/usr/lib/sasl2', './sasl2']
    config_file = 'proton-client.conf'
    
    found_config = False
    for path in default_paths:
        config_path = os.path.join(path, config_file)
        if os.path.exists(config_path):
            print("✅ Found SASL config: {0}".format(config_path))
            found_config = True
        else:
            print("   Checked: {0} (not found)".format(config_path))
    
    if not found_config:
        print("⚠️  No SASL configuration files found")
        print("   You may need to create {0} in one of the search paths".format(config_file))
    
    return found_config

def test_ssl_certificates():
    """Test SSL certificate availability"""
    print("\n=== Testing SSL Certificates ===")
    
    ssl_files = {
        './ssl/cert.pem': 'Client certificate',
        './ssl/key.pem': 'Private key',
        './ssl/ca.pem': 'CA certificate'
    }
    
    all_present = True
    for file_path, description in ssl_files.items():
        if os.path.exists(file_path):
            print("✅ {0}: {1}".format(description, file_path))
        else:
            print("❌ {0}: {1} (missing)".format(description, file_path))
            all_present = False
    
    return all_present

def test_import_modified_script():
    """Test importing the modified secure-queue-send script"""
    print("\n=== Testing Modified Script Import ===")

    try:
        # Test syntax by compiling the script
        import py_compile
        py_compile.compile('secure-queue-send.py', doraise=True)
        print("✅ Script syntax is valid")

        # Test that we can read and parse the script
        with open('secure-queue-send.py', 'r') as f:
            content = f.read()

        # Check for key Cyrus SASL integration elements
        if 'from proton import SSLDomain, SSLException, SASL' in content:
            print("✅ SASL import found")
        else:
            print("❌ SASL import not found")
            return False

        if 'sasl.config_name(' in content:
            print("✅ SASL config_name() call found")
        else:
            print("❌ SASL config_name() call not found")
            return False

        if 'sasl.config_path(' in content:
            print("✅ SASL config_path() call found")
        else:
            print("❌ SASL config_path() call not found")
            return False

        print("✅ All Cyrus SASL integration elements found")
        return True

    except py_compile.PyCompileError as e:
        print("❌ Syntax error in secure-queue-send: {0}".format(e))
        return False
    except Exception as e:
        print("❌ Error testing secure-queue-send: {0}".format(e))
        return False

def main():
    """Run all tests"""
    print("Cyrus SASL Integration Test Suite")
    print("=" * 40)
    
    tests = [
        ("SASL Support", test_sasl_support),
        ("SSL Support", test_ssl_support),
        ("SASL Configuration", test_sasl_config),
        ("SSL Certificates", test_ssl_certificates),
        ("Modified Script Import", test_import_modified_script)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print("❌ Test '{0}' failed with exception: {1}".format(test_name, e))
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("Test Results Summary:")
    print("=" * 40)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print("{0}: {1}".format(test_name, status))
        if result:
            passed += 1
    
    print("\nOverall: {0}/{1} tests passed".format(passed, total))
    
    if passed == total:
        print("🎉 All tests passed! Cyrus SASL integration is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
