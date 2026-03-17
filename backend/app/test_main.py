import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestAuthentication:
    """Test user authentication endpoints"""

    def test_register_success(self):
        """Test successful user registration"""
        response = client.post(
            "/register",
            json={"email": "test@example.com", "password": "testpass123"}
        )
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"

    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        client.post(
            "/register",
            json={"email": "duplicate@example.com", "password": "pass123"}
        )
        response = client.post(
            "/register",
            json={"email": "duplicate@example.com", "password": "pass123"}
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_login_success(self):
        """Test successful login"""
        client.post(
            "/register",
            json={"email": "login@example.com", "password": "pass123"}
        )
        response = client.post(
            "/login",
            data={"username": "login@example.com", "password": "pass123"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        client.post(
            "/register",
            json={"email": "user@example.com", "password": "pass123"}
        )
        response = client.post(
            "/login",
            data={"username": "user@example.com", "password": "wrongpass"}
        )
        assert response.status_code == 401
        assert "Incorrect" in response.json()["detail"]


class TestTaskManagement:
    """Test task CRUD operations"""

    @pytest.fixture
    def auth_token(self):
        """Create a test user and return auth token"""
        client.post(
            "/register",
            json={"email": "taskuser@example.com", "password": "pass123"}
        )
        response = client.post(
            "/login",
            data={"username": "taskuser@example.com", "password": "pass123"}
        )
        return response.json()["access_token"]

    @pytest.fixture
    def auth_headers(self, auth_token):
        """Create authorization headers"""
        return {"Authorization": f"Bearer {auth_token}"}

    def test_create_task(self, auth_headers):
        """Test creating a new task"""
        response = client.post(
            "/tasks",
            headers=auth_headers,
            json={"title": "Test Task", "description": "A test task"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Test Task"
        assert response.json()["completed"] is False

    def test_get_all_tasks(self, auth_headers):
        """Test retrieving all user tasks"""
        # Create a task
        client.post(
            "/tasks",
            headers=auth_headers,
            json={"title": "Task 1"}
        )
        # Get all tasks
        response = client.get("/tasks", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

    def test_get_task_by_id(self, auth_headers):
        """Test retrieving a specific task"""
        create_response = client.post(
            "/tasks",
            headers=auth_headers,
            json={"title": "Task To Fetch"}
        )
        task_id = create_response.json()["id"]
        response = client.get(f"/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["title"] == "Task To Fetch"

    def test_update_task(self, auth_headers):
        """Test updating a task"""
        create_response = client.post(
            "/tasks",
            headers=auth_headers,
            json={"title": "Task To Update"}
        )
        task_id = create_response.json()["id"]
        response = client.put(
            f"/tasks/{task_id}",
            headers=auth_headers,
            json={"completed": True, "title": "Updated Task"}
        )
        assert response.status_code == 200
        assert response.json()["completed"] is True
        assert response.json()["title"] == "Updated Task"

    def test_delete_task(self, auth_headers):
        """Test deleting a task"""
        create_response = client.post(
            "/tasks",
            headers=auth_headers,
            json={"title": "Task To Delete"}
        )
        task_id = create_response.json()["id"]
        response = client.delete(f"/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

    def test_get_completed_tasks(self, auth_headers):
        """Test filtering tasks by completion status"""
        # Create a completed task
        client.post(
            "/tasks",
            headers=auth_headers,
            json={"title": "Completed", "completed": True}
        )
        # Get completed tasks
        response = client.get("/tasks?completed=true", headers=auth_headers)
        assert response.status_code == 200

    def test_task_not_found(self, auth_headers):
        """Test accessing non-existent task"""
        response = client.get("/tasks/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_unauthorized_access(self):
        """Test accessing protected endpoint without token"""
        response = client.get("/tasks")
        assert response.status_code == 403

    def test_user_isolation(self, auth_headers):
        """Test that users can only see their own tasks"""
        # Create a task as first user
        client.post(
            "/tasks",
            headers=auth_headers,
            json={"title": "First User Task"}
        )
        # Register and login as second user
        client.post(
            "/register",
            json={"email": "user2@example.com", "password": "pass123"}
        )
        response2 = client.post(
            "/login",
            data={"username": "user2@example.com", "password": "pass123"}
        )
        headers2 = {"Authorization": f"Bearer {response2.json()['access_token']}"}

        # Second user should not see first user's tasks
        response = client.get("/tasks", headers=headers2)
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 0  # Second user has no tasks


class TestPagination:
    """Test task pagination"""

    @pytest.fixture
    def auth_token(self):
        """Create a test user"""
        client.post(
            "/register",
            json={"email": "paguser@example.com", "password": "pass123"}
        )
        response = client.post(
            "/login",
            data={"username": "paguser@example.com", "password": "pass123"}
        )
        return response.json()["access_token"]

    def test_pagination_default(self, auth_token):
        """Test default pagination"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/tasks", headers=headers)
        assert response.status_code == 200

    def test_pagination_with_limit(self, auth_token):
        """Test pagination with limit parameter"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        # Create multiple tasks
        for i in range(5):
            client.post(
                "/tasks",
                headers=headers,
                json={"title": f"Task {i}"}
            )
        response = client.get("/tasks?limit=2", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) <= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)

def get_test_user():
    user_data = {"email": "test@example.com", "password": "testpass123"}
    response = client.post("/register", json=user_data)
    assert response.status_code == 200
    login_data = {"username": user_data["email"], "password": user_data["password"]}
    response = client.post("/login", data=login_data)
    assert response.status_code == 200
    return user_data, response.json()["access_token"]

def test_register_user():
    response = client.post("/register", json={"email": "new@example.com", "password": "pass123"})
    assert response.status_code == 200

def test_register_duplicate_user():
    client.post("/register", json={"email": "dup@example.com", "password": "pass123"})
    response = client.post("/register", json={"email": "dup@example.com", "password": "pass456"})
    assert response.status_code == 400

def test_create_task():
    _, token = get_test_user()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/tasks",
        json={"title": "Test Task", "description": "Test desc"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"

def test_get_tasks():
    _, token = get_test_user()
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/tasks", json={"title": "Task1"}, headers=headers)
    response = client.get("/tasks", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_get_own_tasks_only():
    # Create user1
    _, token1 = get_test_user()
    headers1 = {"Authorization": f"Bearer {token1}"}
    client.post("/tasks", json={"title": "User1 Task"}, headers=headers1)
    
    # Create user2
    client.post("/register", json={"email": "user2@example.com", "password": "pass123"})
    login_data2 = {"username": "user2@example.com", "password": "pass123"}
    response2 = client.post("/login", data=login_data2)
    token2 = response2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    client.post("/tasks", json={"title": "User2 Task"}, headers=headers2)
    
    # User1 should not see User2 tasks
    response = client.get("/tasks", headers=headers1)
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "User1 Task"
