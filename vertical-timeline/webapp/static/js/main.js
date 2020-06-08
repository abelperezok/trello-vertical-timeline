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

new Vue({
    el: '#timelineFacets',
    data: {
        collapsed1: false,
        collapsed2: true,
        collapsed3: true
    },
    methods: {
        toggle1() {
            this.collapsed1 = !this.collapsed1;
        },
        toggle2() {
            this.collapsed2 = !this.collapsed2;
        },
        toggle3() {
            this.collapsed3 = !this.collapsed3;
        }
    }
});

new Vue({
    el: '#populate-trello-data',
    data: {
        collapsed1: false,
        collapsed2: true,
        collapsed3: true
    },
    methods: {
        submit() {
            console.log(this.$refs.chk_board)
        }
    }
});