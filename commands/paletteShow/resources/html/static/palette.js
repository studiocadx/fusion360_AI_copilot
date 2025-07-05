function getDateString() {
    const today = new Date();
    const date = `${today.getDate()}/${today.getMonth() + 1}/${today.getFullYear()}`;
    const time = `${today.getHours()}:${today.getMinutes()}:${today.getSeconds()}`;
    return `Date: ${date}, Time: ${time}`;
}

// Legacy function for testing
function sendInfoToFusion() {
    const args = {
        arg1: document.getElementById("sampleData").value,
        arg2: getDateString()
    };

    // Send the data to Fusion as a JSON string. The return value is a Promise.
    adsk.fusionSendData("messageFromPalette", JSON.stringify(args)).then((result) =>
        document.getElementById("returnValue").innerHTML = `${result}`
    );
}

// New AI Command function
function sendAICommand() {
    const commandInput = document.getElementById("aiCommandInput");
    const responseDiv = document.getElementById("aiResponse");
    const submitBtn = document.getElementById("aiSubmitBtn");
    
    const userCommand = commandInput.value.trim();
    
    if (!userCommand) {
        showStatus("Please enter a command first.", "error");
        return;
    }
    
    // Disable button and show loading state
    submitBtn.disabled = true;
    submitBtn.textContent = "🔄 Processing...";
    showStatus("Sending command to AI Copilot...", "loading");
    
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
            showStatus("Error communicating with Fusion 360. Please try again.", "error");
        })
        .finally(() => {
            // Re-enable button
            submitBtn.disabled = false;
            submitBtn.textContent = "🚀 Execute Command";
        });
}

function handleAIResponse(response) {
    const responseDiv = document.getElementById("aiResponse");
    
    try {
        // Try to parse as JSON first
        const parsedResponse = JSON.parse(response);
        
        if (parsedResponse.status === "success") {
            showStatus("✅ Command executed successfully!", "success");
            responseDiv.innerHTML = `Command: "${parsedResponse.originalCommand}"\n` +
                                  `Action: ${parsedResponse.action}\n` +
                                  `Parameters: ${JSON.stringify(parsedResponse.parameters, null, 2)}\n` +
                                  `Result: ${parsedResponse.message}`;
        } else if (parsedResponse.status === "error") {
            showStatus("❌ Command failed to execute", "error");
            responseDiv.innerHTML = `Error: ${parsedResponse.message}\n` +
                                  `Command: "${parsedResponse.originalCommand}"`;
        } else if (parsedResponse.status === "processing") {
            showStatus("🔄 AI is processing your command...", "loading");
            responseDiv.innerHTML = `Processing: "${parsedResponse.originalCommand}"\n` +
                                  `AI Response: ${parsedResponse.aiResponse || "Analyzing command..."}`;
        }
    } catch (e) {
        // If not JSON, treat as plain text
        responseDiv.innerHTML = response;
        showStatus("Response received", "success");
    }
}

function showStatus(message, type) {
    const responseDiv = document.getElementById("aiResponse");
    
    // Create or update status element
    let statusDiv = document.getElementById("statusMessage");
    if (!statusDiv) {
        statusDiv = document.createElement("div");
        statusDiv.id = "statusMessage";
        responseDiv.parentNode.insertBefore(statusDiv, responseDiv);
    }
    
    statusDiv.className = `status ${type}`;
    statusDiv.textContent = message;
    
    // Auto-hide success/error messages after 5 seconds
    if (type !== "loading") {
        setTimeout(() => {
            if (statusDiv && statusDiv.parentNode) {
                statusDiv.remove();
            }
        }, 5000);
    }
}

function generateSessionId() {
    return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
}

// Legacy function for updating messages from Fusion
function updateMessage(messageString) {
    // Message is sent from the add-in as a JSON string.
    const messageData = JSON.parse(messageString);

    // Update a paragraph with the data passed in.
    document.getElementById("fusionMessage").innerHTML =
        `<b>Your text</b>: ${messageData.myText} <br/>` +
        `<b>Your expression</b>: ${messageData.myExpression} <br/>` +
        `<b>Your value</b>: ${messageData.myValue}`;
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

// Allow Enter key to submit command
document.addEventListener('DOMContentLoaded', function() {
    const commandInput = document.getElementById('aiCommandInput');
    if (commandInput) {
        commandInput.addEventListener('keydown', function(event) {
            if (event.ctrlKey && event.key === 'Enter') {
                event.preventDefault();
                sendAICommand();
            }
        });
    }
});

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