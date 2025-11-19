const chatWindow = document.getElementById("chatWindow");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const csvFile = document.getElementById("csvFile");


function addMessage(text, sender) {
    const msg = document.createElement("div");
    msg.classList.add("message", sender);
    msg.textContent = text;
    chatWindow.appendChild(msg);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function addTyping() {
    const typing = document.createElement("div");
    typing.id = "typing";
    typing.classList.add("message", "bot");
    typing.textContent = "O modelo está digitando...";
    chatWindow.appendChild(typing);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function removeTyping() {
    const typing = document.getElementById("typing");
    if (typing) typing.remove();
}


sendBtn.onclick = async () => {
    const message = userInput.value.trim();
    if (!message) return;

    addMessage(message, "user");
    userInput.value = "";

    addTyping();

    const formData = new FormData();
    formData.append("message", message);

    if (csvFile.files.length > 0) {
        formData.append("file", csvFile.files[0]);
    }

    const response = await fetch("/analyze", {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    removeTyping();

    if (data.error) {
        addMessage("Erro: " + data.error, "bot");
    } else {
        addMessage(data.response, "bot");
    }
};
