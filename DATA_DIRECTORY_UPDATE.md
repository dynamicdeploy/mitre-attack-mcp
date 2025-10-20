# Data Directory Update: Changed from Cache to Documents

## 📋 **What Was Changed**

### **Old Behavior:**
- **Windows**: `%LOCALAPPDATA%/Cache/mitre-attack-data`
- **macOS**: `~/Library/Caches/mitre-attack-data`
- **Linux**: `~/.cache/mitre-attack-data`

### **New Behavior:**
- **All Platforms**: `~/Documents/mitre-attack-data`

## 🔧 **Files Updated**

### **Core Implementation Files:**
1. **`src/mitre_attack_mcp/server.py`**
   - Updated `get_default_data_dir()` function
   - Changed from cache directory to Documents directory
   - Updated function documentation

2. **`app.py`**
   - Updated `get_default_data_dir()` function
   - Changed from cache directory to Documents directory
   - Updated function documentation

### **Configuration Files:**
3. **`examples/local_config.py`**
   - Updated default data directory references
   - Changed from `~/Library/Caches/mitre-attack-data` to `~/Documents/mitre-attack-data`

### **Documentation Files:**
4. **`README.md`**
   - Updated default behavior documentation
   - Changed from OS-specific cache directories to unified Documents directory
   - Updated important notes about data storage

5. **`CONFIGURATION_GUIDE.md`**
   - Updated environment variable tables
   - Changed default values in documentation

6. **`HTTP_DEPLOYMENT.md`**
   - Updated environment variable documentation
   - Changed default data directory reference

7. **`MCP_CLIENT_CONFIGURATION.md`**
   - Updated environment variable table
   - Changed default data directory reference

## ✅ **Verification**

### **Test Results:**
```bash
# Default data directory now points to Documents
$ python -c "from src.mitre_attack_mcp.server import get_default_data_dir; print(get_default_data_dir())"
/Users/tejaswiredkar/Documents/mitre-attack-data

# Data is successfully downloaded to new location
$ ls -la ~/Documents/mitre-attack-data/v17.1/
-rw------- 1 user staff 44879463 Oct 20 08:10 enterprise-attack.json
-rw------- 1 user staff  2826073 Oct 20 08:10 ics-attack.json
-rw------- 1 user staff  4011725 Oct 20 08:10 mobile-attack.json
```

### **All Tests Pass:**
- ✅ HTTP Server test passes
- ✅ Local configuration examples work
- ✅ Remote configuration examples work
- ✅ MCP Prompts test successfully
- ✅ Data downloads to correct location
- ✅ Server starts with new default path

## 🎯 **Benefits of the Change**

### **User Experience:**
1. **Easier Access**: Data is now in Documents folder, easily accessible
2. **Cross-Platform Consistency**: Same path on all operating systems
3. **Better Organization**: Data is in a user-visible location, not hidden in cache
4. **Persistence**: Data persists between system cleanups of cache directories

### **Developer Experience:**
1. **Simplified Logic**: No more OS-specific cache directory detection
2. **Consistent Behavior**: Same default path across all platforms
3. **Easier Debugging**: Data location is predictable and accessible

## 📁 **New Directory Structure**

```
~/Documents/mitre-attack-data/
└── v17.1/
    ├── enterprise-attack.json  (~45MB)
    ├── mobile-attack.json     (~4MB)
    └── ics-attack.json        (~3MB)
```

## 🔄 **Migration Notes**

### **For Existing Users:**
- **No Action Required**: Server will automatically use new location
- **Data Migration**: Old cache data will be ignored (can be safely deleted)
- **First Run**: Server will download data to new Documents location
- **Custom Paths**: Users with custom `MCP_DATA_DIR` are unaffected

### **For Developers:**
- **Update Tests**: Any tests expecting cache directory paths need updating
- **Update Documentation**: Any custom docs referencing cache paths need updating
- **Docker**: Container behavior unchanged (uses `/app/data`)

## 🚀 **Usage Examples**

### **Default Behavior (New):**
```bash
# Data automatically goes to ~/Documents/mitre-attack-data
python start_server.py
```

### **Custom Path (Unchanged):**
```bash
# Still works as before
MCP_DATA_DIR=/custom/path python start_server.py
```

### **Docker (Unchanged):**
```bash
# Docker still uses /app/data
docker run -e MCP_DATA_DIR=/app/data mitre-attack-mcp
```

## ✅ **Summary**

The change successfully moves the default data directory from OS-specific cache directories to a unified `~/Documents/mitre-attack-data` location. This provides:

- **Better user experience** with accessible data location
- **Cross-platform consistency** with the same path everywhere
- **Simplified implementation** without OS-specific logic
- **Maintained compatibility** with custom data directory settings

All tests pass and the server works correctly with the new default path! 🎉
