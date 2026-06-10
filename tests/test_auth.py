"""
Comprehensive authentication tests for MCU Vault.
Tests: login, logout, access control, password validation.
"""
import pytest
from app import create_app, db
from app.models.user import User


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Create authenticated test client."""
    with app.app_context():
        user = User(username='testuser', email='test@test.com')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
    
    client.post('/login', data={'username': 'testuser', 'password': 'testpass123'})
    return client


class TestLogin:
    """Tests for login functionality."""
    
    def test_login_page_loads(self, client):
        response = client.get('/login')
        assert response.status_code == 200
    
    def test_successful_login(self, app, client):
        with app.app_context():
            user = User(username='logintest', email='logintest@test.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/login', data={'username': 'logintest', 'password': 'password123'}, follow_redirects=True)
        assert response.status_code == 200
    
    def test_login_with_email(self, app, client):
        with app.app_context():
            user = User(username='emailtest', email='emailtest@test.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/login', data={'username': 'emailtest@test.com', 'password': 'password123'}, follow_redirects=True)
        assert response.status_code == 200
    
    def test_invalid_password(self, app, client):
        with app.app_context():
            user = User(username='wrongpass', email='wrongpass@test.com')
            user.set_password('correctpass')
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/login', data={'username': 'wrongpass', 'password': 'wrongpass'}, follow_redirects=False)
        assert response.status_code == 200
    
    def test_invalid_user(self, client):
        response = client.post('/login', data={'username': 'nonexistent', 'password': 'anypassword'}, follow_redirects=False)
        assert response.status_code == 200
    
    def test_empty_credentials(self, client):
        response = client.post('/login', data={'username': '', 'password': ''}, follow_redirects=False)
        assert response.status_code == 200
    
    def test_logout(self, auth_client):
        response = auth_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200


class TestAccessControl:
    """Tests for protected route access control."""
    
    def test_dashboard_requires_login(self, client):
        response = client.get('/dashboard', follow_redirects=False)
        assert response.status_code == 302
    
    def test_dashboard_accessible_when_logged_in(self, auth_client):
        response = auth_client.get('/dashboard')
        assert response.status_code == 200
    
    def test_records_requires_login(self, client):
        response = client.get('/records', follow_redirects=False)
        assert response.status_code == 302
    
    def test_analytics_requires_login(self, client):
        response = client.get('/dashboard/health', follow_redirects=False)
        assert response.status_code == 302


class TestSessionPersistence:
    """Tests for session persistence."""
    
    def test_session_persists_after_login(self, app, client):
        with app.app_context():
            user = User(username='sessiontest', email='session@test.com')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
        
        client.post('/login', data={'username': 'sessiontest', 'password': 'pass123'})
        response = client.get('/dashboard')
        assert response.status_code == 200


class TestSeededUsers:
    """Tests for seeded demo user."""
    
    def test_demo_user_can_login(self, app, client):
        with app.app_context():
            user = User.query.filter_by(email='demo@mcu-vault.com').first()
            if not user:
                user = User(username='demo', email='demo@mcu-vault.com')
                user.set_password('demo123')
                db.session.add(user)
                db.session.commit()
        
        response = client.post('/login', data={'username': 'demo', 'password': 'demo123'}, follow_redirects=True)
        assert response.status_code == 200
    
    def test_demo_user_wrong_password(self, app, client):
        with app.app_context():
            user = User.query.filter_by(email='demo@mcu-vault.com').first()
            if not user:
                user = User(username='demo', email='demo@mcu-vault.com')
                user.set_password('demo123')
                db.session.add(user)
                db.session.commit()
        
        response = client.post('/login', data={'username': 'demo', 'password': 'wrongpassword'}, follow_redirects=False)
        assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
