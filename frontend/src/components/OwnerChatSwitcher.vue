<template>
  <div>
    <input
      v-model="filter"
      class="form-control mb-3"
      placeholder="Filter users by name..."
      type="text"
    />
    <ul class="list-group mb-3">
      <li
        v-for="user in filteredParticipants"
        :key="user.id"
        :class="['list-group-item', 'd-flex', 'align-items-center', {active: user.id === selectedUserId}]"
        style="cursor:pointer;"
        @click="selectUser(user.id)"
      >
        <i class="bi bi-person-circle me-2" style="font-size:1.5em;"></i>
        <span>{{ user.username }}</span>
      </li>
    </ul>
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
  props: { 
    itemId: {type: String, required: true}, 
    ownerId: {type: String, required: true},
  },
  data() {
    return {
      participants: [],
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
    fetch(`${process.env.VUE_APP_CHAT_HTTP_URL}/chat/${this.itemId}/participants`)
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then(data => { 
        this.participants = data.filter(u => u.username !== this.ownerId); 
      })
      .catch(error => {
        console.error('Error fetching chat participants:', error);
        // Set participants to empty array if fetch fails
        this.participants = [];
      });
  }
};
</script>

<style scoped>
.list-group-item.active {
  background-color: #0d6efd;
  color: #fff;
  border-color: #0d6efd;
}
.list-group-item {
  transition: background 0.2s;
}
.list-group-item:hover {
  background: #f0f4fa;
}
</style>
