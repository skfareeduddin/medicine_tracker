if (Notification.permission !== "granted") {
Notification.requestPermission();
}

setInterval(function(){

let now = new Date()

let hour = now.getHours().toString().padStart(2,'0')
let minute = now.getMinutes().toString().padStart(2,'0')

let current = hour + ":" + minute

let reminders = document.querySelectorAll(".reminder")

reminders.forEach(function(r){

if(r.innerText === current){

new Notification("Medicine Reminder",{
body:"Time to take your medicine"
})

}

})

},60000)
