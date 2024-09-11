document.addEventListener('DOMContentLoaded', function () {
    const chatBox = document.getElementById('chat-box');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const messagesContainer = document.getElementById('messages');

    // roomName を取得
    const roomName = window.roomName;
    const ws = new ReconnectingWebSocket('ws://' + window.location.host + '/ws/chat/' + roomName + '/');

    // WebSocketからメッセージを受信したときの処理
    ws.onmessage = function (event) {
        const data = JSON.parse(event.data);
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.textContent = data.message; // ユーザー情報が含まれていない場合は data.message だけにする

        // メッセージを表示
        messagesContainer.appendChild(messageElement);

        // メッセージ追加後に自動スクロール
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    // メッセージ送信
    function sendMessage() {
        const message = messageInput.value.trim();
        if (message.length > 0) {
            ws.send(JSON.stringify({
                'message': message
            }));
            messageInput.value = ''; // 送信後、入力フィールドをクリア
        }
    }

    // 送信ボタンをクリックしたとき
    sendButton.addEventListener('click', sendMessage);

    // Enterキーでメッセージ送信
    messageInput.addEventListener('keypress', function (event) {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });
});
