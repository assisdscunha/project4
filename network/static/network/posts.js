document.addEventListener("DOMContentLoaded", function () {
  const usernameLink = document.querySelector("#username-link");
  if (usernameLink) {
    usernameLink.addEventListener("click", () => loadPosts("profile"));
  }
  document
    .querySelector("#allposts-link")
    .addEventListener("click", () => loadPosts("all"));
  const followingLink = document.querySelector("#following-link");
  if (followingLink) {
    followingLink.addEventListener("click", () => loadPosts("following"));
  }
  const form = document.querySelector("#new-post-form");
  if (form) {
    form.onsubmit = insertNewPost;
  }
  loadPosts("all");
});

function loadPosts(page_name) {
  const postsContainer = document.querySelector("#posts-view");
  postsContainer.innerHTML = "";
  // Display only the div of ID posts-view
  postsContainer.style.display = "block";
  document.querySelector("#following-view").style.display = "none";
  document.querySelector("#profile-view").style.display = "none";

  document.querySelector("#view-title").innerHTML = `<h3>Apenas um teste</h3>`;
  fetch(`/posts/${page_name}`)
    .then((response) => response.json())
    .then((data) => {
      data["data"].forEach((post) => {
        const postElement = document.createElement("div");
        postElement.classList.add("post-element", "card");
        console.log(post.liked);
        const heartClass = post.liked ? "bi-heart-fill" : "bi-heart";
        const hearStyleColor = post.liked ? "color:red" : "color:";
        postElement.innerHTML = `
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <h5 class="card-title mb-0">${post.user}</h5>
            <small class="text-muted">${post.timestamp}</small>
          </div>
          <p class="card-text">${post.body}</p>
          <div class="d-flex align-items-center">
            <span class="like-count mr-2">${post.likes}</span>
            <i class="bi ${heartClass} like-icon" style="${hearStyleColor}"></i>
          </div>
        </div>`;

        const likeIcon = postElement.querySelector(".like-icon");
        likeIcon.dataset.liked = post.liked;

        likeIcon.addEventListener("click", () => {
          fetch(`posts/${post.id}`, {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ action: "toggle_like" }),
          })
            .then((response) => response.json())
            .then((data) => {
              const likeCountElement = postElement.querySelector(".like-count");
              likeCountElement.textContent = data.likes;
              likeIcon.dataset.liked = data.liked;
              if (data.liked) {
                console.log("liked");
                likeIcon.classList.remove("bi-heart", "like-icon");
                likeIcon.classList.add("bi-heart-fill", "like-icon");
                likeIcon.style.color = "red";
              } else {
                likeIcon.classList.remove("bi-heart-fill");
                likeIcon.classList.add("bi-heart");
                likeIcon.style.color = "";
              }
            });
        });

        likeIcon.addEventListener("mouseenter", () => {
          if (likeIcon.dataset.liked === "false") {
            likeIcon.classList.add("bi-heart-fill");
            likeIcon.classList.remove("bi-heart");
          }
        });

        likeIcon.addEventListener("mouseleave", () => {
          if (likeIcon.dataset.liked === "false") {
            likeIcon.classList.remove("bi-heart-fill");
            likeIcon.classList.add("bi-heart");
          }
        });

        postsContainer.appendChild(postElement);
      });
    });
}

function insertNewPost() {
  console.log("POST iniciado!");
  fetch("/posts", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      body: document.querySelector("#post-body").value,
      parent: "",
    }),
  })
    .then((result) => {
      console.log(result);
      loadPosts("all");
    })
    .catch((error) => {
      console.error("Erro ao criar o post:", error);
    });
  return false;
}
