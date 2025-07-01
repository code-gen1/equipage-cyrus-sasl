# Apache Qpid Proton Submodule Integration

This document explains the Apache Qpid Proton submodule integration in the equipage-cyrus-sasl repository.

## Overview

The `qpid-proton-source` directory contains the complete Apache Qpid Proton source code as a Git submodule. This provides direct access to the official Qpid Proton implementation alongside our enhanced Python examples with Cyrus SASL authentication support.

## Repository Structure

```
equipage-cyrus-sasl/
├── qpid-proton-python/          # Enhanced Python examples with Cyrus SASL
│   └── auto-create/
│       ├── secure-queue-send.py # Modified with Cyrus SASL authentication
│       ├── README-CYRUS-SASL.md # Cyrus SASL documentation
│       ├── test-cyrus-sasl.py   # Test suite
│       └── sasl2/               # SASL configuration files
├── qpid-proton-source/          # Official Apache Qpid Proton source (submodule)
│   ├── c/                       # C implementation
│   ├── cpp/                     # C++ implementation
│   ├── python/                  # Official Python bindings
│   ├── ruby/                    # Ruby implementation
│   ├── go/                      # Go implementation
│   ├── examples/                # Official examples
│   ├── tests/                   # Comprehensive test suites
│   └── docs/                    # Official documentation
└── [other equipage examples]    # Original equipage examples
```

## Submodule Information

- **Repository**: https://github.com/apache/qpid-proton.git
- **Current Version**: 0.40.0+ (latest main branch)
- **Path**: `qpid-proton-source/`
- **Purpose**: Provides complete AMQP messaging stack source code

## Working with the Submodule

### Initial Clone
When cloning this repository, initialize the submodule:
```bash
git clone https://github.com/code-gen1/equipage-cyrus-sasl.git
cd equipage-cyrus-sasl
git submodule init
git submodule update
```

### Alternative: Clone with Submodules
```bash
git clone --recursive https://github.com/code-gen1/equipage-cyrus-sasl.git
```

### Update Submodule to Latest
```bash
cd qpid-proton-source
git pull origin main
cd ..
git add qpid-proton-source
git commit -m "Update qpid-proton submodule to latest"
```

### Check Submodule Status
```bash
git submodule status
```

## Building Qpid Proton from Source

### Prerequisites
```bash
# Ubuntu/Debian
sudo apt-get install cmake build-essential libssl-dev libsasl2-dev

# CentOS/RHEL
sudo yum install cmake gcc-c++ openssl-devel cyrus-sasl-devel
```

### Build Process
```bash
cd qpid-proton-source
mkdir build
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local
make -j$(nproc)
sudo make install
```

### Python Bindings
```bash
cd qpid-proton-source/python
python setup.py build
python setup.py install
```

## Integration Benefits

### 1. Complete Development Environment
- Official Qpid Proton source code
- Enhanced Python examples with Cyrus SASL
- Comprehensive test suites
- Official documentation

### 2. Version Consistency
- Ensures compatibility between examples and Qpid Proton version
- Allows testing against specific Qpid Proton versions
- Enables contribution back to Apache Qpid Proton project

### 3. Advanced Development
- Access to C/C++ implementations for performance-critical applications
- Multiple language bindings (Python, C++, Ruby, Go)
- Complete build system and configuration options

### 4. Solace PubSub+ Compatibility
- Test Cyrus SASL examples against official Qpid Proton builds
- Validate SSL/TLS certificate chain configurations
- Ensure enterprise messaging compatibility

## Example Workflows

### Testing Cyrus SASL with Official Build
```bash
# Build official Qpid Proton with SASL support
cd qpid-proton-source
mkdir build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local -DSASL_IMPL=cyrus
make -j$(nproc) && sudo make install

# Test our enhanced examples
cd ../../qpid-proton-python/auto-create
python test-cyrus-sasl.py
python secure-queue-send.py amqps://localhost:5671 test.queue "Hello World!" EXTERNAL
```

### Development and Contribution
```bash
# Make changes to official Qpid Proton
cd qpid-proton-source
# ... make changes ...
git add . && git commit -m "Fix SASL authentication issue"

# Update our repository to use the modified version
cd ..
git add qpid-proton-source
git commit -m "Update to modified qpid-proton with SASL fix"
```

## Maintenance

### Keeping Submodule Updated
Regularly update the submodule to get latest Apache Qpid Proton improvements:
```bash
git submodule update --remote qpid-proton-source
git add qpid-proton-source
git commit -m "Update qpid-proton submodule to latest upstream"
git push
```

### Submodule Best Practices
1. **Pin to Stable Versions**: For production, pin to stable release tags
2. **Test After Updates**: Always test Cyrus SASL examples after submodule updates
3. **Document Changes**: Record significant submodule updates in commit messages
4. **Coordinate Updates**: Ensure team members update submodules consistently

## Troubleshooting

### Submodule Not Initialized
```bash
git submodule init
git submodule update
```

### Submodule Out of Sync
```bash
git submodule sync
git submodule update --init --recursive
```

### Build Issues
Check that all dependencies are installed and paths are correct:
```bash
cd qpid-proton-source
cmake . -DCMAKE_BUILD_TYPE=Debug
```

## Related Documentation

- [Apache Qpid Proton Documentation](qpid-proton-source/README.md)
- [Cyrus SASL Integration Guide](qpid-proton-python/auto-create/README-CYRUS-SASL.md)
- [Cyrus SASL Changes Summary](qpid-proton-python/auto-create/CYRUS-SASL-CHANGES.md)
- [Official Qpid Proton Website](https://qpid.apache.org/proton/)

This integration provides a complete AMQP messaging development environment with enhanced Solace PubSub+ broker compatibility through Cyrus SASL authentication.
