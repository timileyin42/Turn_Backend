# Role-Based Access Control (RBAC) Documentation

## Overview

The TURN Platform implements a comprehensive **Role-Based Access Control (RBAC)** system to manage user permissions and access levels across the application.

## User Roles

The platform supports **5 distinct roles** with increasing levels of access:

### 1.  USER (Default Role)
**Purpose:** Regular job seekers and learners

**Permissions:**
-  View and edit their own profile
-  Search and view job listings
-  Apply to jobs
-  Create and manage CVs
-  Build portfolios
-  Access learning resources
-  Participate in project simulations
-  View mentor profiles
-  Cannot post jobs
-  Cannot review other users' applications

**Use Cases:**
- Job seekers
- Students
- Career changers
- Learners

---

### 2.  RECRUITER
**Purpose:** Recruiters who can post jobs and review applications

**Permissions:**
-  All USER permissions
-  **Create job postings**
-  **Update and delete own job postings**
-  **Review applications** for their jobs
-  **View applicant CVs**
-  Manage company profile (basic)
-  Cannot access admin functions
-  Cannot manage other recruiters

**Use Cases:**
- External recruiters
- Recruitment agencies
- Talent acquisition specialists

---

### 3.  COMPANY
**Purpose:** Company representatives with extended access

**Permissions:**
-  All RECRUITER permissions
-  **Manage company profile** (full access)
-  **Manage multiple recruiters** under their company
-  **View company-wide application analytics**
-  Post jobs under company brand
-  Cannot access admin functions
-  Cannot manage other companies

**Use Cases:**
- HR managers
- Company administrators
- Hiring managers
- Corporate accounts

---

### 4.  MENTOR
**Purpose:** Mentors who provide guidance and support

**Permissions:**
-  All USER permissions
-  **Create mentorship programs**
-  **Manage mentees**
-  **Access mentee progress data**
-  Provide feedback on projects
-  Create educational content
-  Cannot post jobs
-  Cannot review applications

**Use Cases:**
- Career coaches
- Industry professionals
- Senior project managers
- Educators

---

### 5.  ADMIN
**Purpose:** Platform administrators with full access

**Permissions:**
-  **ALL PERMISSIONS** across the platform
-  Manage all users
-  Assign and modify user roles
-  Deactivate/activate accounts
-  Delete users and content
-  View system statistics
-  Access admin dashboard
-  Configure platform settings
-  Manually verify emails
-  Perform bulk operations

**Use Cases:**
- Platform administrators
- System maintainers
- Support team leads

---

## Authentication in Swagger UI

### How to Login

1. **Navigate to Swagger UI:** Open `http://localhost:8000/docs`

2. **Click the "Authorize" Button:** Look for the 🔒 lock icon at the top right

3. **Enter Credentials:**
   - **Username:** Your email address (e.g., `user@example.com`)
   - **Password:** Your password

4. **Click "Authorize":** You'll automatically receive a JWT token

5. **Start Making Requests:** All authenticated endpoints will now work

### OAuth2 Password Flow

The platform uses **OAuth2 Password Flow** for authentication:

- **Token URL:** `/api/v1/auth/login`
- **Grant Type:** `password`
- **Token Type:** `Bearer JWT`
- **Token Expiration:** Configurable (default: 1 hour)
- **Refresh Tokens:** Supported (7 days)

### Alternative: Manual Bearer Token

If you prefer manual token management:

1. Call `/api/v1/auth/login-json` with JSON body:
   ```json
   {
     "username": "user@example.com",
     "password": "your_password"
   }
   ```

2. Copy the `access_token` from response

3. In Swagger UI, click "Authorize" and enter:
   ```
   Bearer <your_access_token>
   ```

---

## Using RBAC in Code

### 1. Require Specific Role(s)

```python
from fastapi import APIRouter, Depends
from app.core.dependencies import require_admin, require_recruiter, UserRole
from app.database.user_models import User

router = APIRouter()

@router.get("/admin-only")
async def admin_endpoint(current_user: User = Depends(require_admin)):
    """Only admins can access this."""
    return {"message": "Welcome, admin!"}

@router.get("/recruiter-or-admin")
async def recruiter_endpoint(current_user: User = Depends(require_recruiter)):
    """Recruiters and admins can access this."""
    return {"message": "Welcome, recruiter!"}
```

### 2. Check Permissions

```python
from app.core.rbac import has_permission, Permission

@router.post("/jobs")
async def create_job(current_user: User = Depends(get_current_user)):
    """Create job with permission check."""
    if not has_permission(current_user, Permission.JOB_CREATE):
        raise HTTPException(status_code=403, detail="Cannot create jobs")
    
    # Create job logic...
    return {"message": "Job created"}
```

### 3. Resource Ownership Check

```python
from app.core.rbac import can_access_resource, Permission

@router.get("/cvs/{cv_id}")
async def get_cv(
    cv_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get CV with ownership check."""
    cv = await get_cv_by_id(db, cv_id)
    
    # Check if user owns CV or has admin permission
    if not can_access_resource(current_user, cv.user_id, Permission.ADMIN_READ):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return cv
```

### 4. Custom Role Requirements

```python
from app.core.dependencies import require_roles

# Multiple roles allowed
@router.post("/content")
async def create_content(
    current_user: User = Depends(require_roles(UserRole.MENTOR, UserRole.ADMIN))
):
    """Only mentors and admins can create content."""
    return {"message": "Content created"}
```

---

## Permission System

### Available Permissions

The platform uses fine-grained permissions:

#### User Permissions
- `user:read` - View user profiles
- `user:write` - Edit user profiles
- `user:delete` - Delete users

#### Job Permissions
- `job:read` - View job listings
- `job:create` - Create job postings
- `job:update` - Update job postings
- `job:delete` - Delete job postings
- `job:apply` - Apply to jobs

#### Application Permissions
- `application:read` - View applications
- `application:write` - Submit applications
- `application:review` - Review/manage applications

#### CV Permissions
- `cv:read` - View CVs
- `cv:write` - Create/edit CVs
- `cv:delete` - Delete CVs

#### Admin Permissions
- `admin:read` - View admin data
- `admin:write` - Perform admin actions
- `admin:delete` - Delete any content
- `system:settings` - Configure platform

### Permission Hierarchy

```
ADMIN > COMPANY > RECRUITER > MENTOR > USER
  5        4          3          2        1
```

---

## API Endpoints

### Admin Endpoints

All admin endpoints require **Admin role** and are prefixed with `/api/v1/admin`:

#### User Management
- `GET /admin/users` - List all users with filtering
- `GET /admin/users/{user_id}` - Get user details
- `PATCH /admin/users/{user_id}/role` - Update user role
- `PATCH /admin/users/bulk-role-update` - Bulk role updates
- `PATCH /admin/users/{user_id}/activation` - Activate/deactivate user
- `DELETE /admin/users/{user_id}` - Delete user permanently

#### System Administration
- `GET /admin/stats` - System statistics
- `GET /admin/permissions/{user_id}` - View user permissions
- `POST /admin/verify-email/{user_id}` - Manually verify email

---

## Role Assignment

### During Registration

Users are assigned the **USER** role by default:

```json
POST /api/v1/auth/register
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "role": "user"  // Optional, defaults to "user"
}
```

### Admin Role Assignment

Admins can change roles via API:

```json
PATCH /api/v1/admin/users/123/role
{
  "user_id": 123,
  "new_role": "recruiter"
}
```

### Bulk Role Assignment

For onboarding multiple recruiters:

```json
PATCH /api/v1/admin/users/bulk-role-update
{
  "user_ids": [123, 456, 789],
  "new_role": "recruiter"
}
```

---

## Security Best Practices

### 1. Principle of Least Privilege
- Users start with minimal permissions (USER role)
- Grant additional permissions only when needed
- Regularly audit user roles

### 2. Token Security
- Tokens expire after 1 hour
- Use refresh tokens for extended sessions
- Never share tokens or credentials
- Implement token rotation

### 3. Resource Ownership
- Users can only access their own resources by default
- Admins can access all resources
- Implement proper ownership checks in endpoints

### 4. Audit Trail
- Log all role changes
- Track admin actions
- Monitor suspicious activity

---

## Testing RBAC

### Test User Creation

Create test users for each role:

```bash
# Regular user
POST /api/v1/auth/register
{"username": "testuser", "email": "user@test.com", "password": "Test123!", "role": "user"}

# Recruiter (needs admin to change role after registration)
POST /api/v1/auth/register
{"username": "recruiter", "email": "recruiter@test.com", "password": "Test123!"}
PATCH /api/v1/admin/users/{id}/role
{"user_id": {id}, "new_role": "recruiter"}
```

### Test Endpoints

```python
# Test with different roles
import httpx

# Login as user
response = httpx.post("http://localhost:8000/api/v1/auth/login", data={
    "username": "user@test.com",
    "password": "Test123!"
})
user_token = response.json()["access_token"]

# Try accessing admin endpoint (should fail)
response = httpx.get(
    "http://localhost:8000/api/v1/admin/stats",
    headers={"Authorization": f"Bearer {user_token}"}
)
assert response.status_code == 403
```

---

## Troubleshooting

### "Access Denied" Errors

**Problem:** Getting 403 Forbidden errors

**Solutions:**
1. Check your current role: `GET /api/v1/auth/me`
2. Verify endpoint permissions in Swagger UI docs
3. Contact admin to upgrade your role if needed

### Token Expired

**Problem:** "Invalid or expired token" error

**Solution:**
```json
POST /api/v1/auth/refresh
{
  "refresh_token": "your_refresh_token"
}
```

### Cannot Login to Swagger

**Problem:** Authorization fails in Swagger UI

**Solutions:**
1. Use email as username (not username field)
2. Check password is correct
3. Verify account is activated
4. Check account is email verified (if required)

---

## Migration from Bearer Token

If migrating from old Bearer token auth:

### Old Way (Manual Bearer Token)
```python
# User manually gets token
response = requests.post("/login", json={"username": "...", "password": "..."})
token = response.json()["access_token"]

# User manually adds to Swagger
# Authorization: Bearer <token>
```

### New Way (OAuth2 Password Flow)
```python
# User clicks "Authorize" in Swagger
# Enters email and password
# Token automatically managed
# All requests automatically authenticated
```

**Benefits:**
-  No manual token copying
-  Better Swagger UI integration
-  Automatic token refresh
-  Clearer role-based access
-  Follows OAuth2 standards

---

## Future Enhancements

### Planned Features
- [ ] Multi-role support (users with multiple roles)
- [ ] Custom permission sets
- [ ] Role-based UI visibility
- [ ] Temporary role escalation
- [ ] Role expiration dates
- [ ] Permission groups
- [ ] OAuth2 with external providers (Google, LinkedIn)
- [ ] Two-factor authentication (2FA)
- [ ] API key authentication for integrations

---

## Support

For questions or issues with RBAC:

- **Documentation:** This file
- **API Docs:** `http://localhost:8000/docs`
- **Support:** support@turn-platform.com

---

## Changelog

### Version 1.0.0 (Current)
-  Implemented 5-role system (USER, RECRUITER, COMPANY, MENTOR, ADMIN)
-  OAuth2 password flow authentication
-  Fine-grained permission system
-  Admin management endpoints
-  Swagger UI integration
-  Role-based middleware
-  Resource ownership checks
