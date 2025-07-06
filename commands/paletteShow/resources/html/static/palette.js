function getDateString() {
    const today = new Date();
    const date = `${today.getDate()}/${today.getMonth() + 1}/${today.getFullYear()}`;
    const time = `${today.getHours()}:${today.getMinutes()}:${today.getSeconds()}`;
    return `Date: ${date}, Time: ${time}`;
}

// Chat functionality
let messageHistory = [];

function insertQuickCommand(command) {
    const chatInput = document.getElementById("chatInput");
    chatInput.value = command;
    chatInput.focus();
    
    // Add a subtle animation to show the command was inserted
    chatInput.style.transform = "scale(1.02)";
    setTimeout(() => {
        chatInput.style.transform = "scale(1)";
    }, 200);
}

function addMessage(content, type = 'user') {
    const messagesContainer = document.getElementById('messagesContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = type === 'user' ? 'U' : 'AI';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.textContent = content;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Store in history
    messageHistory.push({ content, type, timestamp: new Date() });
}

function addStatusMessage(message, type = 'loading') {
    const messagesContainer = document.getElementById('messagesContainer');
    const statusDiv = document.createElement('div');
    statusDiv.className = `status-message ${type}`;
    statusDiv.id = 'currentStatus';
    
    if (type === 'loading') {
        statusDiv.innerHTML = `${message} <span class="loading-dots"><span></span><span></span><span></span></span>`;
    } else {
        statusDiv.textContent = message;
    }
    
    // Remove existing status message
    const existingStatus = document.getElementById('currentStatus');
    if (existingStatus) {
        existingStatus.remove();
    }
    
    messagesContainer.appendChild(statusDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    return statusDiv;
}

function removeStatusMessage() {
    const statusDiv = document.getElementById('currentStatus');
    if (statusDiv) {
        statusDiv.remove();
    }
}

function sendChatMessage() {
    const chatInput = document.getElementById("chatInput");
    const sendBtn = document.getElementById("sendBtn");
    
    const userCommand = chatInput.value.trim();
    
    if (!userCommand) {
        return;
    }
    
    // Add user message to chat
    addMessage(userCommand, 'user');
    
    // Clear input and disable button
    chatInput.value = '';
    sendBtn.disabled = true;
    
    // Show loading status
    addStatusMessage("CadxStudio AI is analyzing your command...", "loading");
    
    const commandData = {
        command: userCommand,
        timestamp: getDateString(),
        sessionId: generateSessionId()
    };
    
    // Send the AI command to Fusion
    adsk.fusionSendData("aiCommand", JSON.stringify(commandData))
        .then((result) => {
            console.log("AI Command Response:", result);
            handleAIResponse(result);
        })
        .catch((error) => {
            console.error("Error sending AI command:", error);
            removeStatusMessage();
            addMessage("Error communicating with Fusion 360. Please try again.", 'assistant');
        })
        .finally(() => {
            // Re-enable button
            sendBtn.disabled = false;
        });
}

function handleAIResponse(response) {
    removeStatusMessage();
    
    try {
        // Try to parse as JSON first
        const parsedResponse = JSON.parse(response);
        
        if (parsedResponse.status === "success") {
            addStatusMessage("✅ Command executed successfully!", "success");
            const message = `Created: ${parsedResponse.action.replace('_', ' ')} with parameters: ${JSON.stringify(parsedResponse.parameters)}`;
            addMessage(message, 'assistant');
        } else if (parsedResponse.status === "error") {
            addStatusMessage("❌ Command failed to execute", "error");
            addMessage(`Error: ${parsedResponse.message}`, 'assistant');
        } else if (parsedResponse.status === "processing") {
            addStatusMessage("🔄 AI is processing your command...", "loading");
        }
    } catch (e) {
        // If not JSON, treat as plain text
        addMessage(response, 'assistant');
    }
    
    // Auto-remove status messages after 3 seconds
    setTimeout(() => {
        const statusMsg = document.querySelector('.status-message');
        if (statusMsg) {
            statusMsg.style.opacity = '0';
            setTimeout(() => statusMsg.remove(), 300);
        }
    }, 3000);
}

function generateSessionId() {
    return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
}

// Auto-resize textarea
function autoResizeTextarea() {
    const chatInput = document.getElementById('chatInput');
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
}

// Enhanced handler for AI responses
function handleAIUpdate(messageString) {
    try {
        const data = JSON.parse(messageString);
        handleAIResponse(JSON.stringify(data));
    } catch (e) {
        handleAIResponse(messageString);
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chatInput');
    
    if (chatInput) {
        // Auto-resize on input
        chatInput.addEventListener('input', autoResizeTextarea);
        
        // Send on Ctrl+Enter
        chatInput.addEventListener('keydown', function(event) {
            if (event.ctrlKey && event.key === 'Enter') {
                event.preventDefault();
                sendChatMessage();
            }
        });
        
        // Send on Enter (without Shift)
        chatInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && !event.shiftKey && !event.ctrlKey) {
                event.preventDefault();
                sendChatMessage();
            }
        });
    }
    
    // Add keyboard support for quick actions
    document.querySelectorAll('.quick-action').forEach(action => {
        action.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                action.click();
            }
        });
    });
});

// Legacy functions for backward compatibility
function sendInfoToFusion() {
    const args = {
        arg1: "Legacy test",
        arg2: getDateString()
    };

    adsk.fusionSendData("messageFromPalette", JSON.stringify(args)).then((result) =>
        addMessage(`Legacy response: ${result}`, 'assistant')
    );
}

function updateMessage(messageString) {
    const messageData = JSON.parse(messageString);
    const message = `Text: ${messageData.myText}, Expression: ${messageData.myExpression}, Value: ${messageData.myValue}`;
    addMessage(message, 'assistant');
}

// Fusion 360 JavaScript Handler
window.fusionJavaScriptHandler = {
    handle: function (action, data) {
        try {
            if (action === "updateMessage") {
                updateMessage(data);
            } else if (action === "aiResponse") {
                handleAIUpdate(data);
            } else if (action === "debugger") {
                debugger;
            } else {
                console.log(`Unhandled action: ${action}`);
                return `Unexpected command type: ${action}`;
            }
        } catch (e) {
            console.log(e);
            console.log(`Exception caught with command: ${action}, data: ${data}`);
        }
        return "OK";
    },
};