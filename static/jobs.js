// jobs.js
// Hides the rows of the job table that don't match what is typed in the box.

let searchBox = document.getElementById("search-box");
let table = document.getElementById("job-table");
let matchCount = document.getElementById("match-count");

function filterRows() {
    let typed = searchBox.value.toLowerCase();
    let rows = table.getElementsByTagName("tr");
    let shown = 0;

    // Start at 1 to skip the header row.
    for (let i = 1; i < rows.length; i++) {
        let rowText = rows[i].textContent.toLowerCase();

        if (rowText.includes(typed)) {
            rows[i].style.display = "";
            shown = shown + 1;
        } else {
            rows[i].style.display = "none";
        }
    }

    matchCount.textContent = "Showing " + shown + " of " + (rows.length - 1) + " jobs on this page.";
}

// Run filterRows every time the text in the box changes.
searchBox.addEventListener("input", filterRows);
