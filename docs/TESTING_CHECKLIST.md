# Testing Checklist

## Edge Cases to Test

### Image Upload
- [ ] Very large images (>10MB) - should reject
- [ ] Non-image files (PDF, text) - should reject
- [ ] Corrupted image files
- [ ] Empty file upload
- [ ] Multiple rapid uploads
- [ ] Very small images (<100px)
- [ ] Very wide/tall images (aspect ratio extremes)

### API Endpoints
- [ ] Missing required fields
- [ ] Empty intent string
- [ ] Very long intent (>500 chars)
- [ ] Special characters in intent
- [ ] Concurrent requests (rate limiting)
- [ ] Invalid API keys
- [ ] Network timeouts
- [ ] Server crashes mid-request

### Drug Interaction Checker
- [ ] Single prescription (should work)
- [ ] 5+ prescriptions (max limit)
- [ ] Prescriptions with no text/illegible
- [ ] Prescriptions in different languages
- [ ] Empty allergies field
- [ ] Invalid allergy names
- [ ] Medications with typos

### Diet Portal
- [ ] Invalid condition names
- [ ] Empty condition field
- [ ] Multiple conditions
- [ ] Very long medication lists
- [ ] Invalid food items
- [ ] Special characters in inputs

### Executor
- [ ] Website not loading
- [ ] Elements not found
- [ ] Dynamic content loading
- [ ] Pop-ups interrupting
- [ ] Forms with validation errors
- [ ] Timeout scenarios

## Bottlenecks to Monitor

### Performance
- [ ] LLM API response time (should be <5s)
- [ ] Image processing time
- [ ] Database query time
- [ ] Playwright execution time
- [ ] Frontend render time

### Scalability
- [ ] Multiple concurrent users
- [ ] Large image processing
- [ ] Database connection pooling
- [ ] Memory usage with Playwright
- [ ] API rate limits

### Resource Usage
- [ ] CPU usage during processing
- [ ] Memory leaks (long-running server)
- [ ] Browser instances cleanup
- [ ] Database connection limits

## Connection Issues to Test

### Network
- [ ] Slow internet connection
- [ ] Intermittent connectivity
- [ ] Timeout scenarios
- [ ] CORS errors
- [ ] SSL/TLS issues

### API Failures
- [ ] OpenAI API down
- [ ] Supabase connection lost
- [ ] Playwright browser crash
- [ ] Database timeout

### Recovery
- [ ] Automatic retry logic
- [ ] Graceful error messages
- [ ] Partial success handling
- [ ] Data persistence on failure

## Test Scenarios

### Happy Path
1. Upload valid medical form image
2. Enter clear intent
3. Get successful response
4. View results

### Error Path
1. Upload invalid file
2. See clear error message
3. Retry with valid file
4. Success

### Edge Case Path
1. Upload borderline image
2. Partial success
3. User can retry or proceed

## Performance Benchmarks

- Image upload: <1s
- Vision analysis: <3s
- Planning: <2s
- Execution: <10s
- Total: <15s

## Monitoring

- Add logging for:
  - Request/response times
  - Error rates
  - API call costs
  - User actions

