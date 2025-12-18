# Security Testing Checklist

## Authentication & Authorization
- [ ] JWT token validation works
- [ ] Invalid tokens are rejected
- [ ] Expired tokens are rejected
- [ ] Token refresh works (if implemented)
- [ ] Unauthorized access blocked
- [ ] Role-based access (if implemented)

## Data Protection
- [ ] Sensitive data redaction works (SSN, card numbers, passwords)
- [ ] PHI (Protected Health Information) is not logged
- [ ] Database encryption at rest
- [ ] HTTPS enforced in production
- [ ] API keys not exposed in logs
- [ ] Environment variables secured

## Input Validation
- [ ] SQL injection attempts blocked
- [ ] XSS (Cross-Site Scripting) attempts blocked
- [ ] Path traversal attempts blocked
- [ ] File upload restrictions enforced
- [ ] Malicious file uploads rejected
- [ ] Command injection attempts blocked

## API Security
- [ ] Rate limiting works correctly
- [ ] CORS properly configured
- [ ] CSRF protection (if needed)
- [ ] API key validation
- [ ] Request size limits enforced
- [ ] Timeout limits prevent DoS

## Data Privacy
- [ ] User data not shared between users
- [ ] Session isolation works
- [ ] Data deletion works correctly
- [ ] Audit logs don't contain sensitive info
- [ ] Backup data is encrypted

## Network Security
- [ ] SSL/TLS certificates valid
- [ ] No mixed content (HTTP/HTTPS)
- [ ] Secure headers (HSTS, CSP, etc.)
- [ ] No sensitive data in URLs
- [ ] WebSocket connections secured (if used)

## Healthcare-Specific
- [ ] HIPAA compliance checks (for production)
- [ ] PHI handling verified
- [ ] Access controls for medical data
- [ ] Audit trails for medical actions
- [ ] Data retention policies

