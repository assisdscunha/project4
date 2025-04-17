from datetime import datetime
import json
from django.test import Client, TestCase

from network.models import Posts, User


# Create your tests here.
class BaseTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = self.create_user("test")
        self.user2 = self.create_user("second")
        self.login_as(self.user)

    def create_user(self, username, is_active=True):
        return User.objects.create_user(
            username=username, password="123456", is_active=is_active
        )

    def create_post(self, user=None, body="Test post", parent=None, likes=0):
        return Posts.objects.create(
            user=user or self.user, body=body, parent=parent, likes=likes
        )

    def login_as(self, user):
        self.client.logout()
        self.client.login(username=user.username, password="123456")


class PostModelTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.inactive_user = User.objects.create_user(
            username="inactive", password="123456", is_active=False
        )
        self.deleted_user = User.objects.create_user(
            username="deleted", password="123456"
        )

        self.post_active_user = self.create_post(body="1st post")
        self.post_inactive_user = self.create_post(
            user=self.inactive_user, body="2nd post"
        )
        self.post_deleted_user = self.create_post(
            user=self.deleted_user, body="3rd post"
        )
        self.comment = self.create_post(body="A comment", parent=self.post_active_user)

    def test_post_with_active_user(self):
        serialized_post = self.post_active_user.serialize()
        self.assertEqual(serialized_post["user"], "test")

    def test_post_with_inactive_user(self):
        serialized_post = self.post_inactive_user.serialize()
        self.assertEqual(serialized_post["user"], "user removed")

    def test_post_with_deleted_user(self):
        self.deleted_user.delete()
        self.post_deleted_user.refresh_from_db()
        serialized_post = self.post_deleted_user.serialize()
        self.assertEqual(serialized_post["user"], "user removed")

    def test_comment_serialization(self):
        serialized_comment = self.comment.serialize_comments(self.comment)
        self.assertEqual(serialized_comment["body"], "A comment")
        self.assertEqual(serialized_comment["user"], "test")
        self.assertEqual(serialized_comment["likes"], 0)

    def test_comment_with_inactive_user(self):
        self.comment.user = self.inactive_user
        self.comment.save()
        serialized_comment = self.comment.serialize_comments(self.comment)
        self.assertEqual(serialized_comment["user"], "user removed")


class UserModelTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.alice = self.create_user("alice")
        self.bob = self.create_user("bob")
        self.charlie = self.create_user("charlie")

        self.user.following.add(self.alice, self.bob, self.charlie)

    def test_user_followers(self):
        following_usernames = list(
            self.user.following.values_list("username", flat=True)
        )
        expected_usernames = ["alice", "bob", "charlie"]
        self.assertListEqual(sorted(following_usernames), sorted(expected_usernames))

    def test_user_followers_list(self):
        self.assertIn(self.user, self.alice.followers.all())

    def test_user_serialization(self):
        self.alice.following.add(self.user)
        self.assertDictEqual(
            self.user.serialize(),
            {
                "username": "test",
                "followers": ["alice"],
                "following": ["alice", "bob", "charlie"],
            },
        )


class PostByIdEndpointTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.post = self.create_post(body="Just a post.")
        self.comment = self.create_post(
            user=self.user2, body="My comment", parent=self.post
        )

    def test_invalid_post_id(self):
        response = self.client.get("/posts/9999")
        self.assertFalse(Posts.objects.filter(id=9999).exists())
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("error"), "Post cannot be found.")

    def test_get_method(self):
        response = self.client.get(f"/posts/{self.post.id}")
        self.assertDictEqual(response.json(), self.post.serialize())

    def test_put_method_wrong_user(self):
        self.login_as(self.user2)
        response = self.client.put(
            f"/posts/{self.post.id}",
            data=json.dumps({"body": "Just a test!"}),
            content_type="application/json",
        )
        self.post.refresh_from_db()
        self.assertNotEqual(self.post.body, "Just a test!")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json().get("error"), "User post not the same as requested."
        )

    def test_put_method_update_post_body(self):
        response = self.client.put(
            f"/posts/{self.post.id}",
            data=json.dumps({"body": "Just a test!"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 204)
        self.post.refresh_from_db()
        self.assertEqual(self.post.body, "Just a test!")

    def test_put_method_update_comment_body(self):
        self.login_as(self.user2)
        response = self.client.put(
            f"/posts/{self.comment.id}",
            data=json.dumps({"body": "Updated comment", "likes": 10}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 204)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.body, "Updated comment")
        self.assertEqual(self.comment.likes, 10)

    def test_put_method_invalid_keys(self):
        response = self.client.put(
            f"/posts/{self.post.id}",
            data=json.dumps({"invalid": "Should fail"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json().get("error"), "Only 'body' or 'likes' fields are allowed."
        )

    def test_put_method_invalid_json(self):
        response = self.client.put(
            f"/posts/{self.post.id}", data="str", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("error"), "Invalid JSON.")

    def test_post_method_not_allowed(self):
        response = self.client.post(
            f"/posts/{self.post.id}",
            data=json.dumps({"body": "Should fail"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("error"), "GET or PUT request required.")


class SharePostTest(BaseTestCase):
    def test_get_request_not_allowed(self):
        response = self.client.get("/posts")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("error"), "POST request required.")

    def test_put_request_not_allowed(self):
        response = self.client.put("/posts")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("error"), "POST request required.")

    def test_invalid_json_request(self):
        response = self.client.post(
            "/posts",
            data="str",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("error"), "Invalid JSON.")

    def test_post_creation(self):
        body = "Post test"
        response = self.client.post(
            "/posts",
            data=json.dumps({"body": body}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        post = Posts.objects.first()
        self.assertEqual(post.body, body)
        self.assertEqual(post.user, self.user)

    def test_comment_creation(self):
        parent = self.create_post(body="Post original")
        body = "Just a comment"
        response = self.client.post(
            "/posts",
            data=json.dumps({"body": body, "parent": parent.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(parent.comments.count(), 1)
        self.assertEqual(parent.comments.first().body, body)

    def test_post_creation_empty_body(self):
        response = self.client.post(
            "/posts",
            data=json.dumps({"body": ""}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Post body cannot be empty.", response.json().get("error"))

    def test_post_comment_empty_parent(self):
        response = self.client.post(
            "/posts",
            data=json.dumps({"body": "Comment", "parent": 9999}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Post cannot be found.", response.json().get("error"))

class PageTestMixin:
    def assert_valid_response(self, page_name):
        response = self.client.get(f"/posts/{page_name}")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def assert_valid_post_structure(self, post):
        keys = {"body", "likes", "timestamp", "comments", "user"}
        self.assertTrue(keys.issubset(post.keys()))
    
    def assert_posts_validity(self, data, expected_len):
        self.assertIn("posts", data)
        self.assertIsInstance(data["posts"], list)
        self.assertEqual(len(data["posts"]), expected_len)

    def assert_post_order_by_timestamp_desc(self, posts):
        fmt = "%b %d %Y, %I:%M %p"
        timestamps = [datetime.strptime(post["timestamp"], fmt) for post in posts]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))

class GetPageTest(BaseTestCase, PageTestMixin):
    def setUp(self):
        super().setUp()
        self.post1 = self.create_post(body="Post 1")
        self.post2 = self.create_post(body="Post 2")
        self.post3 = self.create_post(body="Post 3", user=self.user2, likes=10)
        self.post3 = self.create_post(body="Post 4", user=self.user2, likes=5)
        self.user.following.add(self.user2)

    def test_put_request_method(self):
        response = self.client.put(
            "/posts/random_page", content_type="/application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("error"), "GET request required.")

    def test_post_request_method(self):
        response = self.client.post(
            "/posts/random_page", content_type="/application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("error"), "GET request required.")
    
    def test_invalid_page(self):
        response = self.client.get("/posts/invalid_name")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json().get("error"), "Page not found.")

    def test_profile_page(self):
        data = self.assert_valid_response("profile")

        self.assertIn("username", data)
        self.assertEqual(data["username"], self.user.username)

        self.assert_posts_validity(data, 2)

        post = data["posts"][0]
        self.assert_valid_post_structure(post)

        self.assertEqual(post["body"], "Post 2")
        self.assertEqual(post["likes"], 0)
        self.assertEqual(post["comments"], [])
        self.assertIsInstance(post["timestamp"], str)
        self.assertEqual(post["user"], "test")

        bodies = [post["body"] for post in data["posts"]]
        self.assertNotIn("Post 3", bodies)
        
        self.assert_post_order_by_timestamp_desc(data["posts"])

    def test_all_page(self):
        data = self.assert_valid_response("all")

        self.assert_posts_validity(data, 4)

        post = data["posts"][0]
        self.assert_valid_post_structure(post)

        self.assertEqual(post["body"], "Post 4")
        self.assertEqual(post["likes"], 5)
        self.assertEqual(post["comments"], [])
        self.assertIsInstance(post["timestamp"], str)
        self.assertEqual(post["user"], "second")

        post = data["posts"][-1]
        self.assert_valid_post_structure(post)

        self.assertEqual(post["body"], "Post 1")
        self.assertEqual(post["likes"], 0)
        self.assertEqual(post["comments"], [])
        self.assertIsInstance(post["timestamp"], str)
        self.assertEqual(post["user"], "test")
        
        self.assert_post_order_by_timestamp_desc(data["posts"])

    def test_following_page(self):
        data = self.assert_valid_response("following")

        self.assert_posts_validity(data, 2)

        post = data["posts"][1]
        self.assert_valid_post_structure(post)

        self.assertEqual(post["body"], "Post 3")
        self.assertEqual(post["likes"], 10)
        self.assertEqual(post["comments"], [])
        self.assertIsInstance(post["timestamp"], str)
        self.assertEqual(post["user"], "second")
        
        self.assert_post_order_by_timestamp_desc(data["posts"])
