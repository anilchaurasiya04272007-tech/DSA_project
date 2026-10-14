function confirmRegister(name){
    return confirm("Register for " + name + "?");
}
function confirmDrop(name){
    return confirm("Are you sure you want to drop " + name + "?");
}
document.addEventListener("DOMContentLoaded", () => {
    const search = document.getElementById("courseSearch");
    const filter = document.getElementById("semesterFilter");
    const cards = [...document.querySelectorAll(".course-card")];
    const noResults = document.getElementById("noResults");

    function filterCourses(){
        if(!search || !filter) return;
        const term = search.value.toLowerCase().trim();
        const sem = filter.value;
        let visible = 0;
        cards.forEach(card => {
            const matchesText = card.dataset.search.toLowerCase().includes(term);
            const matchesSem = !sem || card.dataset.semester === sem;
            card.classList.toggle("hidden", !(matchesText && matchesSem));
            if(matchesText && matchesSem) visible++;
        });
        if(noResults) noResults.classList.toggle("hidden", visible !== 0);
    }
    if(search) search.addEventListener("input", filterCourses);
    if(filter) filter.addEventListener("change", filterCourses);

    document.querySelectorAll(".flash").forEach(el => {
        setTimeout(() => el.remove(), 4500);
    });
});
