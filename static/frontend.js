const archives = {
    "desuarchive": "https://desuarchive.org",
    "palanq": "https://archive.palanq.win",
    "archived.moe": "https://archived.moe",
    "4plebs": "https://archive.4plebs.org",
    "b4k": "https://arch.b4k.co",
    "warosu": "https://warosu.org/jp/search/text/"
}

function displayResults(data, selectedArchives) {
    const resultsDiv = document.getElementById('results');
    let sitesDiv = resultsDiv.appendChild(document.createElement('div'));
    sitesDiv.innerHTML = ''; // Clear previous results if any
    if (data.error) {
        sitesDiv.textContent = "Error: " + data.error;
        return;
    }

    if (Array.isArray(data.results) && data.results.length > 0) {
        // Variables to track unique sites and count
        let sites = [];
        let sitesCount = [];
        let lastSite = Object.entries(selectedArchives)[0][1];
        let i = 1;

        data.results.forEach(resultObj => {
            // Loop through each key in the result object
            for (const key in resultObj) {
                const post = resultObj[key];
                console.log(key, post, lastSite)

                // Skip null posts
                if (!post) continue;

                // Track unique sites and create headers for each new source
                if (typeof post === 'string' && key === 'source' && typeof post === 'string' && lastSite !== post) {
                    lastSite = post;
                    sites.push(lastSite);
                    sitesCount.push(0);

                    const siteHeader = document.createElement('h2');
                    siteHeader.textContent = lastSite;
                    sitesDiv.prepend(siteHeader);
                    sitesDiv = resultsDiv.appendChild(document.createElement('div'));
                }

                // Count posts for each site
                const siteIndex = sites.indexOf(lastSite);
                if (siteIndex >= 0) sitesCount[siteIndex]++;

                // Create a container for each post
                const postDiv = document.createElement('div');
                postDiv.classList.add('result-container');
                let link = ''
                if(post.board?.short_name && lastSite !== ''){
                    link = `<span><strong><a href="${archives[lastSite]}/${post.board.short_name}/post/${post.num}">View</a></span></strong>`
                }
                // Populate post information
                postDiv.innerHTML = `
                            <div class="result-title">${i}. Post ID: ${post.num || 'N/A'}</div>
                            <span><strong>Board:</strong> ${post.board ? '/' + post.board.short_name + '/ ' + post.board.name : '_'}</span>
                            <div class="result-meta">
                                <span><strong>Thread Number:</strong> ${post.thread_num || 'N/A'}</span> |
                                <span><strong>Timestamp:</strong> ${post.timestamp ? new Date(post.timestamp * 1000).toLocaleString() : 'N/A'}</span>
                                ${link}
                            </div>
                            <div class="result-comment">${post.comment || "No Comment"}</div>
                            <div class="result-media">
                                ${post.media && post.media.media_orig ? `<strong>Media:</strong> <a href="${post.media.media_orig}" download>Download</a>` : ""}
                            </div>
                        `;

                sitesDiv.appendChild(postDiv);
                i++;
            }
        });

        // Sort sites and display count table
        sortSites(sites, sitesCount);

        const countTable = document.createElement('table');
        countTable.innerHTML = `<tr><th>Search Count</th><th>Site</th></tr>`;
        sites.forEach((site, index) => {
            countTable.innerHTML += `<tr><td>${sitesCount[index]}</td><td>${site}</td></tr>`;
        });
        resultsDiv.prepend(countTable);
    } else {
        sitesDiv.textContent = "No results found.";
    }
}

// Helper function to sort sites based on search count
function sortSites(sites, counts) {
    for (let i = 0; i < counts.length - 1; i++) {
        for (let j = i + 1; j < counts.length; j++) {
            if (counts[j] > counts[i]) {
                // Swap counts
                [counts[i], counts[j]] = [counts[j], counts[i]];
                // Swap corresponding site names
                [sites[i], sites[j]] = [sites[j], sites[i]];
            }
        }
    }
}
document.getElementById('searchForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const formData = new FormData(this);
    const selectedArchives = formData.getAll("archives");  // Get all selected archives

    if (selectedArchives.length === 0) {
        alert("Please select at least one archive.");
        return;
    }

    const searchParams = new URLSearchParams();
    searchParams.append('query', formData.get("query"));
    searchParams.append('archives', JSON.stringify(selectedArchives));  // Send archives as JSON array

    const response = await fetch('/search', {
        method: 'POST',
        body: searchParams
    });
    const result = await response.json();
    console.dir(result);
    console.log(selectedArchives)
    displayResults(result, selectedArchives);
});