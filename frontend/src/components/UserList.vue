<template>
    <div>
        <h1>Users</h1>
        <ul>
            <li v-for="user in users" :key="user.id">
                {{ user.username }}
            </li>
        </ul>
    </div>
</template>

<script>
import axios from 'axios';

export default {
    data() {
        return {
            users: [],
        };
    },
    async created() {
        try {
            const response = await axios.get('http://localhost:8000/users', {
                headers: {
                    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
                },
            });
            this.users = response.data;
        } catch (error) {
            console.error(error);
        }
    }
};
</script>