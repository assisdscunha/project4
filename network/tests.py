import json
from django.test import Client, TestCase

from network.models import Posts, User

# Create your tests here.


class SharePostTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teste", password="123456")
        self.client = Client()
        self.client.login(username="teste", password="123456")

    def test_post_creation(self):
        post_body = "Post teste"
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
