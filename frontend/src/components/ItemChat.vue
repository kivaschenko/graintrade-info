<template>
  <div class="chat-box">
    <div class="messages" style="height:250px;overflow:auto;">
      <div
        v-for="msg in messages"
        :key="msg.timestamp"
        :class="{'my-message': msg.sender_id === userId, 'other-message': msg.sender_id !== userId}"
        class="message-row"
      >
        <div class="message-content">
          <b v-if="msg.sender_id !== userId">{{ msg.sender_id }}:</b>
          {{ msg.content }}
          <div class="timestamp">{{ formatTimestamp(msg.timestamp) }}</div>
        </div>
      </div>
    </div>
    <div class="mb-3 d-flex flex-column">
      <textarea
        class="form-control mb-2"
        v-model="newMessage"
        rows="4"
        maxlength="500"
        :placeholder="$t('chat.messagePlaceholder')"
        @keyup.enter.exact="sendMessage"
        style="resize: vertical;"
      ></textarea>
      <div class="d-flex justify-content-end">
        <button
          class="btn btn-success btn-sm"
          @click="sendMessage"
          :disabled="!newMessage.trim()"
        >
          <i class="bi bi-send"></i> {{ $t('chat.send') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    itemId: {type: String, required: true}, 
    userId: {type: String, required: true},
    otherUserId: {type: String, required: true},
    chatRoomUrl: {type: String, default: process.env.VUE_APP_CHAT_ROOM_URL || 'localhost:8001'},
  },
  data() {
    return {
      ws: null,
      messages: [],
      newMessage: '',
      refreshTimer: null,
    };
  },
  mounted() {
    this.initChat();
    this.startPeriodicRefresh();
  },
  watch: {
    itemId: 'handleSwitch',
    otherUserId: 'handleSwitch'
  },
  beforeUnmount() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
  },
  methods: {
    handleSwitch() {
      this.initChat();
      this.startPeriodicRefresh();
    },
    initChat() {
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }
      this.messages = [];
      if (this.userId !== this.otherUserId) {
          this.ws = new WebSocket(`ws://${this.chatRoomUrl}/ws/chat/${this.itemId}/${this.otherUserId}`);
        this.ws.onmessage = (event) => {
          this.messages.push(JSON.parse(event.data));
        };
        this.fetchHistory();
      }
    },
    fetchHistory() {
      fetch(`http://${this.chatRoomUrl}/chat/${this.itemId}/${this.otherUserId}/history?current_user=${this.userId}`)
        .then(res => res.json())
        .then(data => { this.messages = data; });
    },
    startPeriodicRefresh() {
      if (this.refreshTimer) {
        clearInterval(this.refreshTimer);
      }
      this.refreshTimer = setInterval(() => {
        this.fetchHistory();
      }, 60000); // 60,000 ms = 1 minute
    },
    sendMessage() {
      if (this.newMessage.trim() && this.userId !== this.otherUserId) {
        this.ws.send(JSON.stringify({
          sender_id: this.userId,
          receiver_id: this.otherUserId,
          item_id: this.itemId,
          content: this.newMessage,
        }));
        this.newMessage = '';
      }
    },
    formatTimestamp(ts) {
      if (!ts) return '';
      return new Date(ts).toLocaleString();
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
  max-height: 250px;
  overflow-y: auto;
}
.message-row {
  display: flex;
  margin-bottom: 0.5rem;
}
.my-message {
  justify-content: flex-end;
}
.other-message {
  justify-content: flex-start;
}
.message-content {
  max-width: 70%;
  padding: 0.5rem 1rem;
  border-radius: 16px;
  background: #e6f7e6;
  color: #222;
}
.my-message .message-content {
  background: #d1e7fd;
  color: #222;
}


</style>

<style scoped>
.timestamp {
  font-size: 0.8em;
  color: #888;
  margin-top: 0.2em;
  text-align: right;
}
</style>

