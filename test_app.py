import asyncio
import time
from httpx import ASGITransport, AsyncClient

import main


async def run_tests():
    print("=" * 60)
    print("  FASTWEB BLOG APP - AUTOMATED TEST SUITE")
    print("=" * 60)

    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Trigger lifespan startup (creates tables)
        async with main.lifespan(main.app):
            # Unique suffix so tests can be run repeatedly without unique constraint errors
            uid = int(time.time()) % 100000
            test_username = f"user_{uid}"
            test_email = f"user_{uid}@example.com"

            # 1. Test Home Route (HTML)
            print("\n[1] Testing GET / (Home Page)...")
            res = await client.get("/")
            assert res.status_code == 200, f"Failed: {res.status_code}"
            assert "text/html" in res.headers.get("content-type", "")
            print("    [PASS] Home page loaded successfully (200 OK)")

            # 2. Test User Creation
            print(f"\n[2] Testing POST /api/users/ (Create User: '{test_username}')...")
            res = await client.post(
                "/api/users/",
                json={"username": test_username, "email": test_email},
            )
            assert res.status_code == 201, f"Failed: {res.status_code} {res.text}"
            user_data = res.json()
            user_id = user_data["id"]
            assert user_data["username"] == test_username
            assert user_data["email"] == test_email
            print(f"    [PASS] User created with ID: {user_id} (201 Created)")

            # 3. Test Duplicate Username Validation
            print("\n[3] Testing POST /api/users/ (Duplicate Username Rejection)...")
            res = await client.post(
                "/api/users/",
                json={"username": test_username, "email": f"other_{uid}@example.com"},
            )
            assert res.status_code == 400, f"Expected 400, got: {res.status_code}"
            print("    [PASS] Duplicate username correctly rejected (400 Bad Request)")

            # 4. Test Get User by ID
            print(f"\n[4] Testing GET /api/users/{user_id}...")
            res = await client.get(f"/api/users/{user_id}")
            assert res.status_code == 200, f"Failed: {res.status_code}"
            assert res.json()["id"] == user_id
            print(f"    [PASS] User {user_id} fetched successfully (200 OK)")

            # 5. Test Update User (PATCH)
            print(f"\n[5] Testing PATCH /api/users/{user_id}...")
            updated_name = f"upd_{uid}"
            res = await client.patch(
                f"/api/users/{user_id}",
                json={"username": updated_name},
            )
            assert res.status_code == 200, f"Failed: {res.status_code}"
            assert res.json()["username"] == updated_name
            print(f"    [PASS] Username updated to '{updated_name}' (200 OK)")

            # 6. Test Post Creation
            print(f"\n[6] Testing POST /api/posts (Create Post for User {user_id})...")
            post_payload = {
                "title": f"Test Post {uid}",
                "content": "This is test content written by the automated test suite.",
                "user_id": user_id,
            }
            res = await client.post("/api/posts", json=post_payload)
            assert res.status_code == 201, f"Failed: {res.status_code} {res.text}"
            post_data = res.json()
            post_id = post_data["id"]
            assert post_data["author"]["id"] == user_id
            assert post_data["author"]["username"] == updated_name
            print(f"    [PASS] Post created with ID: {post_id}, Author: '{updated_name}' (201 Created)")

            # 7. Test Get All Posts (API)
            print("\n[7] Testing GET /api/posts/...")
            res = await client.get("/api/posts/")
            assert res.status_code == 200, f"Failed: {res.status_code}"
            posts = res.json()
            assert any(p["id"] == post_id for p in posts)
            print(f"    [PASS] Post list retrieved (total: {len(posts)}) (200 OK)")

            # 8. Test Get Single Post (API)
            print(f"\n[8] Testing GET /api/posts/{post_id}...")
            res = await client.get(f"/api/posts/{post_id}")
            assert res.status_code == 200, f"Failed: {res.status_code}"
            assert res.json()["author"]["username"] == updated_name
            print(f"    [PASS] Single post retrieved with author details (200 OK)")

            # 9. Test HTML Single Post Page
            print(f"\n[9] Testing HTML GET /posts/{post_id}...")
            res = await client.get(f"/posts/{post_id}")
            assert res.status_code == 200, f"Failed: {res.status_code}"
            assert "text/html" in res.headers.get("content-type", "")
            print("    [PASS] HTML post page rendered successfully (200 OK)")

            # 10. Test HTML User Posts Page
            print(f"\n[10] Testing HTML GET /users/{user_id}/posts...")
            res = await client.get(f"/users/{user_id}/posts")
            assert res.status_code == 200, f"Failed: {res.status_code}"
            assert "text/html" in res.headers.get("content-type", "")
            print(f"    [PASS] HTML user posts page rendered successfully (200 OK)")

            # 11. Test Full Post Update (PUT)
            print(f"\n[11] Testing PUT /api/posts/{post_id}...")
            put_payload = {
                "title": f"Updated Title {uid}",
                "content": "Fully updated content.",
                "user_id": user_id,
            }
            res = await client.put(f"/api/posts/{post_id}", json=put_payload)
            assert res.status_code == 200, f"Failed: {res.status_code} {res.text}"
            assert res.json()["title"] == f"Updated Title {uid}"
            print("    [PASS] Post fully updated (200 OK)")

            # 12. Test Partial Post Update (PATCH)
            print(f"\n[12] Testing PATCH /api/posts/{post_id}...")
            patch_payload = {"title": f"Patched Title {uid}"}
            res = await client.patch(f"/api/posts/{post_id}", json=patch_payload)
            assert res.status_code == 200, f"Failed: {res.status_code} {res.text}"
            assert res.json()["title"] == f"Patched Title {uid}"
            print("    [PASS] Post partially updated (200 OK)")

            # 13. Test Delete Post
            print(f"\n[13] Testing DELETE /api/posts/{post_id}...")
            res = await client.delete(f"/api/posts/{post_id}")
            assert res.status_code == 204, f"Failed: {res.status_code}"
            print("    [PASS] Post deleted (204 No Content)")

            # 14. Test Delete User
            print(f"\n[14] Testing DELETE /api/users/{user_id}...")
            res = await client.delete(f"/api/users/{user_id}")
            assert res.status_code == 204, f"Failed: {res.status_code}"
            print("    [PASS] User deleted (204 No Content)")

            # 15. Test API 404 Exception Handler (JSON Response)
            print("\n[15] Testing API 404 Error Handler...")
            res = await client.get("/api/posts/99999999")
            assert res.status_code == 404, f"Expected 404, got: {res.status_code}"
            assert res.headers.get("content-type", "").startswith("application/json")
            print("    [PASS] API 404 returns JSON error format (404 Not Found)")

            # 16. Test Web Page 404 Exception Handler (HTML Response)
            print("\n[16] Testing HTML 404 Error Handler...")
            res = await client.get("/posts/99999999")
            assert res.status_code == 404, f"Expected 404, got: {res.status_code}"
            assert "text/html" in res.headers.get("content-type", "")
            print("    [PASS] Browser 404 renders HTML error template (404 Not Found)")

    print("\n" + "=" * 60)
    print("  ALL 16 TESTS PASSED! APPLICATION IS HEALTHY & ERROR-FREE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_tests())
