// Depends on https://cdn.jsdelivr.net/npm/vue@2.6.11

new Vue({
    el: '#nav-bar',
    data: {
        collapsed: true
    },
    methods: {
        toggle() {
            this.collapsed = !this.collapsed;
        }
    }
});