from httpx import AsyncClient
import asyncio


BASE_URL = "http://localhost:8000"  # Replace with your actual base URL


async def main():
    async with AsyncClient(base_url=BASE_URL) as ac:
        # Step 0: Create a user
        user_data = {
            "username": "testuser",
            "email": "test-user-123@example.com",
            "full_name": "Test User",
            "password": "testpassword",
        }
        response = await ac.post("/users", json=user_data)
        assert response.status_code == 201
        assert response.json()["username"] == user_data["username"]

        # Step 1: Obtain a token
        login_data = {"username": "testuser", "password": "testpassword"}
        response = await ac.post("/token", data=login_data)
        assert response.status_code == 201
        token = response.json().get("access_token")
        assert token is not None

        headers = {"Authorization": f"Bearer {token}"}

        # Step 2: Create an item
        item_data = {
            "title": "Test Item",
            "description": "A test item",
            "price": 10.99,
            "tax": 0.5,
            "region": "CA",
            "latitude": 34.0522,
            "longitude": -118.2437,
        }
        response = await ac.post("/items", json=item_data, headers=headers)
        assert response.status_code == 201
        item_id = response.json().get("id")
        assert item_id is not None

        # Step 3: Read the created item
        response = await ac.get(f"/items/{item_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["title"] == item_data["title"]

        # Step 4: Update the item
        updated_item_data = item_data.copy()
        updated_item_data["title"] = "Updated Test Item"
        response = await ac.put(
            f"/items/{item_id}", json=updated_item_data, headers=headers
        )
        assert response.status_code == 202
        assert response.json()["title"] == "Updated Test Item"

        # Step 5: Delete the item
        response = await ac.delete(f"/items/{item_id}", headers=headers)
        assert response.status_code == 204
        assert response.json()["status"] == "success"

        # Step 6: Verify the item is deleted
        response = await ac.get(f"/items/{item_id}", headers=headers)
        assert response.status_code == 404


if __name__ == "__main__":
    asyncio.run(main())
