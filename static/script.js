// Comprehensive list of business categories
const CATEGORIES_DB = [
    "Restaurants", "Coffee Shops", "Real Estate", "Tuition Centers", "Event Planners",
    "Plumbers", "Electricians", "Dentists", "Gyms", "Lawyers", "Accountants", 
    "Bakeries", "Salons", "Spas", "Pet Stores", "Vets", "Car Repairs", "Car Washes",
    "Hotels", "Travel Agencies", "Marketing Agencies", "Web Designers", "IT Services",
    "Cleaning Services", "Pest Control", "Locksmiths", "Photographers", "Caterers",
    "Florists", "Bookstores", "Pharmacies", "Clinics", "Hospitals", "Yoga Studios",
    "Fitness Centers", "Martial Arts", "Dance Studios", "Music Schools", "Driving Schools",
    "Supermarkets", "Grocery Stores", "Hardware Stores", "Furniture Stores", "Clothing Stores",
    "Jewelry Stores", "Shoe Stores", "Electronics Stores", "Toy Stores", "Sporting Goods",
    "Bars", "Clubs", "Movie Theaters", "Museums", "Art Galleries", "Amusement Parks",
    "Architects", "Contractors", "Roofers", "Landscapers", "HVAC Services", "Painters",
    "Movers", "Storage Facilities", "Security Services", "Private Investigators",
    "Insurance Agencies", "Banks", "Credit Unions", "Financial Advisors", "Tax Preparation",
    "Optometrists", "Chiropractors", "Physiotherapists", "Massage Therapists",
    "Acupuncture", "Nutritionists", "Psychologists", "Counselors", "Daycares",
    "Preschools", "Tailors", "Dry Cleaners", "Laundromats", "Towing Services"
];

const selectedCategories = new Set();
const searchInput = document.getElementById('categorySearch');
const suggestionsBox = document.getElementById('suggestionsBox');
const tagsInputContainer = document.getElementById('tagsInput');

// Multi-select functionality
function renderTags() {
    // Remove existing tags
    document.querySelectorAll('.tag').forEach(t => t.remove());
    
    // Create tags
    selectedCategories.forEach(cat => {
        const tag = document.createElement('div');
        tag.className = 'tag';
        tag.innerHTML = `${cat} <span class="tag-remove" data-val="${cat}">×</span>`;
        tagsInputContainer.insertBefore(tag, searchInput);
    });
    
    // Re-bind remove events
    document.querySelectorAll('.tag-remove').forEach(btn => {
        btn.onclick = (e) => {
            selectedCategories.delete(e.target.dataset.val);
            renderTags();
        }
    });
}

function showSuggestions(query) {
    suggestionsBox.innerHTML = '';
    const filtered = CATEGORIES_DB.filter(c => 
        c.toLowerCase().includes(query.toLowerCase()) && !selectedCategories.has(c)
    );
    
    if (filtered.length === 0) {
        suggestionsBox.classList.add('hidden');
        return;
    }
    
    filtered.slice(0, 10).forEach(cat => {
        const div = document.createElement('div');
        div.className = 'suggestion-item';
        div.textContent = cat;
        div.onclick = () => {
            selectedCategories.add(cat);
            searchInput.value = '';
            suggestionsBox.classList.add('hidden');
            renderTags();
            searchInput.focus();
        };
        suggestionsBox.appendChild(div);
    });
    suggestionsBox.classList.remove('hidden');
}

searchInput.addEventListener('input', (e) => {
    const val = e.target.value.trim();
    if (val) {
        showSuggestions(val);
    } else {
        suggestionsBox.classList.add('hidden');
    }
});

searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && searchInput.value.trim()) {
        e.preventDefault();
        // If pressing enter, add the text as custom category
        selectedCategories.add(searchInput.value.trim());
        searchInput.value = '';
        suggestionsBox.classList.add('hidden');
        renderTags();
    }
});

searchInput.addEventListener('focus', () => {
    tagsInputContainer.classList.add('focused');
});

searchInput.addEventListener('blur', () => {
    tagsInputContainer.classList.remove('focused');
    setTimeout(() => suggestionsBox.classList.add('hidden'), 200); // delay to allow clicks
});

// Form submission to trigger Server-Sent Events (SSE)
document.getElementById('scrapeForm').addEventListener('submit', (e) => {
    e.preventDefault();
    
    // Custom tags inside the list or parsed
    if (selectedCategories.size === 0) {
         // Fallback if they just typed inside search box without enter
         if(searchInput.value.trim()) {
             selectedCategories.add(searchInput.value.trim());
             renderTags();
             searchInput.value = '';
         } else {
            alert("Please select at least one category.");
            return;
         }
    }
    
    const locationInput = document.getElementById('location').value;
    const maxResults = parseInt(document.getElementById('max_results').value);
    
    if (!locationInput) {
        alert("Please enter a location.");
        return;
    }

    // UI Updates to Loading State
    const submitBtn = document.getElementById('submitBtn');
    const statusArea = document.getElementById('statusArea');
    const statusMessage = document.getElementById('statusMessage');
    const resultAction = document.getElementById('resultAction');
    const tableBody = document.getElementById('tableBody');
    const emptyState = document.getElementById('emptyState');
    const pulseIndicator = document.getElementById('pulseIndicator');
    
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;
    
    statusArea.classList.remove('hidden');
    resultAction.classList.add('hidden');
    statusMessage.textContent = 'Connecting to extraction stream...';
    statusMessage.style.color = '#a0a5b8';
    
    tableBody.innerHTML = '';
    emptyState.classList.add('hidden');
    pulseIndicator.classList.remove('hidden');

    const catParam = Array.from(selectedCategories).join(',');
    const url = `/api/stream?categories=${encodeURIComponent(catParam)}&location=${encodeURIComponent(locationInput)}&max_results=${maxResults}`;

    const eventSource = new EventSource(url);
    
    eventSource.addEventListener('data', (e) => {
        statusMessage.textContent = 'Receiving live data stream...';
        const data = JSON.parse(e.data);
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td title="${data.Name}">${data.Name}</td>
            <td title="${data.Category}">${data.Category}</td>
            <td>${data.Rating || '-'}</td>
            <td>${data.Reviews || '-'}</td>
            <td>${data.Phone || '-'}</td>
            <td title="${data.Address}">${data.Address || '-'}</td>
             <td title="${data.Website}">${data.Website ? `<a href="${data.Website}" target="_blank" style="color:#6c5ce7; text-decoration:none;">Link</a>` : '-'}</td>
            <td><span style="color: ${data['Has Website'] === 'Yes' ? '#4ade80' : '#ff758c'}">${data['Has Website']}</span></td>
        `;
        tableBody.appendChild(row);
        
        // Auto scroll to bottom
        const responsiveTable = document.querySelector('.table-responsive');
        responsiveTable.scrollTop = responsiveTable.scrollHeight;
    });

    eventSource.addEventListener('done', (e) => {
        eventSource.close();
        const data = JSON.parse(e.data);
        pulseIndicator.classList.add('hidden');
        statusMessage.classList.add('hidden');
        resultAction.classList.remove('hidden');
        
        document.getElementById('leadCount').textContent = data.count;
        
        const downloadBtn = document.getElementById('downloadBtn');
        downloadBtn.href = data.download_url;
        
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
        
        // Auto trigger download
        setTimeout(() => downloadBtn.click(), 1000);
    });

    eventSource.addEventListener('error', (e) => {
        eventSource.close();
        pulseIndicator.classList.add('hidden');
        let errorMsg = 'An error occurred during streaming.';
        if (e.data) {
            try {
                errorMsg = JSON.parse(e.data).error || errorMsg;
            } catch(err){}
        }
        statusMessage.textContent = `Streaming Error: ${errorMsg}`;
        statusMessage.style.color = '#ef4444';
        
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
    });
});
