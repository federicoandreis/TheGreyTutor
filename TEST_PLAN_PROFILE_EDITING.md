# Test Plan: User Profile Editing Feature

## Test Environment Setup

### Backend Testing
```bash
cd thegreytutor/backend
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx
```

### Frontend Testing
```bash
cd thegreytutor/frontend
npm install
npm install --save-dev @testing-library/react-native @testing-library/jest-native
```

## Manual Testing Checklist

### 1. Profile Navigation
- [ ] Open app and navigate to Profile tab
- [ ] Verify "Edit Profile" button is visible
- [ ] Tap "Edit Profile" button
- [ ] Verify EditProfileScreen opens correctly

### 2. Form Display
- [ ] Verify current username is pre-filled
- [ ] Verify current email is pre-filled
- [ ] Verify current display name is pre-filled
- [ ] Verify current avatar is displayed

### 3. Username Validation
- [ ] Clear username field and tap Save
  - **Expected**: Error message "Username is required"
- [ ] Enter "ab" and tap Save
  - **Expected**: Error message "Username must be at least 3 characters"
- [ ] Enter "invalid user" and tap Save
  - **Expected**: Error message about invalid characters
- [ ] Enter valid username and verify error clears

### 4. Email Validation
- [ ] Clear email field and tap Save
  - **Expected**: Error message "Email is required"
- [ ] Enter "invalid-email" and tap Save
  - **Expected**: Error message "Please enter a valid email address"
- [ ] Enter valid email and verify error clears

### 5. Display Name Validation
- [ ] Clear display name field and tap Save
  - **Expected**: Error message "Display name is required"
- [ ] Enter "a" and tap Save
  - **Expected**: Error message "Display name must be at least 2 characters"
- [ ] Enter valid display name and verify error clears

### 6. Avatar Picker
- [ ] Tap "Change Avatar" button
  - **Expected**: Permission request dialog appears (first time)
- [ ] Grant permission
  - **Expected**: Image picker opens
- [ ] Select an image
  - **Expected**: Avatar updates in form
- [ ] Deny permission
  - **Expected**: Alert about permission requirement

### 7. Cancel Functionality
- [ ] Open Edit Profile without making changes
- [ ] Tap "Cancel"
  - **Expected**: Navigate back immediately
- [ ] Open Edit Profile and make changes
- [ ] Tap "Cancel"
  - **Expected**: Confirmation dialog appears
- [ ] Tap "Discard" in dialog
  - **Expected**: Navigate back, changes discarded

### 8. Save Functionality
- [ ] Update username, email, and display name
- [ ] Tap "Save"
  - **Expected**: Loading indicator shows
  - **Expected**: Success alert appears
  - **Expected**: Navigate back to Profile screen
- [ ] Verify changes are reflected on Profile screen

### 9. Error Handling
- [ ] Try to update with duplicate username (if possible with test data)
  - **Expected**: Error alert
- [ ] Try to update with duplicate email (if possible with test data)
  - **Expected**: Error alert
- [ ] Simulate network error
  - **Expected**: Error alert "Failed to update profile"

### 10. UI/UX Verification
- [ ] Verify form fields have proper icons
- [ ] Verify error messages are in red
- [ ] Verify info card at bottom is visible
- [ ] Verify header shows "Edit Profile" title
- [ ] Verify Cancel and Save buttons are properly styled
- [ ] Test on different screen sizes (if possible)
- [ ] Test with keyboard open (proper scrolling)

## Automated Testing

### Backend Tests

Run all profile update tests:
```bash
cd thegreytutor/backend
pytest tests/test_auth.py::TestAuthEndpoints::test_update_profile_success -v
pytest tests/test_auth.py::TestAuthEndpoints::test_update_profile_partial -v
pytest tests/test_auth.py::TestAuthEndpoints::test_update_profile_duplicate_username -v
pytest tests/test_auth.py::TestAuthEndpoints::test_update_profile_duplicate_email -v
pytest tests/test_auth.py::TestAuthEndpoints::test_update_profile_invalid_username -v
pytest tests/test_auth.py::TestAuthEndpoints::test_update_profile_no_auth -v
```

### Frontend Tests

Run EditProfileScreen tests:
```bash
cd thegreytutor/frontend
npm test -- EditProfileScreen.test.tsx
```

## API Testing (Using cURL or Postman)

### 1. Register a Test User
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123",
    "name": "Test User"
  }'
```

### 2. Get Access Token
Save the `access_token` from the registration response.

### 3. Update Profile
```bash
curl -X PUT http://localhost:8000/auth/me \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "username": "updateduser",
    "email": "updated@example.com",
    "name": "Updated Name",
    "avatar": "🧙‍♂️"
  }'
```

### 4. Verify Update
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## Database Verification

### Check Avatar Column Exists
```sql
-- PostgreSQL
\d users

-- Or
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'users' AND column_name = 'avatar';
```

### Verify User Data After Update
```sql
SELECT id, username, email, name, avatar, created_at, last_login
FROM users
WHERE username = 'updateduser';
```

## Performance Testing

### Response Time Benchmarks
- Profile update should complete in < 500ms
- Form validation should be instant (< 50ms)
- Image picker should open in < 200ms

### Load Testing (Optional)
```bash
# Using Apache Bench
ab -n 100 -c 10 -H "Authorization: Bearer <token>" \
   -p profile_update.json \
   -T application/json \
   http://localhost:8000/auth/me
```

## Accessibility Testing

- [ ] Test with screen reader (if available)
- [ ] Verify all form fields have proper labels
- [ ] Verify error messages are announced
- [ ] Test keyboard navigation
- [ ] Verify color contrast meets WCAG standards

## Security Testing

- [ ] Verify endpoint requires authentication
  - Try accessing without token → Should return 401
- [ ] Verify JWT token validation
  - Try with invalid token → Should return 401
- [ ] Verify username uniqueness
  - Try duplicate username → Should return 400
- [ ] Verify email uniqueness
  - Try duplicate email → Should return 400
- [ ] Verify password is never returned in responses
- [ ] Test SQL injection attempts in form fields
- [ ] Test XSS attempts in form fields

## Edge Cases

### 1. Concurrent Updates
- Open EditProfile on two devices
- Update profile on device A
- Try to update on device B
- Verify behavior

### 2. Long Strings
- Enter very long username (51+ chars)
  - **Expected**: Validation error or truncation
- Enter very long email
  - **Expected**: Validation error
- Enter very long display name (101+ chars)
  - **Expected**: Validation error or truncation

### 3. Special Characters
- Test usernames with: `test_user`, `test-user`
  - **Expected**: Should work
- Test usernames with: `test user`, `test@user`
  - **Expected**: Validation error
- Test display names with emojis
  - **Expected**: Should work

### 4. Network Conditions
- Enable airplane mode mid-save
  - **Expected**: Error alert
- Slow 3G connection
  - **Expected**: Loading indicator, eventual success or timeout

### 5. Session Expiration
- Wait for token to expire
- Try to update profile
  - **Expected**: 401 error, redirect to login

## Regression Testing

After implementing this feature, verify:
- [ ] Login still works
- [ ] Registration still works
- [ ] Password change still works
- [ ] Other profile screen buttons still work
- [ ] Chat functionality unaffected
- [ ] Learning paths unaffected
- [ ] Logout still works

## Test Data

### Valid Test Cases
```json
{
  "username": "validuser123",
  "email": "valid@example.com",
  "name": "Valid User",
  "avatar": "🧙‍♂️"
}
```

### Invalid Test Cases
```json
// Invalid username (spaces)
{ "username": "invalid user" }

// Invalid email
{ "email": "not-an-email" }

// Too short username
{ "username": "ab" }

// Empty display name
{ "name": "" }
```

## Success Criteria

✅ All automated tests pass
✅ All manual test cases pass
✅ No console errors or warnings
✅ Database migration applied successfully
✅ API responds with correct status codes
✅ UI is responsive and accessible
✅ No regression in existing features
✅ Documentation is complete and accurate

## Test Results Log

### Test Run: [DATE]

| Test Case | Status | Notes |
|-----------|--------|-------|
| Profile Navigation | ⬜ | |
| Form Display | ⬜ | |
| Username Validation | ⬜ | |
| Email Validation | ⬜ | |
| Display Name Validation | ⬜ | |
| Avatar Picker | ⬜ | |
| Cancel Functionality | ⬜ | |
| Save Functionality | ⬜ | |
| Error Handling | ⬜ | |
| Backend Tests | ⬜ | |
| Frontend Tests | ⬜ | |

## Issues Found

| Issue # | Description | Severity | Status | Resolution |
|---------|-------------|----------|--------|------------|
| | | | | |

## Sign-off

- [ ] Developer tested
- [ ] QA tested (if applicable)
- [ ] Code reviewed
- [ ] Documentation reviewed
- [ ] Ready for deployment
