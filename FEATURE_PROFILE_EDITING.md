# User Profile Editing Feature

## Overview
This feature allows users to edit their profile information including username, email, display name, and avatar.

## Changes Summary

### Backend Changes

#### 1. Database Schema
- **File**: `database/models/user.py`
- **Changes**: Added `avatar` column to `User` model
- **Migration**: `database/migrations/001_add_avatar_to_users.sql`

#### 2. API Schemas
- **File**: `thegreytutor/backend/src/api/schemas/auth.py`
- **Added**:
  - `UserUpdateRequest` schema for profile update requests
  - `avatar` field to `UserResponse` schema

#### 3. API Endpoints
- **File**: `thegreytutor/backend/src/api/routes/auth.py`
- **New Endpoint**: `PUT /auth/me`
  - Updates user profile (username, email, name, avatar)
  - Validates uniqueness of username and email
  - Requires authentication
  - Returns updated user data

#### 4. Tests
- **File**: `thegreytutor/backend/tests/test_auth.py`
- **Added Tests**:
  - `test_update_profile_success` - Successful profile update
  - `test_update_profile_partial` - Partial field updates
  - `test_update_profile_duplicate_username` - Duplicate username validation
  - `test_update_profile_duplicate_email` - Duplicate email validation
  - `test_update_profile_invalid_username` - Invalid username format validation
  - `test_update_profile_no_auth` - Authentication requirement

### Frontend Changes

#### 1. New Screen
- **File**: `thegreytutor/frontend/src/screens/profile/EditProfileScreen.tsx`
- **Features**:
  - Form with username, email, display name, and avatar fields
  - Real-time validation with error messages
  - Image picker for avatar selection
  - Unsaved changes detection
  - Loading states during save
  - Success/error feedback

#### 2. Navigation
- **File**: `thegreytutor/frontend/src/navigation/AppNavigator.tsx`
- **Changes**:
  - Created `ProfileStackNavigator` for nested profile screens
  - Added `EditProfile` screen to profile stack
  - Integrated profile stack into main tab navigator

#### 3. Profile Screen Update
- **File**: `thegreytutor/frontend/src/screens/profile/ProfileScreen.tsx`
- **Changes**:
  - Updated "Edit Profile" button to navigate to EditProfileScreen
  - Added navigation prop to component

#### 4. Tests
- **File**: `thegreytutor/frontend/__tests__/screens/profile/EditProfileScreen.test.tsx`
- **Test Coverage**:
  - Component rendering
  - Form field updates
  - Validation errors (username, email, display name)
  - Error clearing on input fix
  - Image picker integration
  - Permission handling
  - Cancel confirmation
  - Save functionality
  - Loading states

## API Documentation

### PUT /auth/me

Update the authenticated user's profile.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
  "username": "string (optional)",
  "email": "string (optional)",
  "name": "string (optional)",
  "avatar": "string (optional)"
}
```

**Success Response (200)**:
```json
{
  "id": "string",
  "username": "string",
  "email": "string",
  "name": "string",
  "avatar": "string",
  "role": "string",
  "created_at": "datetime",
  "last_login": "datetime"
}
```

**Error Responses**:
- `400 Bad Request` - Duplicate username or email
- `401 Unauthorized` - Missing or invalid authentication
- `404 Not Found` - User not found
- `422 Unprocessable Entity` - Validation errors
- `500 Internal Server Error` - Server error

## Validation Rules

### Username
- Required
- Minimum 3 characters
- Maximum 50 characters
- Only letters, numbers, underscores, and hyphens
- Must be unique

### Email
- Required
- Valid email format
- Must be unique

### Display Name
- Required
- Minimum 2 characters
- Maximum 100 characters

### Avatar
- Optional
- Can be emoji or image URI

## Testing

### Running Backend Tests
```bash
cd thegreytutor/backend
pytest tests/test_auth.py::TestAuthEndpoints::test_update_profile_success -v
pytest tests/test_auth.py::TestAuthEndpoints::test_update_profile_partial -v
pytest tests/test_auth.py::TestAuthEndpoints::test_update_profile_duplicate_username -v
pytest tests/test_auth.py::TestAuthEndpoints::test_update_profile_duplicate_email -v
pytest tests/test_auth.py::TestAuthEndpoints::test_update_profile_invalid_username -v
pytest tests/test_auth.py::TestAuthEndpoints::test_update_profile_no_auth -v
```

### Running Frontend Tests
```bash
cd thegreytutor/frontend
npm test -- EditProfileScreen.test.tsx
```

### Running All Tests
```bash
# Backend
cd thegreytutor/backend
pytest tests/test_auth.py -v

# Frontend
cd thegreytutor/frontend
npm test
```

## Database Migration

To apply the database migration for the avatar column:

```bash
# PostgreSQL
psql -U <username> -d thegreytutor < database/migrations/001_add_avatar_to_users.sql

# Or using SQLAlchemy in Python
from database.connection import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar VARCHAR(255)"))
    conn.commit()
```

## Future Enhancements

1. **Image Upload Service**
   - Integrate with cloud storage (S3, Cloudinary)
   - Upload and serve user avatars
   - Image resizing and optimization

2. **Profile Picture Cropping**
   - Add image cropping UI
   - Ensure consistent aspect ratio

3. **Email Verification**
   - Send verification email on email change
   - Require verification before email update takes effect

4. **Username History**
   - Track username changes
   - Prevent rapid username changes

5. **Profile Visibility Settings**
   - Public/private profile toggle
   - Control what information is visible to others

6. **Avatar Library**
   - Provide default avatar options
   - Character avatars from Middle Earth

## Security Considerations

- All endpoints require authentication
- Username and email uniqueness is enforced at database level
- Password is never included in response payloads
- Input validation prevents injection attacks
- Rate limiting should be applied to prevent abuse

## Known Limitations

1. Avatar is currently stored as a string (emoji or URI)
2. No actual image upload implementation (uses local URI from image picker)
3. Email changes don't trigger verification emails
4. No username change cooldown period

## Support

For questions or issues related to this feature, please contact the development team or create an issue in the project repository.
