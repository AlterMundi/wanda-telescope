# WANDA Telescope - Cursor Rules Organization

This directory contains modular rule files for the Cursor AI assistant. According to [Cursor documentation](https://docs.cursor.com/en/context/rules), rules are organized as follows:

## File Structure

### Always Applied
- **`base.mdc`** - Core project rules that are ALWAYS active. Contains:
  - Project context and architecture
  - Mandatory development practices (TDD, code quality)
  - Critical constraints (Raspberry Pi ecosystem)
  - Error handling requirements

### Context-Specific Rules (Enable as needed)

- **`testing.mdc`** - Testing and quality assurance guidelines
  - Test organization and commands
  - Performance requirements
  - Coverage requirements
  - Test implementation patterns

- **`hardware.mdc`** - Hardware integration and camera/mount control
  - Camera detection hierarchy
  - picamera2 import strategies
  - GPIO configuration
  - Hardware debugging commands

- **`web-api.mdc`** - Web interface and REST API development
  - Flask application structure
  - API endpoint specifications
  - Response standards
  - MJPEG streaming implementation

- **`performance.mdc`** - Performance optimization guidelines
  - Performance benchmarks and targets
  - Memory management strategies
  - Threading optimization
  - Caching strategies

- **`session-management.mdc`** - Automated capture session handling
  - Session architecture
  - Thread safety requirements
  - Progress tracking
  - Metadata export formats

- **`debugging.mdc`** - Debugging and troubleshooting
  - Logging configuration
  - Common debugging commands
  - Debug environment variables
  - Common issues and solutions

### Archive
- **`original-full.mdc`** - Complete original .cursorrules file (kept for reference)

## Usage in Cursor

1. The `base.mdc` file is automatically applied to all conversations
2. Other `.mdc` files can be included when working on specific features
3. Use Cursor's context management to enable/disable specific rule files as needed

## For Developers

- **Cursor Users**: Use these `.mdc` files in the `.cursor/rules/` directory
- **Claude.ai Users**: Use the `CLAUDE.md` file in the repository root
- Both tools have their own configuration to avoid confusion

## Rule Priority

When multiple rules apply, follow this priority:
1. Explicit user instructions (highest priority)
2. `base.mdc` rules (always applied)
3. Context-specific `.mdc` rules (when enabled)
4. General best practices (lowest priority)