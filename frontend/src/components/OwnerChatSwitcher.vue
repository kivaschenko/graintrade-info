<!-- filepath: /home/kostiantyn/projects/graintrade-info/frontend/src/components/OwnerChatSwitcher.vue -->
<template>
  <div>
    <div class="user-list">
      <div
        v-for="user in filteredParticipants"
        :key="user.id"
        :class="{'active': user.id === selectedUserId}"
        @click="selectUser(user.id)"
        style="cursor:pointer; padding: 0.5em; border-bottom: 1px solid #eee;"
      >
        {{ user.username }}
      </div>
    </div>
    <ItemChat
      v-if="selectedUserId"
      :itemId="itemId"
      :userId="ownerId"
      :otherUserId="selectedUserId"
    />
  </div>
</template>

<script>
import ItemChat from './ItemChat.vue';
export default {
  components: { ItemChat },
  props: { itemId: String, ownerId: String },
  data() {
    return {
      participants: [], // fetched from backend
      selectedUserId: null,
      filter: '',
    };
  },
  computed: {
    filteredParticipants() {
      if (!this.filter) return this.participants;
      return this.participants.filter(user => 
        user.username && user.username.toLowerCase().includes(this.filter.toLowerCase())
    );
    }
  },
  methods: {
    selectUser(userId) {
      this.selectedUserId = userId;
    }
  },
  mounted() {
    if (!this.itemId) {
      console.error('itemId is undefined!');
      return;
    }
    // Fetch participants from backend
    fetch(`http://localhost:8001/chat/${this.itemId}/participants`)
      .then(res => res.json())
      .then(data => { this.participants = data.filter(u => u.username !== this.ownerId); });
    console.log("Fetch participants:", this.participants);
  }
};
</script>