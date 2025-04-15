document.addEventListener("DOMContentLoaded", function () {
    loadPosts("teste");
});

function loadPosts(page) {
    const postsContainer = document.querySelector("#posts-view");
    // Display only the div of ID posts-view
    postsContainer.style.display = "block";
    document.querySelector("#following-view").style.display = "none";
    document.querySelector("#profile-view").style.display = "none";

    postsContainer.innerHTML = `<h3>Apenas um teste</h3>`
}
