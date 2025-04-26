window.onpopstate = function (event) {
  if (event.state && event.state.dataPath) {
    navigateTo(event.state.uiPath, event.state.dataPath, false);
  } else {
    loadURL(window.location.pathname);
  }
};

function historyPush(uiPath, dataPath) {
  if (window.location.pathname !== uiPath) {
    history.pushState({ uiPath, dataPath }, "", uiPath);
  }
}

function navigateTo(uiPath, dataPath, pushHistory = true) {
  console.log("Navigate to: ", uiPath);
  console.log("API Path: ", dataPath);
  if (pushHistory) {
    historyPush(uiPath, dataPath);
  }
  loadPosts(dataPath);
}

function loadURL(path) {
  if (path.startsWith("/profile/")) {
    const username = decodeURIComponent(path.replace("/profile/", ""));
    navigateTo(`/profile/${username}`, `/posts/profile/${username}`);
  } else if (path === "/following") {
    navigateTo("/following", "/posts/following");
  } else if (path === "/all" || path === "/") {
    navigateTo("/all", "/posts/all");
  } else {
    // If the URL is not recognized, it will redirect to the home page
    navigateTo("/all", "/posts/all");
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const usernameLink = document.querySelector("#username-link");
  if (usernameLink) {
    usernameLink.addEventListener("click", () => {
      const username = usernameLink.textContent.trim();
      console.log("Navigating..");
      navigateTo(`/profile/${username}`, `/posts/profile/${username}`);
      console.log("Done!");
    });
  }
  document.querySelector("#allposts-link").addEventListener("click", () => {
    navigateTo("/all", "/posts/all");
  });
  const followingLink = document.querySelector("#following-link");
  if (followingLink) {
    followingLink.addEventListener("click", () => {
      navigateTo("/following", "/posts/following");
    });
  }
  const form = document.querySelector("#new-post-form");
  if (form) {
    form.onsubmit = insertNewPost;
  }
  const path = window.location.pathname;

  loadURL(path);
});

function loadPosts(page_name) {
  const postsContainer = document.querySelector("#posts-view");
  postsContainer.innerHTML = "";
  // Display only the div of ID posts-view
  postsContainer.style.display = "block";
  document.querySelector("#following-view").style.display = "none";
  document.querySelector("#profile-view").style.display = "none";

  fetch(page_name)
    .then((response) => response.json())
    .then((data) => {
      document.querySelector(
        "#view-title"
      ).innerHTML = `<h3>${data["page_name"]}</h3>`;
      data["data"].forEach((post) => {
        const postElement = document.createElement("div");
        postElement.classList.add("post-element", "card");
        console.log(post.liked);
        const heartClass = post.liked ? "bi-heart-fill" : "bi-heart";
        const heartStyleColor = post.liked ? "color:red" : "color:";
        postElement.innerHTML = `
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <h5 class="card-title mb-0" style="cursor: pointer">${post.user}</h5>
            <small class="text-muted">${post.timestamp}</small>
          </div>
          <p class="card-text">${post.body}</p>
          <div class="d-flex align-items-center">
            <span class="like-count mr-2">${post.likes}</span>
            <i class="bi ${heartClass} like-icon" style="${heartStyleColor}"></i>
          </div>
        </div>`;
        postElement
          .querySelector(".card-title")
          .addEventListener("click", () => {
            navigateTo(`/profile/${post.user}`, `/posts/profile/${post.user}`);
          });
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
    })
    .catch((error) => {
      console.error("Error loading posts:", error);
      postsContainer.innerHTML =
        "<p>Failed to load posts. Please try again later.</p>";
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
      document.querySelector("#post-body").value = "";
      navigateTo("/all", "/posts/all");
    })
    .catch((error) => {
      console.error("Erro ao criar o post:", error);
    });
  return false;
}
