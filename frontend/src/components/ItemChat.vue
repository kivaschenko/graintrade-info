<template>
  <div class="chat-box">
    <div class="messages" style="height:200px;overflow:auto;">
      <div v-for="msg in messages" :key="msg.timestamp">
        <b>{{ msg.sender_id }}:</b> {{ msg.content }}
      </div>
    </div>
    <div class="mb-3 d-flex flex-column">
      <textarea
        class="form-control mb-2"
        v-model="newMessage"
        rows="3"
        placeholder="Type your message..."
        @keyup.enter.exact="sendMessage"
        style="resize: vertical;"
      ></textarea>
      <div class="d-flex justify-content-end">
        <button
          class="btn btn-success btn-sm"
          @click="sendMessage"
          :disabled="!newMessage.trim()"
        >
          <i class="bi bi-send"></i> Send
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {itemId: {type: String, required: true}, userId: {type: String, required: true}},
  data() {
    return {
      ws: null,
      messages: [],
      newMessage: '',
    };
  },
  mounted() {
    console.log("ItemChat mounted with itemId:", this.itemId, "userId:", this.userId);
    this.ws = new WebSocket(`ws://localhost:8001/ws/chat/${this.itemId}`);
    this.ws.onmessage = (event) => {
      this.messages.push(JSON.parse(event.data));
    };
    // Optionally fetch history via REST
    fetch(`http://localhost:8001/chat/${this.itemId}/history`)
      .then(res => res.json())
      .then(data => { this.messages = data; });
  },
  methods: {
    sendMessage() {
      if (this.newMessage.trim()) {
        this.ws.send(JSON.stringify({
          sender_id: this.userId,
          item_id: this.itemId,
          content: this.newMessage,
        }));
        this.newMessage = '';
      }
    }
  }
};
</script>

<style scoped>
.chat-box {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1rem;
  background: #fafbfc;
}
.messages {
  background: #fff;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  margin-bottom: 1rem;
  padding: 0.5rem;
}
textarea.form-control {
  font-size: 1rem;
}
</style>