const chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/' + groupId + '/'
);

chatSocket.onmessage = function(e) {
    // 受信データを解析
    const data = JSON.parse(e.data);

    // チャットメッセージの表示領域を取得
    const chatMessages = document.querySelector('#chat-messages');

    // メッセージ要素を作成
    const messageElement = document.createElement('div');
    messageElement.className = 'message mb-2';

    // ユーザー名を作成
    const usernameSpan = document.createElement('strong');
    usernameSpan.className = 'username text-primary';
    usernameSpan.textContent = data.username;

    // スペースを挿入
    const spaceText = document.createTextNode(' ');

    // タイムスタンプを作成
    const timestampSpan = document.createElement('small');
    timestampSpan.className = 'timestamp text-muted';
    timestampSpan.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

    // メッセージ本文を作成
    const contentP = document.createElement('p');
    contentP.innerHTML = parseMarkdown(data.message); // Markdown変換を使用
    contentP.className = 'mb-0'

    // 作成した要素を親要素に追加
    messageElement.appendChild(usernameSpan);
    messageElement.appendChild(spaceText); // ユーザー名とタイムスタンプの間にスペースを挿入
    messageElement.appendChild(timestampSpan);
    messageElement.appendChild(contentP);

    // メッセージをチャット表示領域に追加
    chatMessages.appendChild(messageElement);

    // スクロール位置を最新に調整
    chatMessages.scrollTop = chatMessages.scrollHeight;
};

chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
};

document.querySelector('#chat-form').onsubmit = function(e) {
    e.preventDefault();
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;
    chatSocket.send(JSON.stringify({
        'message': message,
        'username': username
    }));
    messageInputDom.value = '';
};


// Markdownレンダリング用の関数
function parseMarkdown(text) {
    // marked.jsライブラリを使用してMarkdownをレンダリング
    return marked.parse(text, {
        breaks: true,
        gfm: true,
        sanitize: true
    });
}
