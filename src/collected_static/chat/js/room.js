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
    contentP.textContent = data.message;

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
