# Documentation Update: MCP_DATA_DIR and MCP_WORKERS Parameters

## 📋 **What Was Added to README.md**

### 1. **Quick Configuration Reference** (Early in README)
- Added a quick reference table for key environment variables
- Included practical examples for different use cases
- Shows default values and descriptions at a glance

### 2. **Detailed MCP_DATA_DIR Documentation**
- **Purpose**: Controls where MITRE ATT&CK STIX data files are stored
- **Default Behavior**: OS-specific cache directories
- **Data Structure**: Shows the directory layout created
- **Usage Examples**: Custom paths, Docker volumes
- **Important Notes**: Storage requirements, permissions, caching

### 3. **Comprehensive MCP_WORKERS Documentation**
- **Performance Characteristics Table**: Memory usage vs. concurrency
- **Usage Examples**: Development vs. production settings
- **Critical Limitations**: Memory overhead, no data sharing, startup time
- **Recommended Settings**: Based on available RAM
- **Memory Requirements**: Clear guidelines for different scenarios
- **Monitoring Commands**: How to check resource usage

### 4. **Enhanced Troubleshooting Section**
- **MCP_DATA_DIR Issues**: Permission errors, data loading, custom paths
- **MCP_WORKERS Issues**: Memory usage, startup problems, performance
- **Performance Optimization**: Production best practices
- **Monitoring Commands**: Resource usage tracking

## 🎯 **Key Information Users Now Have**

### **MCP_DATA_DIR:**
- ✅ **Default locations** for Windows, macOS, Linux
- ✅ **Data structure** showing what files are created
- ✅ **Storage requirements** (~50-100MB per domain)
- ✅ **Permission requirements** and troubleshooting
- ✅ **Docker integration** examples

### **MCP_WORKERS:**
- ✅ **Memory impact** (~500MB per worker)
- ✅ **Performance trade-offs** (concurrency vs. memory)
- ✅ **Recommended settings** based on available RAM
- ✅ **Critical limitations** (no data sharing between workers)
- ✅ **Monitoring commands** for resource usage

### **Troubleshooting:**
- ✅ **Common issues** with both parameters
- ✅ **Solutions** for permission, memory, and performance problems
- ✅ **Monitoring commands** for debugging
- ✅ **Production optimization** tips

## 📊 **Impact on User Experience**

### **Before:**
- Users had to guess how parameters worked
- No guidance on memory requirements
- No troubleshooting for common issues
- Unclear performance implications

### **After:**
- ✅ **Clear understanding** of what each parameter does
- ✅ **Memory requirements** clearly documented
- ✅ **Performance implications** explained
- ✅ **Troubleshooting guide** for common issues
- ✅ **Production recommendations** provided
- ✅ **Monitoring commands** for debugging

## 🚀 **Quick Reference for Users**

| Parameter | Default | Memory Impact | Use Case |
|-----------|---------|---------------|----------|
| `MCP_DATA_DIR` | Auto-detected | N/A | Data storage location |
| `MCP_WORKERS=1` | Default | ~500MB | Development |
| `MCP_WORKERS=2` | Production | ~1GB | Small production |
| `MCP_WORKERS=4` | High-perf | ~2GB+ | Large production |

## 📝 **Files Updated**
- ✅ `README.md` - Comprehensive documentation added
- ✅ All tests pass successfully
- ✅ Documentation is accurate and helpful
- ✅ Users now have complete understanding of these critical parameters
