const chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/' + groupId + '/'
);

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    const chatMessages = document.querySelector('#chat-messages');
    const messageElement = document.createElement('div');
    messageElement.className = 'message';

    const usernameSpan = document.createElement('span');
    usernameSpan.className = 'username';
    usernameSpan.textContent = data.username;

    const timestampSpan = document.createElement('span');
    timestampSpan.className = 'timestamp';
    timestampSpan.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

    const contentP = document.createElement('p');
    contentP.innerHTML = parseLinks(data.message); // メッセージ内のリンクを変換

    messageElement.appendChild(usernameSpan);
    messageElement.appendChild(timestampSpan);
    messageElement.appendChild(contentP);

    chatMessages.appendChild(messageElement);
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

// メッセージ内のリンクをHTMLリンクに変換
function parseLinks(message) {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    return message.replace(urlRegex, function(url) {
        return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
    });
}
