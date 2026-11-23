document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const messages = document.getElementById("chat-messages");

  const ICONS = {
    bot: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="9" width="18" height="11" rx="2"></rect><circle cx="8.5" cy="14.5" r="1.5"></circle><circle cx="15.5" cy="14.5" r="1.5"></circle><path d="M12 9V5"></path><circle cx="12" cy="3.5" r="1.5"></circle></svg>',
    user: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>',
  };

  function addMessage(text, sender) {
    const isUser = sender === "user";
    const div = document.createElement("div");
    div.className = "msg " + (isUser ? "msg-user" : "msg-bot");

    const avatar = document.createElement("span");
    avatar.className = "msg-avatar";
    avatar.innerHTML = isUser ? ICONS.user : ICONS.bot;

    const bubble = document.createElement("span");
    bubble.className = "msg-bubble";
    bubble.textContent = text;

    div.appendChild(avatar);
    div.appendChild(bubble);
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    addMessage(text, "user");
    input.value = "";

    try {
      const res = await fetch("/api/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      addMessage(data.response, "bot");
    } catch (err) {
      addMessage("Sorry, I couldn't reach the server. Please try again.", "bot");
    }
  });
});
