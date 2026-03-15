# cli-anything Plugin v1.1.0 Release Notes

## 🚀 New Features

### OpenClaw Integration
- **OpenClaw Support**: Added comprehensive OpenClaw CLI harness support
- **Multi-platform Compatibility**: Works on Windows, Linux, and macOS
- **Enhanced Tooling**: Integration with OpenClaw's advanced tool ecosystem
- **Session Management**: Improved session handling for long-running tasks

### Unreal Engine (UE) Calling Tools
- **UE5/UE4 Support**: Tools for interacting with Unreal Engine projects
- **Blueprint Integration**: CLI access to UE Blueprint systems
- **Automation Scripts**: Automated UE project setup and management
- **Cross-Editor Workflow**: Seamless integration with UE Editor workflows

## 📦 Installation

### For OpenClaw Users
```bash
# Clone the plugin
cd ~/.claude/plugins
git clone https://github.com/HKUDS/CLI-Anything.git cli-anything-plugin

# Ensure OpenClaw is installed
# Visit: https://openclaw.ai for installation instructions
```

### For Unreal Engine Developers
```bash
# Install the plugin
cd ~/.claude/plugins
git clone https://github.com/HKUDS/CLI-Anything.git cli-anything-plugin

# Configure UE project paths in your environment
export UE_PROJECT_PATH="/path/to/your/ue/project"
```

## 🔧 Usage Examples

### OpenClaw Integration
```bash
# Create OpenClaw harness for your application
cli-anything openclaw --app "YourApp.exe"

# Manage OpenClaw sessions
cli-anything openclaw --session list
```

### UE Project Management
```bash
# Generate CLI interface for UE project
cli-anything unreal --project "/path/to/ue/project.uproject"

# Build UE project via CLI
cli-anything unreal --build --configuration Development
```

## 🐛 Bug Fixes & Improvements
- Improved error handling for CLI commands
- Enhanced documentation and examples
- Better cross-platform path handling
- Performance optimizations for large projects

## 📋 Requirements
- **OpenClaw**: Version 1.0.0 or higher
- **Unreal Engine**: UE4.27+ or UE5.0+
- **Python**: 3.8 or higher
- **Claude Code**: Latest version

## 🤝 Contributors
Special thanks to all contributors who made this release possible.

## 🔗 Links
- [GitHub Repository](https://github.com/HKUDS/CLI-Anything)
- [Documentation](https://github.com/HKUDS/CLI-Anything/tree/main/cli-anything-plugin)
- [Issue Tracker](https://github.com/HKUDS/CLI-Anything/issues)

## 📞 Support
For questions or issues:
1. Check the [documentation](https://github.com/HKUDS/CLI-Anything/tree/main/cli-anything-plugin)
2. Open an [issue on GitHub](https://github.com/HKUDS/CLI-Anything/issues)
3. Join the community discussions

---

**Next Steps**: We're already working on v1.2.0 with more advanced OpenClaw integrations and UE5-specific enhancements!