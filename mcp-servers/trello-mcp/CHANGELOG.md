# Changelog

All notable changes to the Trello MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-23

### Added

#### Core Features
- **MCP Server Implementation** - Full Model Context Protocol 2025-06-18 specification compliance
- **Three Production Tools:**
  - `trello_get_board_structure` - Get complete board structure (lists + cards)
  - `trello_create_card` - Create cards with title, description, and due date
  - `trello_move_card` - Move cards between lists

#### Architecture
- **Async HTTP Client** - httpx-based implementation with connection pooling
- **Rate Limiting** - Intelligent throttling (90 req/10s default, configurable)
- **Exponential Backoff** - Automatic retry with jitter for 429 errors (max 5 attempts)
- **Pydantic Schemas** - Strict data validation for all inputs/outputs
- **Environment-Based Config** - 12-factor app principles (no hardcoding)

#### Developer Experience
- **Validation Script** (`verify_setup.py`) - Test credentials before configuring Claude
- **Dual Platform Support:**
  - Claude Desktop configuration guide
  - Claude Code CLI setup documentation
- **Comprehensive Error Messages** - Actionable feedback for auth/network/validation errors
- **Type Safety** - Full mypy strict mode compliance

#### Documentation
- **README.md** - Complete setup and usage guide
- **Architecture Documentation** - Design principles and implementation details
- **Troubleshooting Guide** - Solutions for common issues
- **Example Workflows** - Real-world usage patterns

### Technical Details

#### Dependencies
- `mcp>=1.0.0` - Official MCP SDK
- `httpx>=0.27.0` - Async HTTP client
- `pydantic>=2.0.0` - Data validation
- `pydantic-settings>=2.0.0` - Environment management
- `python-dotenv>=1.0.0` - .env file loading
- `backoff>=2.2.0` - Retry logic

#### Security
- Environment variable-based credential management
- No hardcoded secrets or absolute paths
- Token validation on server startup
- Separate stderr logging (stdout reserved for MCP protocol)

#### Performance
- Nested resource optimization (2 API calls instead of N+1)
- Proactive rate limit monitoring
- Connection pooling via httpx
- Async I/O (non-blocking event loop)

### Known Limitations

- Does not support Trello attachments (file uploads) yet
- Does not support card comments (planned for v1.1.0)
- Does not support board creation (planned for v1.2.0)
- OAuth 2.0 not yet implemented (Trello migration pending)

## [Unreleased]

### Planned for v1.1.0
- [ ] Add card comment support
- [ ] Add label management (create, assign, remove)
- [ ] Add checklist support
- [ ] Add member assignment to cards
- [ ] Webhook support for real-time updates

### Planned for v1.2.0
- [ ] Board creation and configuration
- [ ] Custom field support
- [ ] Power-Up integration
- [ ] Bulk operations (create multiple cards)
- [ ] Search functionality

### Planned for v2.0.0
- [ ] OAuth 2.0 support (when Trello completes migration)
- [ ] Multi-board operations
- [ ] Advanced filtering and querying
- [ ] Integration with other MCP servers
- [ ] GraphQL support (if Trello releases GraphQL API)

---

[1.0.0]: https://github.com/your-repo/trello-mcp/releases/tag/v1.0.0
