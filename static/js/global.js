window.onload = () => {

const attachments = document.getElementsByClassName("attachment");

Array.prototype.slice.call(attachments).forEach(attachment => {
    attachment.addEventListener("click", e => {
        const previous = e.target.src;
        e.target.src = e.target.dataset.attachment;
        e.target.dataset.attachment = previous;
    });
});

const topic_divs = document.getElementsByClassName("topic-container");

Array.prototype.slice.call(topic_divs).forEach(topic_div => {
    const topic_number_inputs = topic_div.getElementsByClassName("topic-number-input");
    
    Array.prototype.slice.call(topic_number_inputs).forEach(input => {
        input.value = topic_div.dataset.number;
    })
});

const reply_form_divs = document.getElementsByClassName("reply-form-container");

Array.prototype.slice.call(reply_form_divs).forEach(form_div => {
    const textarea = form_div.getElementsByClassName("post-form")[0];
    textarea.value = ">>" + form_div.dataset.number;
});

const post_numbers = document.getElementsByClassName("post-number");

Array.prototype.slice.call(post_numbers).forEach(post_number => {
    post_number.addEventListener("click", e => {
        const reply_form_div = document.getElementById(e.target.name + "-form");
        if (reply_form_div.style.visibility == "visible") {
            reply_form_div.style.visibility = "hidden";
            reply_form_div.style.display = "none"
        }
        else {
            reply_form_div.style.visibility = "visible";
            reply_form_div.style.display = "block"
        }
    });

    const reply_form_div = document.getElementById(post_number.name + "-form");
    var secret_field = reply_form_div.getElementsByClassName("post_number")[0];
    secret_field.value = post_number.name;

    const delete_form_div = document.getElementById(post_number.name + "-delete-form");
    secret_field = delete_form_div.getElementsByClassName("deletion-form-secret")[0];
    secret_field.value = post_number.name;

    const ban_form_div = document.getElementById(post_number.name + "-ban-form");
    if (ban_form_div != null) {
        const hidden_field = ban_form_div.getElementsByClassName('ban-form')[0];
        hidden_field.value = post_number.name;
    }
});

const open_delete_links = document.getElementsByClassName("open-delete-form");

Array.prototype.slice.call(open_delete_links).forEach(link => {
    link.addEventListener("click", e => {
        const delete_form_div = document.getElementById(e.target.dataset.number + "-delete-form");
        if (delete_form_div.style.visibility == "visible") {
            delete_form_div.style.visibility = "hidden";
            delete_form_div.style.display = "none";
        }
        else {
            delete_form_div.style.visibility = "visible";
            delete_form_div.style.display = "inline";
        }
    });
});

const open_ban_links = document.getElementsByClassName("open-ban-form");

Array.prototype.slice.call(open_ban_links).forEach(link => {
    link.addEventListener("click", e => {
        const delete_form_div = document.getElementById(e.target.dataset.number + "-ban-form");
        if (delete_form_div.style.visibility == "visible") {
            delete_form_div.style.visibility = "hidden";
            delete_form_div.style.display = "none";
        }
        else {
            delete_form_div.style.visibility = "visible";
            delete_form_div.style.display = "inline";
        }
    });
});

// Code from https://www.quirksmode.org/js/cookies.html
function createCookie(name,value,days) {
	if (days) {
		var date = new Date();
		date.setTime(date.getTime()+(days*24*60*60*1000));
		var expires = "; expires="+date.toGMTString();
	}
	else var expires = "";
	document.cookie = name+"="+value+expires+"; path=/";
}

function readCookie(name) {
	var nameEQ = name + "=";
	var ca = document.cookie.split(';');
	for(var i=0;i < ca.length;i++) {
		var c = ca[i];
		while (c.charAt(0)==' ') c = c.substring(1,c.length);
		if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
	}
	return null;
}

function eraseCookie(name) {
	createCookie(name,"",-1);
}

if (readCookie('password') == null) {
    var password = "";
    var exclamationCharCode = "!".charCodeAt(0);
    var tildeCharCode = "~".charCodeAt(0);
    for (var i = 0; i < 10; i++) {
        password += String.fromCharCode(exclamationCharCode + Math.ceil(Math.random() * (tildeCharCode - spaceCharCode)));
    }

    createCookie('password', password, 1);
}

const password_inputs = document.getElementsByClassName("password-input");

Array.prototype.slice.call(password_inputs).forEach(input => {
    input.value = readCookie('password');
});

const deletion_inputs = document.getElementsByClassName("deletion-input");

Array.prototype.slice.call(deletion_inputs).forEach(input => {
    input.value = readCookie('password');
});

const timestamps = document.getElementsByClassName("timestamp");

Array.prototype.slice.call(timestamps).forEach(timestamp => {
    var date = new Date(timestamp.innerHTML);
    timestamp.innerHTML = date.toLocaleString();
});

};