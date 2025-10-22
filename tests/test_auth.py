"""
Test cases for authentication endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth_service import auth_service


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication API endpoints."""
    
    async def test_register_user(self, client: AsyncClient, sample_user_data):
        """Test user registration."""
        response = await client.post("/auth/register", json=sample_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["username"] == sample_user_data["username"]
        assert data["first_name"] == sample_user_data["first_name"]
        assert "id" in data
        assert "hashed_password" not in data  # Password should not be returned
    
    async def test_register_duplicate_email(self, client: AsyncClient, sample_user_data):
        """Test registration with duplicate email."""
        # Register user first time
        await client.post("/auth/register", json=sample_user_data)
        
        # Try to register again with same email
        response = await client.post("/auth/register", json=sample_user_data)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    async def test_login_success(self, client: AsyncClient, sample_user_data):
        """Test successful login."""
        # Register user first
        await client.post("/auth/register", json=sample_user_data)
        
        # Login
        login_data = {
            "email_or_username": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    async def test_login_invalid_credentials(self, client: AsyncClient, sample_user_data):
        """Test login with invalid credentials."""
        # Register user first
        await client.post("/auth/register", json=sample_user_data)
        
        # Try login with wrong password
        login_data = {
            "email_or_username": sample_user_data["email"],
            "password": "wrongpassword"
        }
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        login_data = {
            "email_or_username": "nonexistent@example.com",
            "password": "password123"
        }
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
    
    async def test_refresh_token(self, client: AsyncClient, sample_user_data):
        """Test token refresh."""
        # Register and login
        await client.post("/auth/register", json=sample_user_data)
        login_response = await client.post("/auth/login", json={
            "email_or_username": sample_user_data["email"],
            "password": sample_user_data["password"]
        })
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        refresh_data = {"refresh_token": refresh_token}
        response = await client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    async def test_send_login_otp(self, client: AsyncClient, sample_user_data):
        """Test sending OTP for login."""
        # Register user first
        await client.post("/auth/register", json=sample_user_data)
        
        # Send OTP
        response = await client.post(
            f"/auth/send-login-otp?email={sample_user_data['email']}"
        )
        
        assert response.status_code == 200
        assert "OTP sent successfully" in response.json()["message"]
    
    async def test_send_otp_nonexistent_user(self, client: AsyncClient):
        """Test sending OTP for non-existent user."""
        response = await client.post(
            "/auth/send-login-otp?email=nonexistent@example.com"
        )
        
        assert response.status_code == 404
    
    async def test_password_reset_request(self, client: AsyncClient, sample_user_data):
        """Test password reset request."""
        # Register user first
        await client.post("/auth/register", json=sample_user_data)
        
        # Request password reset
        reset_data = {"email": sample_user_data["email"]}
        response = await client.post("/auth/request-password-reset", json=reset_data)
        
        assert response.status_code == 200
        assert "reset token" in response.json()["message"]
    
    async def test_logout(self, client: AsyncClient):
        """Test logout endpoint."""
        response = await client.post("/auth/logout")
        
        assert response.status_code == 200
        assert "Logged out successfully" in response.json()["message"]


@pytest.mark.asyncio 
class TestAuthService:
    """Test authentication service methods."""
    
    async def test_register_user_service(self, db_session: AsyncSession, sample_user_data):
        """Test user registration service method."""
        from app.schemas.user_schemas import UserCreate
        
        user_create = UserCreate(**sample_user_data)
        user = await auth_service.register_user(db_session, user_create)
        
        assert user.email == sample_user_data["email"]
        assert user.username == sample_user_data["username"]
        assert user.first_name == sample_user_data["first_name"]
        assert user.id is not None
    
    async def test_authenticate_user_service(self, db_session: AsyncSession, sample_user_data):
        """Test user authentication service method."""
        from app.schemas.user_schemas import UserCreate, UserLogin
        
        # Register user first
        user_create = UserCreate(**sample_user_data)
        await auth_service.register_user(db_session, user_create)
        
        # Authenticate user
        login_data = UserLogin(
            email_or_username=sample_user_data["email"],
            password=sample_user_data["password"]
        )
        authenticated_user = await auth_service.authenticate_user(db_session, login_data)
        
        assert authenticated_user is not None
        assert authenticated_user.email == sample_user_data["email"]
    
    async def test_authenticate_invalid_user(self, db_session: AsyncSession, sample_user_data):
        """Test authentication with invalid credentials."""
        from app.schemas.user_schemas import UserLogin
        
        login_data = UserLogin(
            email_or_username="nonexistent@example.com",
            password="wrongpassword"
        )
        authenticated_user = await auth_service.authenticate_user(db_session, login_data)
        
        assert authenticated_user is None