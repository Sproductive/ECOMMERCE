document.addEventListener("DOMContentLoaded", function() {
    // use ai in 
    // personalized product recommendations, search, chatbots, virtual shopping assistants, dynamic pricing, fraud detection, and logistics optimization. 
    let search = document.querySelector(".search");
    let search_form = document.querySelector(".search_form");
    search.addEventListener("focus", function(){
        search_form.style.opacity = 1;
        search_form.style.boxShadow = '0 0px 0px black, inset 0 0 0px white';
    });
    // search_button.addEventListener("mouseout", function(){
    //     search_input.style.opacity = '';
    // });
    search.addEventListener("focus", function(){
        document.documentElement.style.setProperty("--nav-opacity", '1');
        document.documentElement.style.setProperty("--nav-transformX", 'scaleX(1)');
        document.documentElement.style.setProperty("--nav-transformY", 'scaleY(1)');
    });
    
    // search_input.addEventListener("mouseover", function(){
        //     search_input.style.background = 'linear-gradient(white, white) padding-box,linear-gradient(darkblue, darkorchid) border-box;';
        //     console.log("hello");
        // });
        search.addEventListener("blur", function(){
        document.documentElement.style.setProperty("--nav-opacity", '0.7');
        document.documentElement.style.setProperty("--nav-transformX", 'scaleX(0.8)');
        document.documentElement.style.setProperty("--nav-transformY", 'scaleY(0.9)');
        search_form.style.boxShadow = '';
        search_form.style.opacity = '';
    });
    // let search_data = "";
    // search_input.addEventListener("keydown", function(){
    //     let prev_search_data = search_data;
    //     search_data = search_input.value;
    //     let prev_len = prev_search_data.length;
    //     let len_now = search_data.length;

    //     if (prev_len < len_now){    
    //         var xhr = new XMLHttpRequest();
    //         xhr.open("POST", '/search_results/', true);
    //         xhr.setRequestHeader('Content-Type', 'application/json');  
    //         xhr.onreadystatechange = function(){
    //             if (xhr.readyState === 4 && xhr.status === 200){
    //                 var search_results = JSON.parse(xhr.responseText)
    //                 console.log("search_results: ", search_results);
    //             } 
    //         }   
    //         let char_length = len_now - prev_len;
    //         xhr.send(JSON.stringify({new: true, char:search_data.substring(prev_len, len_now - 1), length,  letter: search_data[prev_len]}));
            
    //     }
    //     else if (prev_len > len_now){
    //         var xhr = new XMLHttpRequest();
    //         xhr.open("POST", '/search_results/', true);
    //         xhr.setRequestHeader('Content-Type', 'application/json');  
    //         xhr.onreadystatechange = function(){
    //             if (xhr.readyState === 4 && xhr.status === 200){
    //                 var search_results = JSON.parse(xhr.responseText)
    //                 console.log("search_results: ", search_results);
    //             } 
    //         }   
    //         xhr.send(JSON.stringify({new: false, letter: prev_len - len_now}));
    //         // It will take letters one by one and check for the words with it and then award poinst on the basis of how close the previous word is to the one entered then i will at last find how much distance is the last letter of the title with the last letter of the string we found and similiarly for the fist letter and assign points based on that then i will show results based on the ranking of the things 
    //     } 
    // })
    // function getCSRF(time_limited_token){
    //     xhr = XMLHttpRequest()

    // }
    // Function to send a message to other tabs
    
    const broadcastChannel = new BroadcastChannel('Auction');
    broadcastChannel.onmessage = handleReceivedMessage;

if (window.reload){
    window.reload = false;
    sendMessage('reload');
}
    function sendMessage(message) {
        console.log("message: ", message);
        broadcastChannel.postMessage(message);
        // broadcastChannel.close();
    }

    function handleReceivedMessage(event) {
        console.log('Received: ', event.data);
        if (event.data == 'reload') {
            location.reload();
        }
    }
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;    
    var deleteButtons = document.querySelectorAll(".notification_delete_btn");
    console.log('deleteButtons: ', deleteButtons);
    deleteButtons.forEach(function(button){
        button.addEventListener("click", function(){
            console.log('delete_notification_clicked');
            var CardId = button.getAttribute("data-notification-id");
            var xhr = new XMLHttpRequest();
            xhr.open("POST", '/delete_notifications/' + CardId + "/", true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.setRequestHeader('X-CSRFToken', csrftoken);
            xhr.onreadystatechange = function(){
                if (xhr.readyState === 4 ){
                    if (xhr.status === 200){
                        var data = JSON.parse(xhr.responseText);
                    }
                    if (data.success){
                        console.log("SUCCESSFULLY DELETED CARD ");
                        var notification_card = button.closest(".notification_card");
                        remove_notification(notification_card)
                    }
                    else{
                        console.log("FAILED TO DELETE CARD ");
                    }
                }
            };
            xhr.send();
        });
    });
    function remove_notification(notification_card){
        notification_card.style.transition = "opacity 0.5s ease";
        notification_card.style.opacity = "0";
        setTimeout(function(){
            notification_card.remove()
        }, 500); 
    }
    var unseenNotifications = document.querySelectorAll(".unseen_notification");
    const seen_notifications = [];
    unseenNotifications.forEach(function(unseen_notification){
        console.log("helloqol");
        var rect = unseen_notification.getBoundingClientRect();
        if (rect.top >= 0 && rect.left >= 0 && rect.right <= (window.innerWidth || document.documentElement.clientWidth) && rect.bottom <= (window.innerHeight + 50 || document.documentElement.clientHeight + 50)){
            notification_id = unseen_notification.getAttribute("data-notification-id");
            seen_notifications.push(notification_id);
        }
    });
    if (seen_notifications.length > 0){
        var xhr = new XMLHttpRequest();
        xhr.open("POST", '/seen_notifications/', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.setRequestHeader('X-CSRFToken', csrftoken);
        xhr.onreadystatechange = function(){
            if (xhr.readyState === 4 ){
                if (xhr.status === 200){
                    var data = JSON.parse(xhr.responseText);
                }
                if (data.success){
                    console.log("SUCCESSFULLY SEEN NOTIFICATIONS");
                }
                else{
                    console.log("FAILED TO SEEN NOTIFICATIONS");
                }
            }
        };
        xhr.send(JSON.stringify({ids: seen_notifications}));
    }
});