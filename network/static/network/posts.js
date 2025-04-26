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
  loadPage(dataPath);
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

function loadPage(apiPath) {
  const postsContainer = document.querySelector("#posts-view");
  postsContainer.innerHTML = "";

  // Skeleton loading
  for (let i = 0; i < 5; i++) {
    const skeleton = document.createElement("div");
    skeleton.className = "skeleton";
    postsContainer.appendChild(skeleton);
  }

  postsContainer.style.display = "block";
  document.querySelector("#following-view").style.display = "none";
  document.querySelector("#profile-view").style.display = "none";

  fetch(apiPath)
    .then((response) => response.json())
    .then((data) => {
      postsContainer.innerHTML = "";

      if (apiPath.startsWith("/posts/profile/")) {
        renderProfilePage(data);
      } else if (apiPath === "/posts/following") {
        renderFollowingPage(data);
      } else {
        renderAllPage(data);
      }

      renderPosts(data.data);
    })
    .catch((error) => {
      console.error("Error loading page:", error);
      postsContainer.innerHTML =
        "<p>Failed to load posts. Please try again later.</p>";
    });
}

function renderProfilePage(data) {
  const viewTitle = document.querySelector("#view-title");
  const username = decodeURIComponent(
    window.location.pathname.replace("/profile/", "")
  );
  const loggedUser = document
    .querySelector("#username-link")
    ?.textContent.trim();
  const isFollowing = data.followers.includes(loggedUser);

  let followButtonHTML = "";
  if (username !== loggedUser) {
    followButtonHTML = `
      <button id="follow-button" class="btn btn-primary btn-sm" data-following="${isFollowing}">
        ${isFollowing ? "Unfollow" : "Follow"}
      </button>
    `;
  }

  viewTitle.innerHTML = `
    <div class="profile-header d-flex align-items-center justify-content-between">
      <div class="profile-info">
        <div class="d-flex flex-row">
          <h3 class="mb-0 mr-3">${username}</h3>
          ${followButtonHTML}
        </div>
        <small class="text-muted">
          (<span id="followers-count">${data.followers_count}</span> followers, 
          <span id="following-count">${data.following_count}</span> following)
        </small>
      </div>
    </div>
  `;

  if (followButtonHTML) {
    document
      .querySelector("#follow-button")
      .addEventListener("click", () => toggleFollow(username));
  }
}

function renderFollowingPage(data) {
  const viewTitle = document.querySelector("#view-title");
  viewTitle.innerHTML = `<h3>Following Feed</h3>`;
}

function renderAllPage(data) {
  const viewTitle = document.querySelector("#view-title");
  viewTitle.innerHTML = `<h3>Public Feed</h3>`;
}

function renderPosts(postsData) {
  const postsContainer = document.querySelector("#posts-view");

  postsData.forEach((post) => {
    const postElement = document.createElement("div");
    postElement.classList.add("post-element", "card");
    const heartClass = post.liked ? "bi-heart-fill" : "bi-heart";
    const heartStyleColor = post.liked ? "color:red" : "";
    const isPostUser = post.user === currentUser;

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
          ${
            isPostUser
              ? '<i class="bi bi-pencil-square ml-2" style="cursor: pointer"></i>'
              : ""
          }
        </div>
      </div>
    `;

    postElement.querySelector(".card-title").addEventListener("click", () => {
      navigateTo(`/profile/${post.user}`, `/posts/profile/${post.user}`);
    });

    const likeIcon = postElement.querySelector(".like-icon");
    const editIcon = postElement.querySelector(".bi.bi-pencil-square");
    likeIcon.dataset.liked = post.liked;

    likeIcon.addEventListener("click", () =>
      toggleLike(post.id, postElement, likeIcon)
    );
    likeIcon.addEventListener("mouseenter", () => {
      if (
        likeIcon.dataset.liked === "false" &&
        !likeIcon.classList.contains("bi-heart-fill")
      ) {
        likeIcon.classList.add("bi-heart-fill");
        likeIcon.classList.remove("bi-heart");
      }
    });
    likeIcon.addEventListener("mouseleave", () => {
      if (
        likeIcon.dataset.liked === "false" &&
        !likeIcon.classList.contains("bi-heart")
      ) {
        likeIcon.classList.remove("bi-heart-fill");
        likeIcon.classList.add("bi-heart");
      }
    });

    if (editIcon) {
      editIcon.addEventListener("click", () =>
        toggleEdit(post.id, postElement)
      );
    }

    postsContainer.appendChild(postElement);
  });
}

function toggleEdit(id, element) {
  const postBody = element.querySelector(".card-text");
  const originalText = postBody.textContent;

  const textArea = document.createElement("textarea");
  textArea.className = "form-control";
  textArea.value = originalText;
  postBody.replaceWith(textArea);

  const saveButton = document.createElement("button");
  saveButton.className = "btn btn-primary btn-sm mb-2";
  saveButton.textContent = "Save";

  const cancelButton = document.createElement("button");
  cancelButton.className = "btn btn-secondary btn-sm ml-2 mb-2";
  cancelButton.textContent = "Cancel";

  const buttonContainer = document.createElement("div");
  buttonContainer.className = "d-flex justify-content-end mt-2 mb-2";
  buttonContainer.appendChild(saveButton);
  buttonContainer.appendChild(cancelButton);

  textArea.insertAdjacentElement("afterend", buttonContainer);

  saveButton.addEventListener("click", () => {
    const updatedText = textArea.value.trim();
    if (updatedText === originalText || updatedText === "") {
      showToast("⚠️ No changes were made to the post.");
      cancelEdit();
      return;
    }

    fetch(`/posts/${id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ body: updatedText }),
    })
      .then((response) => {
        if (response.status === 204) {
          // Sucesso, mas sem conteúdo
          textArea.replaceWith(postBody);
          postBody.textContent = updatedText;
          buttonContainer.remove();
          showToast("✅ Post updated successfully!");
          return;
        }
        if (!response.ok) throw new Error("Failed to update post");
        return;
      })
      .catch((e) => {
        console.error("Error updating post: ", e);
        showToast("⚠️ Failed to update post. Please try again.");
      });
  });

  cancelButton.addEventListener("click", cancelEdit);

  function cancelEdit() {
    textArea.replaceWith(postBody);
    postBody.textContent = originalText;
    buttonContainer.remove();
  }
}

function toggleLike(id, postElement, likeIcon) {
  fetch(`posts/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ action: "toggle_like" }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to toggle like");
      }
      return response.json();
    })
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
    })
    .catch((error) => {
      console.error("Error toggling like:", error);
      showToast("⚠️ Failed to toggle like. Please try again.");
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
      console.error("Error creating post:", error);
    });
  return false;
}

function toggleFollow(username) {
  const button = document.querySelector("#follow-button");
  const followersCountElement = document.querySelector("#followers-count");

  button.disabled = true;
  const originalText = button.textContent;
  button.textContent = "Loading...";

  fetch(`/follow/${username}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({}),
  })
    .then((response) => {
      if (!response.ok) throw new Error("Error (un)following user.");
      return response.json();
    })
    .then((data) => {
      console.log(data.message);

      if (data.action === "unfollowed") {
        button.textContent = "Follow";
        button.dataset.following = "false";
        followersCountElement.textContent = (
          parseInt(followersCountElement.textContent, 10) - 1
        ).toString();
        flashButton(button, "red");
        showToast("Unfollowed!");
      } else {
        button.textContent = "Unfollow";
        button.dataset.following = "true";
        followersCountElement.textContent = (
          parseInt(followersCountElement.textContent, 10) + 1
        ).toString();
        flashButton(button, "green");
        showToast("Followed!");
      }
    })
    .catch((error) => {
      console.error(error);
      showToast("⚠️ Fail to follow/unfollow. Try again.");
      button.textContent = originalText;
    })
    .finally(() => {
      button.disabled = false;
    });
}

function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.style.display = "block";

  setTimeout(() => {
    toast.style.display = "none";
  }, 2000); // Hide after 2 seconds
}

function flashButton(button, color) {
  const originalBg = button.style.backgroundColor;

  button.style.backgroundColor = color;
  button.style.transition = "background-color 0.3s";

  setTimeout(() => {
    button.style.backgroundColor = originalBg || ""; // back to original state
  }, 500);
}
