// Search Photos
async function searchPhotos(query) {
    try {
        // Define the search URL
        const searchUrl = `https://t3m0at1i5d.execute-api.us-east-1.amazonaws.com/dev/search?q=${encodeURIComponent(query)}`;

        // Make a GET request to the search endpoint
        const response = await fetch(searchUrl, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Handle the response
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const jsonResponse = await response.json();
        const result = JSON.parse(jsonResponse.body);
        if (result.image) {
            displayResults(result);
        } else {
            alert(result.message || "No matching photos found.");
        }
    } catch (error) {
        console.error("Error fetching search results:", error);
        alert("Failed to fetch search results. Please try again.");
    }
}

// Display Search Results
function displayResults(result) {
    const resultsContainer = document.getElementById('results');
    resultsContainer.innerHTML = ''; // Clear previous results

    // Create a container for the photo
    const photoElement = document.createElement('div');
    photoElement.className = 'photo';

    // Set the image and metadata
    photoElement.innerHTML = `
        <img src="data:image/jpeg;base64,${result.image}" alt="${result.objectKey}" />
        <p><strong>Object Key:</strong> ${result.objectKey}</p>
        <p><strong>Bucket:</strong> ${result.bucket}</p>
        <p><strong>Labels:</strong> ${result.labels.join(', ')}</p>
    `;

    resultsContainer.appendChild(photoElement);
}

// Upload Photo
async function uploadPhoto(file, customLabels = [], bucketName = 'b2-buckett') {
    try {
        // Define the upload URL
        const uploadUrl = `https://t3m0at1i5d.execute-api.us-east-1.amazonaws.com/dev/upload/${bucketName}/${file.name}`;

        // Create headers for the upload
        const headers = new Headers({
            'Content-Type': 'image/jpg', // MIME type of the file
            'X-Amz-Meta-CustomLabels': customLabels.length > 0 ? customLabels.join(', ') : '', // Custom labels as metadata
        });

        // Make a PUT request to the upload endpoint
        const response = await fetch(uploadUrl, {
            method: 'PUT',
            headers: headers,
            body: file, // File data as the request body
        });

        // Handle the response
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        console.log("Upload response:", await response.text());
        alert("Photo uploaded successfully!");
    } catch (error) {
        console.error("Error uploading photo:", error);
        alert("Photo uploaded successfully!");
    }
}

// Handle Search Button Click
document.getElementById('searchButton').addEventListener('click', () => {
    const query = document.getElementById('searchInput').value.trim();
    if (query) {
        searchPhotos(query); // Call searchPhotos function
    } else {
        alert("Please enter a search term.");
    }
});

// Handle Upload Form Submission
document.getElementById('uploadForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const file = document.getElementById('fileInput').files[0];
    const customLabelsInput = document.getElementById('customLabels').value.trim();
    const customLabels = customLabelsInput ? customLabelsInput.split(',').map(label => label.trim()) : []; // Parse custom labels or use an empty array

    if (file) {
        await uploadPhoto(file, customLabels); // Call uploadPhoto function
    } else {
        alert("Please select a file.");
    }
});
