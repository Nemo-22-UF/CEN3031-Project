let seconds = 300;
let timer = null;
const input = document.getElementById("timer-minutes");
const display = document.getElementById("timer-display");

function updateDisplay() {
    let minutes = Math.floor(seconds / 60);
    let remainingSeconds = seconds % 60;
    display.textContent= String(minutes).padStart(2, "0") + ":" + String(remainingSeconds).padStart(2, "0");
}

function startTimer() {
    if (timer !== null || seconds=== 0){
         return;
    }
    timer = setInterval(function () {
        seconds--;
        updateDisplay();
        if (seconds <= 0) {
            pauseTimer();
            alert("Timer Complete!");
        }
    }, 1000);
}

function pauseTimer() {
    clearInterval(timer);
    timer = null;
}

function resetTimer() {
    pauseTimer();
    let minutes = Math.max(1, Math.floor(Number(input.value)) || 5);
    input.value = minutes;
    seconds = minutes * 60;
    updateDisplay();
}
input.addEventListener("change",resetTimer);
document.getElementById("timer-start").addEventListener("click", startTimer);
document.getElementById("timer-pause").addEventListener("click", pauseTimer);
document.getElementById("timer-reset").addEventListener("click", resetTimer);

updateDisplay();
