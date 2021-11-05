// 文章导航
if (document.readyState !== "interactive") {
    const headerSelector = "h2[id], h3[id]";
    const headingsArray = document.querySelectorAll(headerSelector);
    const some = [].some;
    let topHeader = headingsArray[0];
    scrollListener();

    // 监听滚动事件
    function scrollListener(e) {
        const top = document.documentElement.scrollTop;
        some.call(headingsArray, function (heading, i) {
            const position = heading.offsetTop;
            if (position > top + 10) {
                let index = i === 0 ? i : i - 1;
                topHeader = headingsArray[index];
                return true;
            } else if (i === headingsArray.length - 1) {
                topHeader = headingsArray[headingsArray.length - 1];
                return true;
            }
        });
        document.querySelectorAll(".toc li a").forEach((a) => {
            a.parentElement.classList.remove("is-active-li");
        });
        document.querySelectorAll(".toc li").forEach((li) => {
            li.classList.remove("is-collapsible");
        });

        const id = topHeader.getAttribute("id");
        const linkSelector = `.toc li a[href=\"#${id}\"]`;
        document
            .querySelector(linkSelector)
            .parentElement.classList.add("is-active-li");
        if (topHeader.nodeName === "H2") {
            document
                .querySelector(linkSelector)
                .parentElement.classList.add("is-collapsible");
        } else if (topHeader.nodeName === "H3") {
            document
                .querySelector(linkSelector)
                .parentElement.parentElement.parentElement.classList.add(
                    "is-collapsible"
                );
        }
    }

    document.addEventListener("scroll", scrollListener, false);
}
