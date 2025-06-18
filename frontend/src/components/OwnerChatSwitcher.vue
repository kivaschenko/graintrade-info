<!-- filepath: /home/kostiantyn/projects/graintrade-info/frontend/src/components/OwnerChatSwitcher.vue -->
<template>
  <div>
    <div class="user-list">
      <div
        v-for="user in participants"
        :key="user.id"
        :class="{'active': user.id === selectedUserId}"
        @click="selectUser(user.id)"
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
    };
  },
  methods: {
    selectUser(userId) {
      this.selectedUserId = userId;
    }
  },
  mounted() {
    // Fetch participants from backend
    fetch(`http://localhost:8001/chat/${this.itemId}/participants`)
      .then(res => res.json())
      .then(data => { this.participants = data; });
  }
};
</script>