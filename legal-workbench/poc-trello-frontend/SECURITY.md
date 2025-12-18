```markdown
# Security Checklist - Trello Data Extractor Frontend POC

This document outlines initial security considerations for the Trello Data Extractor frontend, following best practices for handling sensitive legal data.

## 1. Data Handling & Storage

- [ ] **No Sensitive Data in Local Storage/Session Storage:** Ensure no Personally Identifiable Information (PII), case details, or confidential legal data is stored client-side in insecure mechanisms. (Currently, only Trello IDs are in Zustand, which is acceptable for POC).
- [ ] **State Management (Zustand):** While Zustand itself is secure, ensure that no sensitive data persists in the store beyond necessary transactional display, and is cleared appropriately (e.g., on logout, session expiry).
- [ ] **Client-Side Caching:** If implemented, ensure cached data (e.g., Trello board/list structure) does not contain sensitive content, or is encrypted/scoped securely. Implement appropriate TTLs.

## 2. API Communication

- [ ] **HTTPS Only:** All communication with the backend API (`http://localhost:8004/api/v1`) must use HTTPS in production to encrypt data in transit. (Currently `http` for local dev).
- [ ] **Authentication & Authorization:**
    - [ ] Implement secure user authentication (e.g., OAuth2, JWT).
    - [ ] Ensure all API requests are authorized with valid tokens.
    - [ ] Frontend should not store long-lived authentication tokens.
- [ ] **CORS Configuration:** Backend must be configured with strict CORS policies to only allow requests from authorized frontend origins.
- [ ] **Input Validation:** Implement client-side validation for any user inputs sent to the API to prevent common vulnerabilities (e.g., XSS, SQL injection via malformed input, though backend must also validate).

## 3. UI/UX Security

- [ ] **Content Security Policy (CSP):** Implement a robust CSP to mitigate XSS attacks by restricting sources of scripts, styles, and other assets.
- [ ] **Clickjacking Protection:** Implement X-Frame-Options or CSP frame-ancestors to prevent the page from being embedded in iframes on malicious sites.
- [ ] **Error Handling:** Generic error messages should be displayed to users; detailed error messages (e.g., stack traces, sensitive data) should **never** be exposed in the frontend. Log detailed errors securely on the backend.
- [ ] **Data Truncation/Masking:** Implement truncation or masking of sensitive data fields where appropriate, especially in overview tables or logs, showing full details only when explicitly requested and authorized.

## 4. Dependencies & Tooling

- [ ] **Dependency Audits:** Regularly audit third-party libraries and packages for known vulnerabilities (e.g., `npm audit`).
- [ ] **Build Process Security:** Ensure the build process prevents injection of malicious code or compromise of build artifacts.

## 5. Export Functionality

- [ ] **Sanitization:** Any data exported to JSON, CSV, Markdown, or Plain Text should be properly sanitized to prevent injection attacks (e.g., CSV injection, XSS in Markdown viewers). This is especially critical if data is directly rendered by other applications.
- [ ] **Access Control:** Ensure only authorized users can export data, and that they can only export data they are permitted to view.

---

*This is a living document and will be updated as the project evolves.*
```
