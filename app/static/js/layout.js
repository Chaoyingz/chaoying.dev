const app = {
    components: {
        VueUtterances,
    },
    delimiters: ["[[", "]]"],
    data() {
        return {
            components: {
                header: {
                    post: "",
                },
            },
        };
    },
};

Vue.createApp(app).mount("#app");
