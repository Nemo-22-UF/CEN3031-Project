
let seconds = 300; // 5 minutes
let timer = null;
const display = document.getElementById("timer-display");

function updateDisplay() {
    let minutes = Math.floor(seconds / 60);
    let remainingSeconds = seconds % 60;
    display.textContent =
        String(minutes).padStart(2, "0") + ":" +
        String(remainingSeconds).padStart(2, "0");
}

function startTimer() {
    if (timer !== null || seconds === 0) return;

    timer = setInterval(function () {
        seconds--;
        updateDisplay();

        if (seconds <= 0) {
            pauseTimer();
            alert("Cooking timer finished!");
        }
    }, 1000);
}

function pauseTimer() {
    clearInterval(timer);
    timer = null;
}

function resetTimer() {
    pauseTimer();
    seconds = 300;
    updateDisplay();
}

document.getElementById("timer-start").addEventListener("click", startTimer);
document.getElementById("timer-pause").addEventListener("click", pauseTimer);
document.getElementById("timer-reset").addEventListener("click", resetTimer);

updateDisplay();
