var app = new Vue({
    el: "#app",
    delimiters: ["[[", "]]"],
    data: {
        is_uploaded: "",
    },
    mounted() {
        let utterances = document.createElement("script");
        utterances.async = true;
        utterances.setAttribute("src", "https://utteranc.es/client.js");
        utterances.setAttribute("repo", "Chaoyingz/chaoying.dev");
        utterances.setAttribute("issue-term", "title");
        utterances.setAttribute("theme", "github-light");
        utterances.setAttribute("crossorigin", "anonymous");
        this.$refs["utterances"].appendChild(utterances);
    },
});
