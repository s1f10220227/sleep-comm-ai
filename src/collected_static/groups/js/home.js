document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('videoModal');
    const closeButton = document.querySelector('.close-button');

    // アクセス後2秒後にモーダルを表示
    setTimeout(function() {
        modal.classList.add('fade-in');
        modal.style.display = 'flex';
    }, 2000);

    // 閉じるボタンでモーダルを閉じる
    closeButton.onclick = function() {
        modal.style.display = 'none';
        modal.classList.remove('fade-in');
    };

    // モーダルの外側をクリックしてもモーダルを閉じる
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
            modal.classList.remove('fade-in');
        }
    };
});

document.addEventListener('DOMContentLoaded', function() {
    // グループを離脱ボタンがクリックされたとき
    const leaveButtons = document.querySelectorAll('button.btn.btn-danger');

    leaveButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            // ユーザーに確認メッセージを表示
            const userConfirmed = confirm("ミッション案が生成された後のグループには再参加できません。本当にグループを離脱しますか？");

            // ユーザーが「キャンセル」を選択した場合、フォームの送信をキャンセル
            if (!userConfirmed) {
                event.preventDefault();
            }
            // ユーザーが「OK」を選択した場合、フォームを送信
        });
    });
});
