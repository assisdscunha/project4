import json
from django.test import Client, TestCase

from network.models import Posts, User


# Create your tests here.
class PostModelTest(TestCase):
    def setUp(self):
        self.active_user = User.objects.create_user(
            username="active_user", password="123456"
        )
        self.inactive_user = User.objects.create_user(
            username="inactive_user", password="123456", is_active=False
        )
        self.deleted_user = User.objects.create_user(
            username="deleted_user", password="123456"
        )

        self.post_active_user = Posts.objects.create(
            user=self.active_user, body="1st post"
        )
        self.post_inactive_user = Posts.objects.create(
            user=self.inactive_user, body="2nd post"
        )
        self.post_deleted_user = Posts.objects.create(
            user=self.deleted_user, body="3rd post"
        )

        self.comment = Posts.objects.create(
            user=self.active_user, body="A comment", parent=self.post_active_user
        )

    def test_post_with_active_user(self):
        serialized_post = self.post_active_user.serialize()
        self.assertEqual(serialized_post["user"], "active_user")

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
        self.assertEqual(serialized_comment["user"], "active_user")
        self.assertEqual(serialized_comment["likes"], 0)

    def test_comment_with_inactive_user(self):
        self.comment.user = self.inactive_user
        self.comment.save()

        serialized_comment = self.comment.serialize_comments(self.comment)
        self.assertEqual(serialized_comment["user"], "user removed")


class PostByIdEndpointTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(username="test", password="123456")
        self.post = Posts.objects.create(user=self.user, body="Just a post.")

        self.user2 = User.objects.create_user(username="2nd test", password="123456")
        self.comment = Posts.objects.create(
            user=self.user2, body="My comment", parent=self.post
        )

    def test_invalid_post_id(self):
        self.client.logout()
        self.client.login(username="test", password="123456")

        response = self.client.get(
            "/posts/9999", content_type="text/html; charset=utf-8"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("error"), "Post cannot be found.")

    def test_get_method(self):
        self.client.logout()
        self.client.login(username="test", password="123456")

        response = self.client.get(f"/posts/{self.post.id}")
        serialized_post = self.post.serialize()
        self.assertDictEqual(response.json(), serialized_post)

    def test_put_method_wrong_user(self):
        self.client.logout()
        self.client.login(username="2nd test", password="123456")

        response = self.client.put(
            f"/posts/{self.post.id}",
            data=json.dumps({"body": "Just a test!"}),
            content_type="application/json",
        )
        self.assertEqual(
            response.json().get("error"),
            "User post not the same as requested.",
        )
        self.assertEqual(response.status_code, 401)

    def test_put_method_update_post_body(self):
        self.client.logout()
        self.client.login(username="test", password="123456")

        response = self.client.put(
            f"/posts/{self.post.id}",
            data=json.dumps({"body": "Just a test!"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 204)
        
        self.post.refresh_from_db()
        self.assertEqual(self.post.body, "Just a test!")

    def test_put_method_update_comment_body(self):
        self.client.logout()
        self.client.login(username="2nd test", password="123456")

        response = self.client.put(
            f"/posts/{self.comment.id}",
            data=json.dumps({"body": "Just another test!", "likes": 10}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 204)
        
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.body, "Just another test!")
        self.assertEqual(self.comment.likes, 10)

    def test_put_method_invalid_keys(self):
        self.client.logout()
        self.client.login(username="test", password="123456")

        response = self.client.put(
            f"/posts/{self.post.id}",
            data=json.dumps({"one key": "Just a key test!"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json().get("error"), "Only 'body' or 'likes' fields are allowed."
        )

    def test_post_method(self):
        self.client.logout()
        self.client.login(username="test", password="123456")

        response = self.client.post(
            f"/posts/{self.post.id}",
            data=json.dumps({"one key": "Just a key test!"}),
            content_type="application/json",
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("error"), "GET or PUT request required.")

class SharePostTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test", password="123456")
        self.client = Client()
        self.client.login(username="test", password="123456")

    def test_post_creation(self):
        post_body = "Post test"
        response = self.client.post(
            "/posts",
            data=json.dumps({"body": post_body}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Posts.objects.count(), 1)
        post = Posts.objects.first()
        self.assertEqual(post.body, post_body)

    def test_comment_creation(self):
        post = Posts.objects.create(user=self.user, body="Post original")
        comment = "Just a comment"
        response = self.client.post(
            "/posts",
            data=json.dumps(
                {"body": comment, "parent": post.id},
            ),
            content_type="application/json",
        )
        post_created = Posts.objects.get(parent=post)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(post_created.body, comment)

    def test_post_creation_empty_body(self):
        response = self.client.post(
            "/posts", data=json.dumps({"body": ""}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Post body cannot be empty.", response.json().get("error"))

    def test_post_comment_empty_parent(self):
        invalid_id = 51
        response = self.client.post(
            "/posts",
            data=json.dumps({"body": "Just a random comment.", "parent": invalid_id}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Post cannot be found.", response.json().get("error"))
