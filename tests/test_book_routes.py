import pytest


BOOKS_URL = "/books"


# ---------------------------------------------------------------------------
# GET /books/
# ---------------------------------------------------------------------------

class TestListBooks:
    def test_list_books_returns_empty_when_no_books(self, client, user_token):
        response = client.get(
            f"{BOOKS_URL}/",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_list_books_returns_existing_books(self, client, user_token, sample_book):
        response = client.get(
            f"{BOOKS_URL}/",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == sample_book.title
        assert data[0]["author"] == sample_book.author

    def test_list_books_requires_authentication(self, client):
        response = client.get(f"{BOOKS_URL}/")
        assert response.status_code == 401

    def test_list_books_user_scope_is_sufficient(self, client, user_token, sample_book):
        response = client.get(
            f"{BOOKS_URL}/",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /books/{book_id}
# ---------------------------------------------------------------------------

class TestGetBook:
    def test_get_book_returns_correct_book(self, client, user_token, sample_book):
        response = client.get(
            f"{BOOKS_URL}/{sample_book.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_book.id
        assert data["title"] == sample_book.title
        assert data["author"] == sample_book.author
        assert data["release_year"] == sample_book.release_year

    def test_get_book_returns_404_when_not_found(self, client, user_token):
        response = client.get(
            f"{BOOKS_URL}/999",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Book not found."

    def test_get_book_requires_authentication(self, client, sample_book):
        response = client.get(f"{BOOKS_URL}/{sample_book.id}")
        assert response.status_code == 401

    def test_get_book_user_scope_is_sufficient(self, client, user_token, sample_book):
        response = client.get(
            f"{BOOKS_URL}/{sample_book.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# POST /books/create
# ---------------------------------------------------------------------------

class TestCreateBook:
    def test_create_book_succeeds_with_admin(self, client, admin_token):
        payload = {
            "title": "The Pragmatic Programmer",
            "author": "Andrew Hunt",
            "description": "Your journey to mastery.",
            "release_year": 1999,
        }
        response = client.post(
            f"{BOOKS_URL}/create",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["author"] == payload["author"]
        assert data["release_year"] == payload["release_year"]
        assert "id" in data

    def test_create_book_requires_authentication(self, client):
        payload = {
            "title": "The Pragmatic Programmer",
            "author": "Andrew Hunt",
            "description": "Your journey to mastery.",
            "release_year": 1999,
        }
        response = client.post(f"{BOOKS_URL}/create", json=payload)
        assert response.status_code == 401

    def test_create_book_forbidden_for_user_scope(self, client, user_token):
        payload = {
            "title": "The Pragmatic Programmer",
            "author": "Andrew Hunt",
            "description": "Your journey to mastery.",
            "release_year": 1999,
        }
        response = client.post(
            f"{BOOKS_URL}/create",
            json=payload,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# PUT /books/edit/{book_id}
# ---------------------------------------------------------------------------

class TestUpdateBook:
    def test_update_book_succeeds_with_admin(self, client, admin_token, sample_book):
        payload = {
            "title": "Clean Code — Updated",
            "author": "Robert C. Martin",
            "description": "Updated description.",
            "release_year": 2008,
        }
        response = client.put(
            f"{BOOKS_URL}/edit/{sample_book.id}",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["description"] == payload["description"]

    def test_update_book_returns_404_when_not_found(self, client, admin_token):
        payload = {
            "title": "Ghost Book",
            "author": "Nobody",
            "description": "Does not exist.",
            "release_year": 2000,
        }
        response = client.put(
            f"{BOOKS_URL}/edit/999",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Book not found."

    def test_update_book_requires_authentication(self, client, sample_book):
        payload = {
            "title": "Clean Code — Updated",
            "author": "Robert C. Martin",
            "description": "Updated description.",
            "release_year": 2008,
        }
        response = client.put(f"{BOOKS_URL}/edit/{sample_book.id}", json=payload)
        assert response.status_code == 401

    def test_update_book_forbidden_for_user_scope(self, client, user_token, sample_book):
        payload = {
            "title": "Clean Code — Updated",
            "author": "Robert C. Martin",
            "description": "Updated description.",
            "release_year": 2008,
        }
        response = client.put(
            f"{BOOKS_URL}/edit/{sample_book.id}",
            json=payload,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /books/delete/{book_id}
# ---------------------------------------------------------------------------

class TestDeleteBook:
    def test_delete_book_succeeds_with_admin(self, client, admin_token, sample_book):
        response = client.delete(
            f"{BOOKS_URL}/delete/{sample_book.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Book deleted."

    def test_delete_book_actually_removes_from_db(self, client, admin_token, user_token, sample_book):
        client.delete(
            f"{BOOKS_URL}/delete/{sample_book.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        response = client.get(
            f"{BOOKS_URL}/{sample_book.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 404

    def test_delete_book_returns_404_when_not_found(self, client, admin_token):
        response = client.delete(
            f"{BOOKS_URL}/delete/999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Book not found."

    def test_delete_book_requires_authentication(self, client, sample_book):
        response = client.delete(f"{BOOKS_URL}/delete/{sample_book.id}")
        assert response.status_code == 401

    def test_delete_book_forbidden_for_user_scope(self, client, user_token, sample_book):
        response = client.delete(
            f"{BOOKS_URL}/delete/{sample_book.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403