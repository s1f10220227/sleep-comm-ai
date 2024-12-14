function calculateSleepDuration() {
    const sleepTime = document.getElementById('sleep_time').value;
    const wakeTime = document.getElementById('wake_time').value;

    if (sleepTime && wakeTime) {
        const sleep = new Date('2000-01-01 ' + sleepTime);
        const wake = new Date('2000-01-01 ' + wakeTime);

        if (wake < sleep) {
            wake.setDate(wake.getDate() + 1);
        }

        const diff = wake - sleep;
        const hours = Math.floor(diff / 1000 / 60 / 60);
        const minutes = Math.floor((diff / 1000 / 60) % 60);

        document.getElementById('sleep_duration').innerHTML =
            `睡眠時間: ${hours}時間${minutes}分`;
    }
}
