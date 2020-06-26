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
                name: 'Lists from included boards',
                filters: [],
                selectedFilters: []
            },
            labels: {
                collapsed: true,
                name: 'Labels from included boards',
                filters: [],
                selectedFilters: []
            }
        },
        cards: []
    },
    mounted: function () {
        this.fetchBoards();
    },
    methods: {
        onSelectBoard(selectedFilters) {
            this.fetchLists(selectedFilters);
            this.fetchLabels(selectedFilters);
        },
        onSelectListsLabels(){
            this.fetchCards(this.groups.lists.selectedFilters, this.groups.labels.selectedFilters)
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

            fetch('/trello/lists?boards=' + selectedBoards.join(','))
                .then(response => response.json())
                .then(data => {
                    this.groups.lists.filters = data;
                    this.groups.lists.collapsed = false;
                })
                .catch((error) => {
                    console.error('Error:', error);
                });
        },
        fetchLabels(selectedBoards) {

            fetch('/trello/labels?boards=' + selectedBoards.join(','))
                .then(response => response.json())
                .then(data => {
                    this.groups.labels.filters = data;
                    this.groups.labels.collapsed = false;
                })
                .catch((error) => {
                    console.error('Error:', error);
                });
        },
        fetchCards(selectedLists, selectedLabels) {
            url = `/trello/cards?lists=${selectedLists.join(',')}&labels=${selectedLabels.join(',')}`
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    this.cards = data;
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