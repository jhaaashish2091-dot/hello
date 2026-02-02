function confirmDelete(postId){
    if(confirm("Are you sure you want to delete this post?")){
        window.location.href = "/delete_post/" + postId;
    }
}
