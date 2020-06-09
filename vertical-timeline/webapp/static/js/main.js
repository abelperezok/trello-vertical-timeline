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

// new Vue({
//     el: '#timelineFacets',
//     data: {
//         collapsed1: false,
//         collapsed2: true,
//         collapsed3: true
//     },
//     methods: {
//         toggle1() {
//             this.collapsed1 = !this.collapsed1;
//         },
//         toggle2() {
//             this.collapsed2 = !this.collapsed2;
//         },
//         toggle3() {
//             this.collapsed3 = !this.collapsed3;
//         }
//     }
// });

new Vue({
    el: '#timelineFacets-2',
    data: {
        groups: {
            boards: {
                collapsed: false,
                name: 'Boards to include',
                filters: [],
                selectedFilters: []
            },
            lists: {
                collapsed: true,
                name: 'Lists from the boards',
                filters: [],
                selectedFilters: []
            }
        }
    },
    mounted: function () {
        this.fetchBoards();
    },
    methods: {
        dispatchEvent(type, filterId, selectedFilters){
            switch (type) {
                case 'boards':
                    this.fetchLists(selectedFilters)
                    break;
                case 'lists':
                    console.log(filterId, selectedFilters)
                    break;            
                default:
                    break;
            }
        },
        fetchBoards() {
            
            fetch('/trello/boards')
            .then(response => response.json())
            .then(data => {
                this.groups.boards.filters = data;
            })
            .catch((error) => {
                console.error('Error:', error);
            });
        },
        fetchLists(selectedBoards) {

            fetch('/trello/lists?boards='+selectedBoards.join(','))
            .then(response => response.json())
            .then(data => {
                this.groups.lists.filters = data;
                this.groups.lists.collapsed = false;
            })
            .catch((error) => {
                console.error('Error:', error);
            });
        },
        toggle(group) {
             group.collapsed = !group.collapsed;
        }
    }
});