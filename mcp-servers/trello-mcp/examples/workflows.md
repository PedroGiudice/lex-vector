# Trello MCP Server - Example Workflows

This document provides real-world examples of using the Trello MCP Server with Claude.

---

## 📋 Table of Contents

1. [Basic Operations](#basic-operations)
2. [Project Management](#project-management)
3. [Bug Tracking](#bug-tracking)
4. [Code Review Automation](#code-review-automation)
5. [Advanced Patterns](#advanced-patterns)

---

## Basic Operations

### 1. Explore Your Boards

**User Prompt:**
```
Show me the structure of my Trello board with ID abc123
```

**Claude's Actions:**
1. Calls `trello_get_board_structure(board_id="abc123")`
2. Returns lists, cards, and board metadata

**Expected Output:**
```
Board: Development Board
URL: https://trello.com/b/abc123/...

Lists (4):
  - Backlog (ID: xyz789...)
  - In Progress (ID: def456...)
  - Code Review (ID: ghi123...)
  - Done (ID: jkl789...)

Total cards: 12
Sample cards:
  - Implement login feature (List: xyz789...)
  - Fix navbar bug (List: def456...)
  ...
```

---

### 2. Create a Simple Card

**User Prompt:**
```
Create a card in my "Backlog" list titled "Refactor database queries"
```

**Claude's Actions:**
1. Calls `trello_get_board_structure()` to find "Backlog" list ID
2. Extracts list_id from response
3. Calls `trello_create_card(list_id="xyz789...", name="Refactor database queries")`

**Expected Output:**
```
✓ Card created successfully!

Title: Refactor database queries
URL: https://trello.com/c/newcard123
List ID: xyz789...
Card ID: newcard123...
```

---

### 3. Move a Card

**User Prompt:**
```
Move the "Fix navbar bug" card from "In Progress" to "Done"
```

**Claude's Actions:**
1. Calls `trello_get_board_structure()` to find both card and list IDs
2. Finds card with name "Fix navbar bug" → card_id
3. Finds list "Done" → target_list_id
4. Calls `trello_move_card(card_id="...", target_list_id="...")`

**Expected Output:**
```
✓ Card moved successfully!

Card: Fix navbar bug
New List ID: jkl789...
URL: https://trello.com/c/...
```

---

## Project Management

### 4. Sprint Planning

**User Prompt:**
```
I'm planning this week's sprint. Get my "Product Roadmap" board structure,
then create cards in "This Week" list for:
1. User authentication with OAuth
2. Email notification system
3. API rate limiting

Each card should have a due date of Friday this week.
```

**Claude's Actions:**
1. Calls `trello_get_board_structure()` for "Product Roadmap"
2. Finds "This Week" list ID
3. Calculates Friday's date (ISO 8601 format)
4. Creates three cards with:
   ```python
   trello_create_card(
       list_id="...",
       name="User authentication with OAuth",
       due="2025-11-29T23:59:59Z"
   )
   ```
   (repeated for each task)

---

### 5. Weekly Cleanup

**User Prompt:**
```
Get my "Sprint Board" and move all cards from "In Progress" that don't have
a due date back to "Backlog".
```

**Claude's Actions:**
1. Calls `trello_get_board_structure()`
2. Filters cards in "In Progress" list where `due == null`
3. For each matching card:
   ```python
   trello_move_card(card_id="...", target_list_id="backlog_id")
   ```
4. Reports how many cards were moved

---

## Bug Tracking

### 6. Automated Bug Report from Code Analysis

**User Prompt:**
```
Analyze the file src/auth.js and if you find any security issues,
create a bug card in my "Security Issues" list with:
- Title: Brief description of the vulnerability
- Description: Code snippet + fix recommendation
- Due date: 7 days from now
```

**Claude's Actions:**
1. Reads `src/auth.js` using file reading capabilities
2. Identifies vulnerability (e.g., "Plaintext password storage")
3. Calls `trello_get_board_structure()` to find "Security Issues" list
4. Calls:
   ```python
   trello_create_card(
       list_id="...",
       name="Critical: Passwords stored in plaintext",
       desc="""
       **Location:** src/auth.js:42

       **Issue:**
       ```javascript
       db.users.insert({ password: userInput })
       ```

       **Fix:**
       Hash passwords before storage using bcrypt:
       ```javascript
       const hashed = await bcrypt.hash(userInput, 10)
       db.users.insert({ password: hashed })
       ```

       **Severity:** Critical
       **Impact:** All user passwords exposed in database
       """,
       due="2025-12-06T23:59:59Z"
   )
   ```

---

### 7. Triage Bugs by Severity

**User Prompt:**
```
Get my "Bug Reports" board. For each card in "New Bugs" list:
- If title contains "Critical" or "Security", move to "High Priority"
- If title contains "Minor" or "UI", move to "Low Priority"
- Everything else goes to "Medium Priority"
```

**Claude's Actions:**
1. Calls `trello_get_board_structure()`
2. Parses all cards in "New Bugs" list
3. For each card, checks title with regex
4. Moves cards to appropriate lists based on keywords

---

## Code Review Automation

### 8. Create Review Checklist

**User Prompt:**
```
I just pushed a new feature branch. Create a card in "Code Review" with:
- Title: "Review: User profile redesign (PR #42)"
- Description: Standard code review checklist (tests, security, performance, docs)
- Due: Tomorrow
```

**Claude's Actions:**
```python
trello_create_card(
    list_id="code_review_list_id",
    name="Review: User profile redesign (PR #42)",
    desc="""
    ## Code Review Checklist

    ### Functionality
    - [ ] Feature works as described in requirements
    - [ ] No regressions in existing features
    - [ ] Edge cases handled

    ### Code Quality
    - [ ] Code follows style guide
    - [ ] No code smells (duplicates, long functions, etc.)
    - [ ] Meaningful variable/function names

    ### Testing
    - [ ] Unit tests added/updated
    - [ ] Integration tests pass
    - [ ] Test coverage >80%

    ### Security
    - [ ] No hardcoded secrets
    - [ ] Input validation implemented
    - [ ] SQL injection prevention

    ### Performance
    - [ ] No N+1 queries
    - [ ] Caching used where appropriate
    - [ ] Load testing done

    ### Documentation
    - [ ] README updated
    - [ ] API docs updated
    - [ ] Inline comments for complex logic

    **PR:** https://github.com/org/repo/pull/42
    """,
    due="2025-11-24T23:59:59Z"
)
```

---

## Advanced Patterns

### 9. Multi-Board Coordination

**User Prompt:**
```
I have two boards: "Development" and "Client Requests".
Get both structures, then for each card in "Client Requests > Approved",
create a matching card in "Development > Backlog" with the same title
and a description linking back to the client request.
```

**Claude's Actions:**
1. Calls `trello_get_board_structure()` for both boards
2. Filters "Approved" cards from Client Requests board
3. For each card:
   ```python
   trello_create_card(
       list_id="dev_backlog_id",
       name=client_card.name,
       desc=f"Client request: {client_card.url}\n\n{client_card.desc}"
   )
   ```

---

### 10. Conditional Workflows

**User Prompt:**
```
Get my "Development" board.
If there are more than 5 cards in "In Progress", move the oldest 2 to "Backlog"
and create a card in "Admin" list titled "Warning: WIP limit exceeded"
```

**Claude's Actions:**
1. Calls `trello_get_board_structure()`
2. Filters cards in "In Progress" (checks length)
3. If `len > 5`:
   - Sorts cards by creation date (oldest first)
   - Moves 2 oldest cards to "Backlog"
   - Creates warning card in "Admin" list

---

### 11. Integration with File System

**User Prompt:**
```
Read the file TODO.md in my project root.
For each line that starts with "- [ ]" (unchecked task),
create a card in my "Tasks" list with that task as the title.
```

**Claude's Actions:**
1. Reads `TODO.md` using file reading tool
2. Parses each line with regex: `^- \[ \] (.+)$`
3. Calls `trello_get_board_structure()` to find "Tasks" list
4. For each match:
   ```python
   trello_create_card(
       list_id="tasks_list_id",
       name=matched_text
   )
   ```

---

### 12. Contextual Card Creation

**User Prompt:**
```
I'm working on refactoring the authentication module.
Create a card in "Technical Debt" with:
- Title based on current task
- Description with relevant files from my codebase
- Due date 2 weeks from now
```

**Claude's Actions:**
1. Uses conversation context to understand current task
2. Searches codebase for authentication-related files
3. Compiles list of affected files
4. Creates card:
   ```python
   trello_create_card(
       list_id="tech_debt_id",
       name="Refactor: Authentication module modernization",
       desc="""
       ## Affected Files
       - src/auth/login.js
       - src/auth/session.js
       - src/middleware/auth-check.js

       ## Objective
       Replace custom auth with industry-standard OAuth 2.0

       ## Rationale
       Current implementation:
       - Uses deprecated crypto library
       - No 2FA support
       - Session management brittle
       """,
       due="2025-12-07T23:59:59Z"
   )
   ```

---

## Best Practices

### 1. Always Get Structure First

❌ **Wrong:**
```
Create a card in "Backlog"
```

✅ **Right:**
```
Get my board structure, then create a card in the "Backlog" list
```

**Why:** Claude needs the exact list ID (24-character alphanumeric), not the name.

---

### 2. Be Specific About Boards

❌ **Wrong:**
```
Move the bug card to Done
```

✅ **Right:**
```
On my "Development" board, move the card titled "Fix login bug" to the "Done" list
```

**Why:** You may have multiple boards with "Done" lists or multiple bugs.

---

### 3. Provide Context for Descriptions

❌ **Wrong:**
```
Create a card called "Fix it"
```

✅ **Right:**
```
Create a card titled "Fix login redirect bug" with description explaining
the issue happens when users try to access /dashboard without authentication
```

**Why:** Better descriptions = better team communication.

---

### 4. Use Due Dates for Accountability

✅ **Good:**
```
Create a card with due date next Friday
```

**Why:** Trello's calendar view and notifications work better with due dates.

---

### 5. Leverage Markdown in Descriptions

✅ **Good:**
```
Create a card with description in Markdown format:
- Use checklists for sub-tasks
- Use code blocks for snippets
- Use links to related resources
```

**Why:** Trello renders Markdown in card descriptions.

---

## Tips & Tricks

### Batch Operations

Instead of asking Claude to create cards one by one, provide a list:
```
Create cards in "Backlog" for these tasks:
1. Implement dark mode
2. Add export to CSV
3. Fix mobile responsive layout
4. Add search functionality
```

### Natural Language Dates

Claude understands relative dates:
- "tomorrow"
- "next Friday"
- "end of month"
- "2 weeks from now"

### Contextual Awareness

Claude remembers conversation history:
```
User: Get my Development board structure
Claude: [shows structure]
User: Create a card in the Backlog list  ← Claude knows which board
```

---

**Need more examples? Check the main README.md or open an issue!**
