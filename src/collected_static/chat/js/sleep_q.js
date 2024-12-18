// ページが表示されたときの処理
window.onpageshow = function(event) {
    if (event.persisted) {
        // ページがブラウザのキャッシュから読み込まれた（戻るボタン）
        hideLoading();
    }
    // 通常のページロードでもローディングを隠す
    hideLoading();
};

// 睡眠時間を計算する関数
function calculateSleepDuration() {
    const sleepTime = document.getElementById('sleep_time').value;
    const wakeTime = document.getElementById('wake_time').value;

    if (sleepTime && wakeTime) {
        // 今日の日付を取得
        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth();
        const day = today.getDate();

        // 就寝時刻と起床時刻を日付付きのDateオブジェクトに変換
        const sleepDateTime = new Date(year, month, day,
            parseInt(sleepTime.split(':')[0]),
            parseInt(sleepTime.split(':')[1]));

        const wakeDateTime = new Date(year, month, day,
            parseInt(wakeTime.split(':')[0]),
            parseInt(wakeTime.split(':')[1]));

        // 起床時刻が就寝時刻より前の場合、次の日の日付にする
        if (wakeDateTime < sleepDateTime) {
            wakeDateTime.setDate(wakeDateTime.getDate() + 1);
        }

        // 睡眠時間を計算（ミリ秒）
        const diff = wakeDateTime - sleepDateTime;

        // 時間と分に変換
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

        document.getElementById('sleep_duration').innerHTML =
            `睡眠時間: ${hours}時間${minutes}分`;
    } else {
        document.getElementById('sleep_duration').innerHTML =
            '睡眠時間: --時間--分';
    }
}

// ローディングアニメーションを表示する関数
function showLoading() {
    document.getElementById('loading').style.display = 'block';
    return true;
}

// ローディングアニメーションを隠す関数
function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}
